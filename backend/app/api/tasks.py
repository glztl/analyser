from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.task import AnalysisTask, TaskStatus
from pydantic import BaseModel, ConfigDict
from app.services.agent_service import AgentService
from typing import Optional, Dict, Any

router = APIRouter(prefix="/tasks", tags=["Tasks"])


class TaskCreate(BaseModel):
    query: str
    file_path: str


# 🔥 加 output 字段，返回分析结果和图表配置
class TaskResponse(BaseModel):
    id: int
    query: str
    status: str
    file_path: Optional[str] = None
    result_path: Optional[str] = None
    error_message: Optional[str] = None
    output: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(task_data: TaskCreate, db: AsyncSession = Depends(get_db)):
    # 1. 创建任务
    new_task = AnalysisTask(
        query=task_data.query, file_path=task_data.file_path, status=TaskStatus.PENDING
    )
    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)

    # 2. 🔥 同步执行，等待AI分析+沙箱执行完成
    analysis_result = await AgentService.run_analysis(task_id=new_task.id, db=db)

    # 3. 刷新最新状态
    await db.refresh(new_task)

    # 4. 🔥 构造返回值，包含 output
    return TaskResponse(
        id=new_task.id,
        query=new_task.query,
        status=new_task.status.value,
        file_path=new_task.file_path,
        result_path=new_task.result_path,
        error_message=new_task.error_message,
        output=analysis_result.get("result", {}),  # 🔥 返回沙箱的输出
    )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AnalysisTask).where(AnalysisTask.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskResponse(
        id=task.id,
        query=task.query,
        status=task.status.value,
        file_path=task.file_path,
        result_path=task.result_path,
        error_message=task.error_message,
        output=None,  # 查询接口暂时不返回output，需要的话可以从code_snapshot还原
    )
