from typing import Generic, TypeVar
from pydantic import BaseModel
T=TypeVar("T")
class ErrorDetail(BaseModel): code: str; message: str
class ErrorResponse(BaseModel): error: ErrorDetail
class Page(BaseModel, Generic[T]): items: list[T]; page: int; page_size: int; total: int
