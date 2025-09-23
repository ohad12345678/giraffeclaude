from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session

from ...utils.database import get_db
from ...utils.dependencies import get_current_active_user, require_permission
from ...services.check_service import CheckService
from ...schemas.check import (
    QualityCheck, QualityCheckCreate, QualityCheckUpdate, QualityCheckFilter,
    QualityCheckStats, QualityCheckResolution, BulkCheckCreate,
    CheckResponse, CheckListResponse, CheckStatsResponse
)
from ...schemas.common import PaginationParams, SortParams, PaginatedResponse
from ...models.user import User
from ...models.quality_check import CheckStatus

router = APIRouter(prefix="/checks", tags=["Quality Checks"])

@router.post("", response_model=CheckResponse)
async def create_quality_check(
    check_data: QualityCheckCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create new quality check"""
    check_service = CheckService(db)
    
    new_check = check_service.create_check(check_data, current_user)
    
    return CheckResponse(
        status="success",
        message="Quality check created successfully",
        data=new_check
    )

@router.get("", response_model=CheckListResponse)
async def get_quality_checks(
    # Pagination
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    
    # Sorting
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    
    # Filters
    branch_id: Optional[int] = Query(None),
    branch_name: Optional[str] = Query(None),
    chef_name: Optional[str] = Query(None),
    dish_name: Optional[str] = Query(None),
    status: Optional[CheckStatus] = Query(None),
    priority: Optional[str] = Query(None),
    score_min: Optional[int] = Query(None, ge=1, le=10),
    score_max: Optional[int] = Query(None, ge=1, le=10),
    low_scores_only: bool = Query(False),
    
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get paginated list of quality checks with filters"""
    check_service = CheckService(db)
    
    # Build filter object
    filters = QualityCheckFilter(
        branch_id=branch_id,
        branch_name=branch_name,
        chef_name=chef_name,
        dish_name=dish_name,
        status=status,
        priority=priority,
        score_min=score_min,
        score_max=score_max,
        low_scores_only=low_scores_only
    )
    
    pagination = PaginationParams(page=page, size=size)
    sort = SortParams(sort_by=sort_by, sort_order=sort_order)
    
    checks, total = check_service.get_checks(filters, pagination, sort, current_user)
    
    # Calculate pagination info
    pages = (total + size - 1) // size if total > 0 else 1
    
    paginated_response = PaginatedResponse(
        items=checks,
        total=total,
        page=page,
        size=size,
        pages=pages
    )
    
    return CheckListResponse(
        status="success",
        data=paginated_response
    )

@router.get("/{check_id}", response_model=CheckResponse)
async def get_quality_check(
    check_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get specific quality check by ID"""
    check_service = CheckService(db)
    
    check = check_service.get_check(check_id, current_user)
    if not check:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quality check not found"
        )
    
    return CheckResponse(
        status="success",
        data=check
    )

@router.put("/{check_id}", response_model=CheckResponse)
async def update_quality_check(
    check_id: int,
    check_data: QualityCheckUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update existing quality check"""
    check_service = CheckService(db)
    
    updated_check = check_service.update_check(check_id, check_data, current_user)
    
    return CheckResponse(
        status="success",
        message="Quality check updated successfully",
        data=updated_check
    )

@router.post("/{check_id}/resolve", response_model=CheckResponse)
async def resolve_quality_check(
    check_id: int,
    resolution: QualityCheckResolution,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Resolve quality check with resolution notes"""
    check_service = CheckService(db)
    
    resolved_check = check_service.resolve_check(check_id, resolution, current_user)
    
    return CheckResponse(
        status="success",
        message="Quality check resolved successfully",
        data=resolved_check
    )

@router.delete("/{check_id}")
async def delete_quality_check(
    check_id: int,
    current_user: User = Depends(require_permission("can_delete_checks")),
    db: Session = Depends(get_db)
):
    """Delete quality check (admin only)"""
    check_service = CheckService(db)
    
    check_service.delete_check(check_id, current_user)
    
    return {"status": "success", "message": "Quality check deleted successfully"}

@router.get("/stats/overview", response_model=CheckStatsResponse)
async def get_quality_check_stats(
    branch_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get quality check statistics"""
    check_service = CheckService(db)
    
    filters = QualityCheckFilter(branch_id=branch_id) if branch_id else None
    stats = check_service.get_check_stats(filters, current_user)
    
    return CheckStatsResponse(
        status="success",
        data=stats
    )

@router.post("/{check_id}/upload-image")
async def upload_check_image(
    check_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Upload image for quality check"""
    check_service = CheckService(db)
    
    filename = await check_service.upload_image(check_id, file, current_user)
    
    return {
        "status": "success",
        "message": "Image uploaded successfully",
        "filename": filename
    }

@router.get("/alerts/low-scores")
async def get_low_score_alerts(
    days_back: int = Query(7, ge=1, le=30),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get recent low-score quality checks as alerts"""
    check_service = CheckService(db)
    
    alerts = check_service.get_low_score_alerts(current_user, days_back)
    
    return {
        "status": "success",
        "data": alerts,
        "count": len(alerts)
    }

@router.post("/bulk", response_model=List[QualityCheck])
async def bulk_create_checks(
    bulk_data: BulkCheckCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create multiple quality checks in bulk"""
    check_service = CheckService(db)
    
    created_checks = check_service.bulk_create_checks(bulk_data.checks, current_user)
    
    return created_checks
