from pydantic import BaseModel, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class ResponseStatus(str, Enum):
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"

class BaseResponse(BaseModel):
    status: ResponseStatus = ResponseStatus.SUCCESS
    message: Optional[str] = None
    
class PaginationParams(BaseModel):
    page: int = 1
    size: int = 20
    
    @validator('page')
    def page_must_be_positive(cls, v):
        if v < 1:
            raise ValueError('Page must be positive')
        return v
    
    @validator('size') 
    def size_must_be_reasonable(cls, v):
        if v < 1 or v > 100:
            raise ValueError('Size must be between 1 and 100')
        return v

class PaginatedResponse(BaseModel):
    items: List[Any] = []
    total: int = 0
    page: int = 1
    size: int = 20
    pages: int = 1
    
    @validator('pages', always=True)
    def calculate_pages(cls, v, values):
        total = values.get('total', 0)
        size = values.get('size', 20)
        return (total + size - 1) // size if total > 0 else 1

class FilterParams(BaseModel):
    search: Optional[str] = None
    branch: Optional[str] = None
    status: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    score_min: Optional[int] = None
    score_max: Optional[int] = None
    
class SortParams(BaseModel):
    sort_by: str = "created_at"
    sort_order: str = "desc"
    
    @validator('sort_order')
    def validate_sort_order(cls, v):
        if v not in ['asc', 'desc']:
            raise ValueError('Sort order must be asc or desc')
        return v

class DateRange(BaseModel):
    start_date: datetime
    end_date: datetime
    
    @validator('end_date')
    def end_after_start(cls, v, values):
        start_date = values.get('start_date')
        if start_date and v < start_date:
            raise ValueError('End date must be after start date')
        return v

class ScoreRange(BaseModel):
    min_score: int = 1
    max_score: int = 10
    
    @validator('min_score')
    def validate_min_score(cls, v):
        if v < 1 or v > 10:
            raise ValueError('Min score must be between 1 and 10')
        return v
    
    @validator('max_score')
    def validate_max_score(cls, v, values):
        min_score = values.get('min_score', 1)
        if v < 1 or v > 10:
            raise ValueError('Max score must be between 1 and 10')
        if v < min_score:
            raise ValueError('Max score must be greater than or equal to min score')
        return v

class BranchFilter(BaseModel):
    branches: Optional[List[str]] = None
    exclude_branches: Optional[List[str]] = None

class TimeGrouping(str, Enum):
    DAY = "day"
    WEEK = "week" 
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"
