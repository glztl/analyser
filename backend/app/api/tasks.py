from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.task import AnalysisTask, TaskStatus
from pydantic import BaseModel, ConfigDict

router = APIRouter(prefix="/tasks", tags=["Tasks"])

class TaskCreate(BaseModel):
    query: str

class TaskResponse(BaseModel):
    id: int
    query: str
    status: str

    model_config = ConfigDict(from_attributes=True)


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(task_data: TaskCreate, db: AsyncSession = Depends(get_db)):
    # 创建新任务
    new_task = AnalysisTask(
        query=task_data.query,
        status=TaskStatus.PENDING
    )
    db.add(new_task)

    await db.flush()

    # 依赖注入中的 get_db 会自动 commit
    return new_task

@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AnalysisTask).where(AnalysisTask.id == task_id))
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return task
    