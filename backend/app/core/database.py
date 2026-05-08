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
        for idx_sql in [
            "CREATE INDEX IF NOT EXISTS ix_fahui_records_temple_id ON fahui_records(temple_id)",
            "CREATE INDEX IF NOT EXISTS ix_fahui_records_temple_fahui_name ON fahui_records(temple_id, fahui_name)",
            "CREATE INDEX IF NOT EXISTS ix_fahui_records_temple_djdate ON fahui_records(temple_id, djdate)",
            "CREATE INDEX IF NOT EXISTS ix_fahui_records_temple_prt ON fahui_records(temple_id, prt)",
            "CREATE INDEX IF NOT EXISTS ix_fahui_records_temple_yanwang ON fahui_records(temple_id, yanwang)",
            "CREATE INDEX IF NOT EXISTS ix_fahui_records_施主姓名 ON fahui_records(施主姓名)",
            "CREATE INDEX IF NOT EXISTS ix_fahui_records_施主编号 ON fahui_records(施主编号)",
        ]:
            try:
                await conn.execute(text(idx_sql))
            except Exception:
                pass
