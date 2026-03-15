from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.core.config import settings

# 1. 构建数据库url
db_url = settings.DATABASE_URL
if db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

# 2. 创建异步引擎
echo = settings.DEBUG
engine = create_async_engine(
    db_url,
    echo=echo,
    pool_size=5,        # 保持5个长连接
    max_overflow=10,    # 允许额外10个临时连接
    pool_pre_ping=True, # 1小时候回收连接，防止数据库侧断开
)

# 创建会话工厂
# expire_on_commit=False: 事务提交后不失效对象属性，方便后续使用
async_session_maker = async_sessionmaker(
    bind=engine,
    expire_on_commit=False
)

# 4. 基础模型类
Base = declarative_base()

# 5. 依赖注入: 获取数据会话
async def get_db():
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()  # 成功则提交事务
        except Exception:
            await session.rollback()  # 失败则回滚事务
            raise
        finally:
            await session.close()  # 关闭会话