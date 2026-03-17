from fastapi import FastAPI
from app.core.config import settings
from app.api import tasks, files, analysis

import logging

# 创建 FastAPI 实例
app = FastAPI(
    title=settings.APP_NAME, version=settings.APP_VERSION, debug=settings.DEBUG
)

app.include_router(tasks.router)
app.include_router(files.router)
app.include_router(analysis.router)


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
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
        "debug": settings.DEBUG,
    }


@app.get("/health")
async def health_check():
    """
    深度健康检查
    """
    return {"status": "healthy"}
