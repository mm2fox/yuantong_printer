from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import text
from .config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=True)

AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        try:
            await conn.execute(text("ALTER TABLE fahui_records ADD COLUMN xm VARCHAR(50)"))
        except Exception:
            pass
        try:
            await conn.execute(text("ALTER TABLE fahui_records ADD COLUMN xm6 VARCHAR(50)"))
        except Exception:
            pass
        try:
            await conn.execute(text("ALTER TABLE fahui_records ADD COLUMN xm7 VARCHAR(50)"))
        except Exception:
            pass
        try:
            await conn.execute(text("ALTER TABLE fahui_records ADD COLUMN xm8 VARCHAR(50)"))
        except Exception:
            pass
        try:
            await conn.execute(text("ALTER TABLE fahui_records ADD COLUMN xm9 VARCHAR(50)"))
        except Exception:
            pass
        try:
            await conn.execute(text("ALTER TABLE fahui_records ADD COLUMN xm10 VARCHAR(50)"))
        except Exception:
            pass
