import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    # 应用配置
    APP_NAME: str = "智能证件照处理系统"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # 数据库配置
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./smart_id_photo.db")

    # JWT配置
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # 安全配置
    BCRYPT_ROUNDS: int = 12

    # 文件上传配置
    MAX_FILE_SIZE_MB: int = 5
    ALLOWED_IMAGE_TYPES: list = ["image/jpeg", "image/png", "image/webp"]
    UPLOAD_DIR: str = "uploads"

    # Redis配置（用于缓存和限流）
    REDIS_URL: Optional[str] = os.getenv("REDIS_URL", "redis://localhost:6379")

    # 限流配置
    RATE_LIMIT_PER_MINUTE: int = 10

    class Config:
        env_file = ".env"


settings = Settings()