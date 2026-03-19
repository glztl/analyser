import logging
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.task import AnalysisTask, TaskStatus
from app.services.llm_service import llm_service
from app.services.sandbox_service import SandboxService
from app.services.file_analyzer import FileAnalyzer
from app.core.prompts import SYSTEM_PROMPT, get_error_fix_prompt
from app.core.config import settings

logger = logging.getLogger(__name__)


class AgentService:
    """
    Agent 核心服务
    负责编排 LLM 和沙箱的交互流程

    企业级特性：
    - 文件结构预分析，注入准确信息到 Prompt
    - 智能数据规模检测，自动选择分析策略
    - 代码执行自我修正（最多 3 次重试）
    - 完整的错误处理和日志记录
    - Token 消耗监控
    """

    # 最大重试次数
    MAX_RETRIES = 3

    # 代码执行超时（秒）
    EXECUTION_TIMEOUT = 30

    @classmethod
    async def run_analysis(
        cls, task_id: int, db: AsyncSession, file_analysis: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        执行数据分析任务

        Args:
            task_id: 任务 ID
            db: 数据库会话
            file_analysis: 文件结构分析结果（可选，如果已预先分析）

        Returns:
            dict: 包含执行结果、输出、错误信息
        """
        # ========== 1. 获取任务信息 ==========
        try:
            result = await db.execute(
                select(AnalysisTask).where(AnalysisTask.id == task_id)
            )
            task = result.scalar_one_or_none()

            if not task:
                logger.error(f"Task {task_id} not found")
                return {"success": False, "error": "Task not found", "output": None}

            logger.info(f"Starting analysis for Task {task_id}")

        except Exception as e:
            logger.exception(f"Failed to get task {task_id}: {e}")
            return {
                "success": False,
                "error": f"获取任务失败：{str(e)}",
                "output": None,
            }

        # ========== 2. 更新任务状态为处理中 ==========
        try:
            task.status = TaskStatus.IN_PROGRESS
            task.error_message = None
            await db.commit()
            await db.refresh(task)
        except Exception as e:
            logger.exception(f"Failed to update task status: {e}")
            await db.rollback()
            return {
                "success": False,
                "error": f"更新任务状态失败：{str(e)}",
                "output": None,
            }

        # ========== 3. 分析文件结构（如果未预先分析） ==========
        if not file_analysis:
            logger.info(f"Analyzing file structure: {task.file_path}")
            try:
                file_analysis = FileAnalyzer.analyze_file(task.file_path)

                if not file_analysis.get("success"):
                    error_msg = file_analysis.get("error", "文件分析失败")
                    logger.error(f"File analysis failed: {error_msg}")

                    # 更新任务为失败
                    task.status = TaskStatus.FAILED
                    task.error_message = error_msg
                    await db.commit()

                    return {"success": False, "error": error_msg, "output": None}

                logger.info(
                    f"File analysis complete: "
                    f"{file_analysis['structure']['num_rows']} rows × "
                    f"{file_analysis['structure']['num_columns']} cols"
                )

            except Exception as e:
                logger.exception(f"File analysis error: {e}")
                file_analysis = None

        # ========== 4. 准备 Prompt 消息 ==========
        messages = await cls._prepare_messages(task, file_analysis)

        # ========== 5. 代码生成与执行循环 ==========
        code = ""
        execution_result = {}
        last_error = ""

        for attempt in range(cls.MAX_RETRIES + 1):
            try:
                logger.info(f"Attempt {attempt + 1}/{cls.MAX_RETRIES + 1}")

                # A. 生成/修复代码
                if attempt == 0:
                    logger.info(f"Task {task_id}: Generating initial code...")
                    code = await cls._generate_code(messages)
                else:
                    logger.info(
                        f"Task {task_id}: Attempting fix ({attempt}/{cls.MAX_RETRIES}), "
                        f"last error: {last_error[:200]}"
                    )
                    messages = await cls._add_error_to_messages(
                        messages, code, last_error
                    )
                    code = await cls._generate_code(messages)

                # B. 保存代码快照
                try:
                    task.code_snapshot = code
                    await db.commit()
                except Exception as e:
                    logger.warning(f"Failed to save code snapshot: {e}")
                    await db.rollback()

                # C. 执行代码
                logger.info(f"Task {task_id}: Executing code...")
                execution_result = SandboxService.execute_code(
                    code=code, file_path=task.file_path
                )

                # D. 检查结果
                if execution_result.get("success"):
                    logger.info(f"Task {task_id}: Execution successful!")

                    # 更新任务为完成
                    task.status = TaskStatus.COMPLETED
                    task.error_message = None

                    # 保存结果（如果沙箱返回了图表路径）
                    if execution_result.get("output", {}).get("chart_path"):
                        task.result_path = execution_result["output"]["chart_path"]

                    await db.commit()

                    return {
                        "success": True,
                        "output": execution_result.get("output", {}),
                        "code": code,
                        "attempts": attempt + 1,
                        "metadata": file_analysis.get("strategy")
                        if file_analysis
                        else None,
                    }
                else:
                    # 执行失败，记录错误，进入下一次循环
                    errors = execution_result.get("errors", ["Unknown error"])
                    last_error = errors[0] if errors else "Unknown error"

                    logger.warning(
                        f"Task {task_id}: Execution failed: {last_error[:300]}"
                    )
                    continue

            except Exception as e:
                logger.exception(f"Task {task_id}: Agent error: {e}")
                last_error = str(e)
                execution_result = {"errors": [str(e)]}
                continue

        # ========== 6. 所有重试都失败 ==========
        logger.error(
            f"Task {task_id}: All {cls.MAX_RETRIES + 1} attempts failed. "
            f"Last error: {last_error[:300]}"
        )

        try:
            task.status = TaskStatus.FAILED
            task.error_message = last_error[:2000]  # 限制长度
            await db.commit()
        except Exception as e:
            logger.exception(f"Failed to update task as failed: {e}")
            await db.rollback()

        return {
            "success": False,
            "error": last_error,
            "output": None,
            "code": code,
            "attempts": cls.MAX_RETRIES + 1,
        }

    @classmethod
    async def _prepare_messages(
        cls, task: AnalysisTask, file_analysis: Optional[Dict] = None
    ) -> list[dict]:
        """
        准备 LLM 消息，注入文件结构信息

        Args:
            task: 任务对象
            file_analysis: 文件结构分析结果

        Returns:
            list: 消息列表
        """
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        # ✅ 关键：注入文件结构信息到 Prompt
        if file_analysis and file_analysis.get("success"):
            llm_context = file_analysis.get("llm_context", "")

            messages.append(
                {
                    "role": "system",
                    "content": f"""
# 📋 文件结构信息（已预先分析）

{llm_context}

请根据上述文件结构信息生成准确的分析代码：
1. 使用准确的列名（必须完全匹配，包括大小写和空格）
2. 根据数据规模选择合适的分析策略
3. 不要尝试渲染超过 {file_analysis.get("strategy", {}).get("max_series", 10)} 个数据系列
4. 如果表格是宽表，第一列是指标名，需要特殊处理
""",
                }
            )

            logger.info(
                f"Injected file structure: "
                f"{file_analysis['structure']['num_rows']} rows × "
                f"{file_analysis['structure']['num_columns']} cols, "
                f"strategy: {file_analysis.get('strategy', {}).get('type', 'unknown')}"
            )

        # 添加用户问题
        messages.append(
            {
                "role": "user",
                "content": f"文件路径：{task.file_path}\n用户问题：{task.query}",
            }
        )

        return messages

    @classmethod
    async def _generate_code(cls, messages: list[dict]) -> str:
        """
        调用 LLM 生成代码

        Args:
            messages: 消息列表

        Returns:
            str: 生成的 Python 代码
        """
        try:
            code = await llm_service.generate_code(messages)  # type: ignore

            # 记录 Token 消耗（已在 llm_service 中记录）
            logger.debug(f"Generated code length: {len(code)} chars")

            return code

        except Exception as e:
            logger.exception(f"LLM code generation failed: {e}")
            raise Exception(f"代码生成失败：{str(e)}")

    @classmethod
    async def _add_error_to_messages(
        cls, messages: list[dict], code: str, error: str
    ) -> list[dict]:
        """
        将错误信息添加到消息历史，用于自我修正

        Args:
            messages: 原消息列表
            code: 上次生成的代码
            error: 错误信息

        Returns:
            list: 更新后的消息列表
        """
        # 截断过长的代码和错误信息
        truncated_code = code[:3000] if len(code) > 3000 else code
        truncated_error = error[:1000] if len(error) > 1000 else error

        error_message = get_error_fix_prompt(truncated_code, truncated_error)

        messages.append({"role": "user", "content": error_message})

        return messages

    @classmethod
    async def run_quick_analysis(
        cls, file_path: str, query: str, db: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """
        快速分析（不保存任务到数据库，用于预览或测试）

        Args:
            file_path: 文件路径
            query: 用户问题
            db: 数据库会话（可选）

        Returns:
            dict: 分析结果
        """
        # 分析文件结构
        file_analysis = FileAnalyzer.analyze_file(file_path)

        if not file_analysis.get("success"):
            return {
                "success": False,
                "error": file_analysis.get("error", "文件分析失败"),
                "output": None,
            }

        # 准备消息
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "system",
                "content": f"""
# 📋 文件结构信息

{file_analysis.get("llm_context", "")}
""",
            },
            {"role": "user", "content": f"文件路径：{file_path}\n用户问题：{query}"},
        ]

        # 生成代码
        code = await cls._generate_code(messages)

        # 执行代码
        execution_result = SandboxService.execute_code(code=code, file_path=file_path)

        return {
            "success": execution_result.get("success", False),
            "output": execution_result.get("output", {}),
            "code": code,
            "file_analysis": file_analysis,
        }
