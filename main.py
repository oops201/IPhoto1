from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional
import uvicorn
from contextlib import asynccontextmanager

from database import get_db, init_db
from auth import authenticate_user, create_access_token, verify_token
from models import User
import sqlite3

# Pydantic模型
class Token(BaseModel):
    """令牌响应模型"""
    access_token: str
    token_type: str = "bearer"


class UserBase(BaseModel):
    """用户基础模型"""
    username: str
    email: str
    is_active: bool

    class Config:
        from_attributes = True


# 创建FastAPI应用
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    print("🚀 启动智能证件照系统...")
    await init_db()
    print("✅ 数据库初始化完成")

    yield

    # 关闭时
    print("👋 关闭应用...")


app = FastAPI(
    title="智能证件照系统",
    description="智能证件照处理系统后端API",
    version="1.0.0",
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

# OAuth2密码模式
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


# 健康检查端点
@app.get("/")
async def root():
    """根端点"""
    return {
        "message": "欢迎使用智能证件照系统",
        "endpoints": {
            "login": "POST /login - 用户登录",
            "me": "GET /me - 获取当前用户信息"
        }
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


# 登录路由
@app.post("/login", response_model=Token)
async def login(
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: AsyncSession = Depends(get_db)
):
    """
    用户登录

    使用测试用户登录：
    - 用户名: testuser
    - 密码: Test123!
    """
    # 认证用户
    user = await authenticate_user(db, form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 创建访问令牌
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


# 获取当前用户信息的依赖项
async def get_current_user(
        token: str = Depends(oauth2_scheme),
        db: AsyncSession = Depends(get_db)
):
    """获取当前登录用户"""
    from sqlalchemy import select

    # 验证令牌
    payload = verify_token(token)
    username: str = payload.get("sub")

    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的令牌"
        )

    # 查询用户
    result = await db.execute(
        select(User).where(User.username == username)
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户已被禁用"
        )

    return user


# 获取当前用户信息
@app.get("/me", response_model=UserBase)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """获取当前登录用户的信息"""
    return current_user


# 受保护的路由示例
@app.get("/protected")
async def protected_route(current_user: User = Depends(get_current_user)):
    """需要登录才能访问的受保护路由"""
    return {
        "message": f"你好, {current_user.username}!",
        "user_id": current_user.id,
        "email": current_user.email
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )