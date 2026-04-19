"""Initialize database tables."""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import settings
from app.db.models import Base


async def init_db():
    """Create all database tables."""
    print(f"Connecting to: {settings.database_url}")

    engine = create_async_engine(settings.database_url)

    async with engine.begin() as conn:
        print("Dropping all tables...")
        await conn.run_sync(Base.metadata.drop_all)

        print("Creating all tables...")
        await conn.run_sync(Base.metadata.create_all)

    await engine.dispose()
    print("✅ Database initialized!")


if __name__ == "__main__":
    asyncio.run(init_db())
