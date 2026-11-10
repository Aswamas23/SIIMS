from fastapi import Query
from typing import TypeVar, Generic, List
from pydantic import BaseModel
import math


class PaginationParams:
    """FastAPI dependency for pagination query parameters."""

    def __init__(
        self,
        skip: int = Query(default=0, ge=0, description="Number of records to skip"),
        limit: int = Query(default=50, ge=1, le=500, description="Max records to return"),
    ):
        self.skip = skip
        self.limit = limit

    @property
    def page(self) -> int:
        if self.limit == 0:
            return 1
        return (self.skip // self.limit) + 1


T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    pages: int

    @classmethod
    def create(cls, items: List[T], total: int, pagination: PaginationParams) -> "PaginatedResponse[T]":
        pages = math.ceil(total / pagination.limit) if pagination.limit > 0 else 1
        return cls(
            items=items,
            total=total,
            page=pagination.page,
            pages=max(1, pages),
        )
