from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.task import AnalysisTask, TaskStatus
from app.services.agent_service import AgentService
from pydantic import BaseModel
from app.services.sandbox_service import SandboxService
from typing import Optional, Dict, Any
import os
import logging
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analysis", tags=["Analysis"])


class AnalysisRequest(BaseModel):
    task_id: int


class AnalysisResponse(BaseModel):
    task_id: int
    status: str
    message: str
    output: Optional[Dict[str, Any]] = None


class AnalysisStatusResponse(BaseModel):
    """分析任务状态响应"""

    task_id: int
    status: str  # pending | processing | completed | failed
    message: str | None = None  # 错误或完成消息
    result_path: str | None = None  # 图表路径

    class Config:
        from_attributes = True


@router.post("/start", response_model=AnalysisResponse)
async def start_analysis(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    启用分析任务
    使用 BackgroundTasks 异步执行，避免 API 超时
    """
    # 验证任务存在
    task = await db.get(AnalysisTask, request.task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.status != TaskStatus.PENDING:
        raise HTTPException(status_code=400, detail="Task is not in pending status")

    # 将耗时任务放入后台执行
    # 生产环境放入 Celery 队列
    background_tasks.add_task(AgentService.run_analysis, request.task_id, db)

    return AnalysisResponse(
        task_id=task.id,
        status=task.status.value,
        message="Analysis task started in background",
    )


@router.get("/status/{task_id}", response_model=AnalysisStatusResponse)
async def get_analysis_status(task_id: int, db: AsyncSession = Depends(get_db)):
    """
    查看任务状态
    """
    task = await db.get(AnalysisTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    # ✅ 根据状态生成友好消息
    message = None
    if task.status == "failed":
        message = task.error_message
    elif task.status == "completed":
        message = "分析完成"
    # pending/processing 时 message 为 None，前端显示 "处理中..."

    return AnalysisStatusResponse(
        task_id=task_id,
        status=task.status.value if hasattr(task.status, "value") else task.status,
        message=task.error_message or "Processing",
        result_path=task.result_path,
    )


@router.post("/execute/{task_id}", response_model=AnalysisResponse)
async def execute_analysis_task(task_id: int, db: AsyncSession = Depends(get_db)):
    task = await db.get(AnalysisTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if not task.code_snapshot:
        raise HTTPException(status_code=400, detail="No code to execute")

    from pathlib import Path

    base_dir = Path(__file__).parent.parent.parent
    real_file_path = base_dir / task.file_path
    real_file_path = str(real_file_path.resolve())

    try:
        sandbox_result = SandboxService.execute_code(
            code=task.code_snapshot, file_path=real_file_path
        )

        if sandbox_result["success"]:
            task.status = TaskStatus.COMPLETED
            task.result_path = sandbox_result["output"].get(
                "chart_path", ""
            )  # 图片路径
            task.error_message = ""
        else:
            task.status = TaskStatus.FAILED
            task.error_message = "\n".join(sandbox_result["errors"])

        await db.commit()

        return AnalysisResponse(
            task_id=task_id,
            status=task.status.value,
            message=task.error_message or "Execution success",
            output=sandbox_result["output"],
        )

    except Exception as e:
        task.status = TaskStatus.FAILED
        task.error_message = str(e)
        await db.commit()
        raise HTTPException(status_code=500, detail=f"Execution failed: {str(e)}")
