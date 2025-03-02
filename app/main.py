from typing import Annotated, Optional
from uuid import UUID, uuid4
from contextlib import asynccontextmanager
from fastapi import FastAPI, Path, status, Depends
from fastapi.exceptions import HTTPException
from sqlalchemy import Text, UUID as UUID_sqlalchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel, Field, ConfigDict
import uvicorn

from app.exception import ErrorCode, MyCustomException
from app.middleware.json_logger import JsonRequestLoggerMiddleware
from app.exception.handler import my_exception_handler, general_exception_handler, http_exception_handler


###############
# db setting ##
###############
DATABASE_URL = "sqlite+aiosqlite://"
engine: AsyncEngine = create_async_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})
async_session = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
async def get_db():
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
            
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


################
# app setting ##
################
@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    
app = FastAPI(title="FastAPI Logging Example Application", lifespan=lifespan,version="0.2.0")
app.add_middleware(JsonRequestLoggerMiddleware)
app.add_exception_handler(MyCustomException, my_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)


###################
# path operation ##
###################
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

############
## force 
###########
# if __name__ == '__main__':
#     uvicorn.run(
#         JsonRequestLoggerMiddleware(app=app),
#         host='0.0.0.0',
#         port=8000
#     )