from sqlalchemy import Column, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from datetime import datetime

class CommonBase(Base):
    """
    基础模型类
    所有业务表都应继承此类，以获得统一的审计字段
    """
    __abstract__ = True  # 声明为抽象类，不会创建对应的数据库表

    # id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )