# app/services/agent_service.py
from app.services.llm_service import llm_service
from app.services.sandbox_service import SandboxService
from app.core.prompts import SYSTEM_PROMPT, get_error_fix_prompt
from app.models.task import TaskStatus
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.task import AnalysisTask
from app.core.config import settings
from openai.types.chat import ChatCompletionMessageParam
from typing import cast
import logging

logger = logging.getLogger(__name__)


class AgentService:
    """
    Agent 核心服务
    负责编排 LLM 沙箱的交互流程
    """

    @staticmethod
    async def run_analysis(task_id: int, db: AsyncSession) -> dict:
        """
        执行分析任务
        包含自我修正循环
        """
        # 1. 获取任务信息
        result = await db.execute(
            select(AnalysisTask).where(AnalysisTask.id == task_id)
        )
        task = result.scalar_one_or_none()

        if not task:
            raise ValueError("Task not found")

        # 更新状态为处理中
        task.status = TaskStatus.IN_PROGRESS
        await db.commit()

        # 2. 准备消息历史
        messages: list[ChatCompletionMessageParam] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"文件路径: {task.file_path}\n用户问题: {task.query}",
            },
        ]

        code = ""
        execution_result = {}

        # 3. 自我修正循环 (Max Retries)
        for attempt in range(settings.AGENT_MAX_RETRIES + 1):
            try:
                # A. 生成/修复代码
                if attempt == 0:
                    logger.info(f"Task {task_id}: Generating initial code...")
                    code = await llm_service.generate_code(messages=messages)
                else:
                    logger.info(
                        f"Task {task_id}: Attempting fix ({attempt}/{settings.AGENT_MAX_RETRIES})"
                    )
                    messages.append(
                        {
                            "role": "user",
                            "content": get_error_fix_prompt(
                                code, execution_result.get("errors", ["Unknow error"])
                            ),
                        }
                    )
                    code = await llm_service.generate_code(messages=messages)

                # 记录代码快照
                task.code_snapshot = code
                await db.commit()

                # 执行代码
                logger.info(f"Task {task_id}: Executing code...")
                execution_result = SandboxService.execute_code(code, task.file_path)

                # 检查结果
                if execution_result.get("success"):
                    logger.info(f"Task {task_id}: Execution successful!")
                    task.status = TaskStatus.COMPLETED
                    task.result_path = execution_result["output"].get("chart_path", "")
                    await db.commit()
                    return {
                        "success": True,
                        "result": execution_result.get("output", {}),
                        "attempts": attempt + 1,
                    }
                else:
                    # 执行失败，进入下一次循环重试
                    logger.warning(
                        f"Task {task_id}: Execution failed: {execution_result.get('errors')}"
                    )

            except Exception as e:
                logger.error(f"Task {task_id}: Agent error: {e}")

        # 4. 循环结束仍失败
        task.status = TaskStatus.FAILED
        task.error_message = str(execution_result.get("errors", ["Unknown failure"]))
        await db.commit()

        return {
            "success": False,
            "error": task.error_message,
            "attempts": settings.AGENT_MAX_RETRIES + 1,
        }
