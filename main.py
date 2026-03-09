from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession
import uvicorn
import logging
from contextlib import asynccontextmanager
from datetime import datetime
import os

from config import settings
from database import engine, init_db, get_db
from api import auth, users, images
from dependencies import log_usage
from utils.security import get_password_hash

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    logger.info("启动智能证件照处理系统...")

    # 创建数据库表
    try:
        await init_db()
        logger.info("数据库初始化完成")

        # 创建上传目录
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        logger.info(f"创建上传目录: {settings.UPLOAD_DIR}")

    except Exception as e:
        logger.error(f"启动失败: {e}")
        raise

    yield

    # 关闭时
    logger.info("关闭应用...")
    await engine.dispose()


# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="智能证件照处理系统后端API",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"全局异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "服务器内部错误"}
    )


# 中间件：记录请求时间
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = datetime.utcnow()
    response = await call_next(request)
    process_time = (datetime.utcnow() - start_time).total_seconds() * 1000
    response.headers["X-Process-Time"] = f"{process_time:.2f}ms"
    return response


# 中间件：记录访问日志
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"请求: {request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"响应: {request.method} {request.url.path} - {response.status_code}")
    return response


# 健康检查端点
@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION
    }


# 根端点
@app.get("/")
async def root():
    """根端点"""
    return {
        "message": f"欢迎使用{settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/docs" if settings.DEBUG else None,
        "endpoints": {
            "auth": "/api/auth",
            "users": "/api/users",
            "images": "/api/images"
        }
    }


# 注册API路由
app.include_router(auth.router, prefix="/api/auth")
app.include_router(users.router, prefix="/api/users")
# 注意：images路由将在后续步骤中创建

# 挂载静态文件（用于存储上传的文件）
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )