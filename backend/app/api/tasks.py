from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.task import AnalysisTask, TaskStatus
from pydantic import BaseModel, ConfigDict
from app.services.agent_service import AgentService
from app.services.file_analyzer import FileAnalyzer
from typing import Optional, Dict, Any
import json

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
    # 分析文件结构
    file_analysis = FileAnalyzer.analyze_file(task_data.file_path)

    if not file_analysis.get("success"):
        # 文件分析失败，直接返回错误信息
        return TaskResponse(
            id=0,
            query=task_data.query,
            status=TaskStatus.FAILED.value,
            file_path=task_data.file_path,
            result_path=None,
            error_message=file_analysis.get("error", "文件分析失败"),
            output=None,
        )

    # 创建任务
    new_task = AnalysisTask(
        query=task_data.query,
        file_path=task_data.file_path,
        status=TaskStatus.PENDING,
        # 保存文件分析结果
        code_snapshot=json.dumps(file_analysis, ensure_ascii=False, default=str)[:1000],
    )
    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)

    # 执行分析
    result = await AgentService.run_analysis(
        new_task.id,
        db,
        file_analysis=file_analysis,
    )

    # 返回结果
    output = None
    if result.get("success") and result.get("output"):
        output = result["output"]
        # 添加文件结构元数据到输出
        output["metadata"] = {
            "file_info": file_analysis.get("file_info"),
            "structure": file_analysis.get("structure"),
            "quality": file_analysis.get("quality"),
            "strategy": file_analysis.get("strategy"),
        }

    return TaskResponse(
        id=new_task.id,
        query=new_task.query,
        status=new_task.status.value,
        file_path=new_task.file_path,
        result_path=new_task.result_path,
        error_message=new_task.error_message,
        output=output,
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
