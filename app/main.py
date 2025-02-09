from typing import Annotated, Optional
from uuid import UUID, uuid4
from contextlib import asynccontextmanager
from fastapi import FastAPI, Path, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import Text, UUID as UUID_sqlalchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel, Field, ConfigDict

from app.database import get_db, get_engine
from app.exception import ErrorCode, MyCustomException
from app.util.env import get_bool_from_env
from app.logger.logger_setup import setup_request_logger, disable_uvicorn_logs
from app.middleware.json_logger import JsonRequestLoggerMiddleware
from app.exception.handler import my_exception_handler, general_exception_handler

class Base(DeclarativeBase):
    pass

class ItemModel(Base):
    __tablename__ = "items"

    id: Mapped[UUID] = mapped_column(UUID_sqlalchemy,default=lambda x: uuid4(),primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text,nullable=True)
    sensitive_data: Mapped[str] = mapped_column(Text,nullable=False)


class ItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: Optional[UUID] = Field(default=None)
    name: str = Field(...)
    description: Optional[str] = Field(default=None)
    sensitive_data: str = Field(...)
    

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    
app = FastAPI(title="FastAPI Logging Example Application", lifespan=lifespan,version="0.0.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if get_bool_from_env("IS_JSON_LOGGING", True):
    setup_request_logger()      # request-logger를 JSON 포맷으로 설정
    disable_uvicorn_logs()      # uvicorn.access 로그 비활성화
    app.add_middleware(JsonRequestLoggerMiddleware)
else:
    # Uvicorn의 기본 로그 사용
    pass

    
app.add_exception_handler(MyCustomException, my_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

@app.post("/items", status_code=status.HTTP_200_OK, response_model=ItemSchema)
async def create_item(
    item_schema: ItemSchema,
    session:AsyncSession = Depends(get_db)
):
    """
    새로운 Item을 생성합니다.
    """
    try:
        item = ItemModel(**item_schema.model_dump())
        session.add(item)
        await session.commit()
        await session.refresh(item)  # 생성된 Item의 ID를 가져오기 위해 refresh
        return ItemSchema.model_validate(item)
    except IntegrityError:
        await session.rollback()
        raise MyCustomException(ErrorCode.ENTITY_ALREADY_EXISTS, reason="동일한 item 이 이미 존재합니다.")

@app.get("/items/{item_id}", response_model=ItemSchema, status_code=status.HTTP_200_OK)
async def get_item(
    item_id: Annotated[UUID, Path(...)],
    session:AsyncSession = Depends(get_db)
):
    """
    ID로 Item을 조회합니다.
    """
    item = await session.get(ItemModel, item_id)
    if not item:
        raise MyCustomException(ErrorCode.ENTITY_NOT_FOUND, reason="item을 찾을 수 없습니다")
    return ItemSchema.model_validate(item)
