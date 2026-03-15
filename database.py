import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from dotenv import load_dotenv
from models import Base

# 加载环境变量
load_dotenv()

# 创建异步数据库引擎
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./test.db")
engine = create_async_engine(DATABASE_URL, echo=True)

# 创建异步会话工厂
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_db():
    """获取数据库会话的依赖项"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """初始化数据库（创建表）"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 测试数据库连接
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT 1"))
        print(f"✅ 数据库连接成功: {result.scalar() == 1}")

    # 创建测试用户（如果不存在）
    await create_test_user()


async def create_test_user():
    """创建测试用户"""
    from auth import get_password_hash
    from sqlalchemy import select

    async with AsyncSessionLocal() as session:
        # 检查测试用户是否存在
        result = await session.execute(
            select(User).where(User.username == "testuser")
        )
        user = result.scalar_one_or_none()

        if not user:
            # 创建测试用户
            test_user = User(
                username="testuser",
                email="test@example.com",
                hashed_password=get_password_hash("Test123!"),  # 密码: Test123!
                is_active=True
            )
            session.add(test_user)
            await session.commit()
            print("✅ 测试用户已创建: testuser / Test123!")