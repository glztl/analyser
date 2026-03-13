from fastapi import FastAPI
from app.core.config import settings

# 创建 FastAPI 实例
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG
)

@app.get("/")
async def root():
    """
    健康检查接口
    用于验证服务是否启动，配置是否加载成功
    """
    return {
        "message": settings.APP_NAME + " API is running!",
        "version": settings.APP_VERSION,
        "debug": settings.DEBUG
    }

@app.get("/health")
async def health_check():
    """
    深度健康检查
    """
    return {"status": "healthy"}