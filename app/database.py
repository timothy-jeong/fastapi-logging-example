import contextvars
import time
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine
from sqlalchemy import event
from fastapi import Request

DATABASE_URL = "sqlite+aiosqlite://"

engine: AsyncEngine = create_async_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})

db_query_time_ms: contextvars.ContextVar[float] = contextvars.ContextVar("db_query_time_ms", default=0.0)

@event.listens_for(engine.sync_engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    context._query_start_time = time.time()

@event.listens_for(engine.sync_engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = time.time() - context._query_start_time
    db_query_time_ms.set(db_query_time_ms.get() + total*1000)


async_session = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

def get_engine():
    return engine

async def reset_db_query_time():
    db_query_time_ms.set(0.0)

# Dependency Injection
async def get_db(request: Request):
    async with async_session() as session:
        try:
            await reset_db_query_time()
            yield session
        finally:
            request.state.db_query_time_ms = db_query_time_ms.get()
            await session.close()