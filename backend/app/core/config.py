import os
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # 读取.env文件的配置
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

    # 应用基础信息
    APP_NAME: str = "analyser"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # 数据库配置
    DATABASE_URL: str = "db"

    # Redis 配置
    REDIS_URL: str = "redis:"

    # LLM API 配置
    LLM_API_KEY: str = "your-llm-api-key"
    LLM_MODEL: str = "gpt-4o-mini"

    # 安全配置
    SECRET_KEY: str = "your-secret-key"

    # 文件存储根目录
    UPLOAD_DIR: str = "./uploads"

    # 沙箱输出目录
    SANDBOX_OUTPUT_DIR: str = "./outputs"

    # 允许的文件扩展名
    ALLOWED_EXTENSIONS: set[str] = {".csv", ".xlsx", ".xls"}

    # 最大文件大小 (10MB)
    MAX_FILE_SIZE: int = 10 * 1024 * 1024

    # 配置类内部设置
    model_config = SettingsConfigDict(
        env_file=".env",    # 读取.env文件
        env_file_encoding="utf-8",
        case_sensitive=False,   # 环境遍历不区分大小写
        extra="ignore"  # 忽略.env中多余的变量
    )

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()