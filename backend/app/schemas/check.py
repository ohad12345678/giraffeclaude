from pydantic import BaseModel, validator, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

from ..models.quality_check import CheckStatus
from .common import BaseResponse, PaginatedResponse

class QualityCheckBase(BaseModel):
    branch_id: int
    chef_name: str
    dish_name: str
    overall_score: int = Field(..., ge=1, le=10, description="Overall quality score (1-10)")
    
    # Optional detailed scores
    taste_score: Optional[int] = Field(None, ge=1, le=10)
    appearance_score: Optional[int] = Field(None, ge=1, le=10)
    temperature_score: Optional[int] = Field(None, ge=1, le=10)
    preparation_time_score: Optional[int] = Field(None, ge=1, le=10)
    portion_size_score: Optional[int] = Field(None, ge=1, le=10)
    
    notes: Optional[str] = None
    priority: Optional[str] = Field("medium", regex="^(low|medium|high|urgent)$")
    metadata: Optional[Dict[str, Any]] = None

class QualityCheckCreate(QualityCheckBase):
    pass

class QualityCheckUpdate(BaseModel):
    chef_name: Optional[str] = None
    dish_name: Optional[str] = None
    overall_score: Optional[int] = Field(None, ge=1, le=10)
    
    # Optional detailed scores
    taste_score: Optional[int] = Field(None, ge=1, le=10)
    appearance_score: Optional[int] = Field(None, ge=1, le=10)
    temperature_score: Optional[int] = Field(None, ge=1, le=10)
    preparation_time_score: Optional[int] = Field(None, ge=1, le=10)
    portion_size_score: Optional[int] = Field(None, ge=1, le=10)
    
    notes: Optional[str] = None
    status: Optional[CheckStatus] = None
    priority: Optional[str] = Field(None, regex="^(low|medium|high|urgent)$")
    metadata: Optional[Dict[str, Any]] = None

class QualityCheckInDB(QualityCheckBase):
    id: int
    status: CheckStatus
    image_path: Optional[str] = None
    resolution_notes: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[int] = None
    submitted_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class QualityCheck(QualityCheckInDB):
    # Additional computed fields
    is_low_score: Optional[bool] = None
    average_detailed_score: Optional[float] = None
    score_breakdown: Optional[Dict[str, Optional[float]]] = None
    
    # Related data
    branch_name: Optional[str] = None
    submitted_by_name: Optional[str] = None
    resolved_by_name: Optional[str] = None

class QualityCheckSummary(BaseModel):
    id: int
    branch_id: int
    branch_name: str
    chef_name: str
    dish_name: str
    overall_score: int
    status: CheckStatus
    priority: str
    is_low_score: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class QualityCheckResolution(BaseModel):
    resolution_notes: str
    status: CheckStatus = CheckStatus.RESOLVED
    
    @validator('status')
    def validate_resolution_status(cls, v):
        if v not in [CheckStatus.RESOLVED, CheckStatus.CLOSED]:
            raise ValueError('Resolution status must be resolved or closed')
        return v

class QualityCheckFilter(BaseModel):
    branch_id: Optional[int] = None
    branch_name: Optional[str] = None
    chef_name: Optional[str] = None
    dish_name: Optional[str] = None
    status: Optional[CheckStatus] = None
    priority: Optional[str] = None
    score_min: Optional[int] = Field(None, ge=1, le=10)
    score_max: Optional[int] = Field(None, ge=1, le=10)
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    submitted_by: Optional[int] = None
    low_scores_only: Optional[bool] = False

class QualityCheckStats(BaseModel):
    total_checks: int = 0
    average_score: float = 0.0
    low_score_count: int = 0
    low_score_percentage: float = 0.0
    status_breakdown: Dict[str, int] = {}
    score_distribution: Dict[str, int] = {}
    
class BulkCheckCreate(BaseModel):
    checks: List[QualityCheckCreate]
    
    @validator('checks')
    def validate_checks_count(cls, v):
        if len(v) > 50:
            raise ValueError('Cannot create more than 50 checks at once')
        return v

class CheckResponse(BaseResponse):
    data: Optional[QualityCheck] = None

class CheckListResponse(BaseResponse):
    data: Optional[PaginatedResponse] = None

class CheckStatsResponse(BaseResponse):
    data: Optional[QualityCheckStats] = None

# File upload schemas
class ImageUpload(BaseModel):
    filename: str
    content_type: str
    size: int
    
    @validator('content_type')
    def validate_content_type(cls, v):
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png']
        if v not in allowed_types:
            raise ValueError(f'Content type must be one of {allowed_types}')
        return v
    
    @validator('size')
    def validate_size(cls, v):
        max_size = 5 * 1024 * 1024  # 5MB
        if v > max_size:
            raise ValueError(f'File size cannot exceed {max_size} bytes')
        return v
