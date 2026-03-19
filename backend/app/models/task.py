"""
记录用户提交的每次数据分析任务
"""
# app/models/task.py
from sqlalchemy import String, Integer, Text, Enum
from sqlalchemy.orm import Mapped, mapped_column
from enum import Enum as PyEnum
from app.models.base import CommonBase
from typing import Optional


# 定义任务状态枚举
class TaskStatus(str, PyEnum):
    PENDING = "pending"  # 等待执行
    IN_PROGRESS = "in_progress"  # 执行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败


class AnalysisTask(CommonBase):
    __tablename__ = "analysis_tasks"

    # 主键ID
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True, autoincrement=True
    )

    # 用户 ID (预留字段，未来做多用户系统)
    user_id: Mapped[str] = mapped_column(String(50), nullable=True, index=True)

    # 任务状态
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus), default=TaskStatus.PENDING, nullable=False
    )

    # 用户的问题/查询指令
    query: Mapped[str] = mapped_column(Text, nullable=False)

    # 上传的文件路径 (存储在服务器上的路径)
    file_path: Mapped[str] = mapped_column(String(255), nullable=True)

    # 分析结果文件路径 (如生成的图表、报告)
    result_path: Mapped[str] = mapped_column(String(255), nullable=True)

    # 错误信息 (如果失败，记录原因)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # 执行的代码快照 (用于审计和调试)
    code_snapshot: Mapped[str] = mapped_column(Text, nullable=True)

    def __repr__(self):
        return f"<AnalysisTask(id={self.id}, status={self.status})>"
