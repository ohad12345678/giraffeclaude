from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_, desc, asc
from fastapi import HTTPException, status, UploadFile
import os
import uuid

from ..models.quality_check import QualityCheck, CheckStatus
from ..models.branch import Branch
from ..models.user import User
from ..schemas.check import (
    QualityCheckCreate, QualityCheckUpdate, QualityCheckFilter,
    QualityCheckStats, QualityCheckResolution
)
from ..schemas.common import PaginationParams, SortParams
from ..utils.config import settings

class CheckService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_check(self, check_data: QualityCheckCreate, user: User) -> QualityCheck:
        """Create new quality check"""
        # Validate branch exists
        branch = self.db.query(Branch).filter(
            Branch.id == check_data.branch_id,
            Branch.is_active == True
        ).first()
        
        if not branch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Branch not found"
            )
        
        # Check if user has access to this branch
        if not user.can_access_branch(branch.name):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No access to this branch"
            )
        
        # Validate dish name
        if check_data.dish_name not in settings.DISHES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid dish name. Must be one of: {settings.DISHES}"
            )
        
        # Create quality check
        db_check = QualityCheck(
            **check_data.dict(),
            submitted_by=user.id,
            status=CheckStatus.OPEN
        )
        
        self.db.add(db_check)
        self.db.commit()
        self.db.refresh(db_check)
        
        return db_check
    
    def get_check(self, check_id: int, user: User) -> Optional[QualityCheck]:
        """Get single quality check by ID"""
        check = self.db.query(QualityCheck).options(
            joinedload(QualityCheck.branch),
            joinedload(QualityCheck.submitted_by_user),
            joinedload(QualityCheck.resolved_by_user)
        ).filter(QualityCheck.id == check_id).first()
        
        if not check:
            return None
        
        # Check access permissions
        if not user.can_access_branch(check.branch.name):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No access to this branch"
            )
        
        return check
    
    def get_checks(self,
                  filters: QualityCheckFilter,
                  pagination: PaginationParams,
                  sort: SortParams,
                  user: User) -> Tuple[List[QualityCheck], int]:
        """Get paginated list of quality checks with filters"""
        
        query = self.db.query(QualityCheck).options(
            joinedload(QualityCheck.branch),
            joinedload(QualityCheck.submitted_by_user)
        )
        
        # Apply user branch restrictions
        if not user.has_permission("can_view_all_branches"):
            user_branches = self.db.query(Branch.id).filter(
                Branch.name.in_(user.assigned_branches or [])
            ).subquery()
            query = query.filter(QualityCheck.branch_id.in_(user_branches))
        
        # Apply filters
        if filters.branch_id:
            query = query.filter(QualityCheck.branch_id == filters.branch_id)
        
        if filters.branch_name:
            query = query.join(Branch).filter(Branch.name == filters.branch_name)
        
        if filters.chef_name:
            query = query.filter(QualityCheck.chef_name.ilike(f"%{filters.chef_name}%"))
        
        if filters.dish_name:
            query = query.filter(QualityCheck.dish_name == filters.dish_name)
        
        if filters.status:
            query = query.filter(QualityCheck.status == filters.status)
        
        if filters.priority:
            query = query.filter(QualityCheck.priority == filters.priority)
        
        if filters.score_min is not None:
            query = query.filter(QualityCheck.overall_score >= filters.score_min)
        
        if filters.score_max is not None:
            query = query.filter(QualityCheck.overall_score <= filters.score_max)
        
        if filters.date_from:
            query = query.filter(QualityCheck.created_at >= filters.date_from)
        
        if filters.date_to:
            query = query.filter(QualityCheck.created_at <= filters.date_to)
        
        if filters.submitted_by:
            query = query.filter(QualityCheck.submitted_by == filters.submitted_by)
        
        if filters.low_scores_only:
            query = query.filter(QualityCheck.overall_score < settings.ALERT_THRESHOLD)
        
        # Get total count
        total = query.count()
        
        # Apply sorting
        sort_column = getattr(QualityCheck, sort.sort_by, QualityCheck.created_at)
        if sort.sort_order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))
        
        # Apply pagination
        offset = (pagination.page - 1) * pagination.size
        checks = query.offset(offset).limit(pagination.size).all()
        
        return checks, total
    
    def update_check(self, check_id: int, check_data: QualityCheckUpdate, user: User) -> QualityCheck:
        """Update existing quality check"""
        check = self.get_check(check_id, user)
        if not check:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quality check not found"
            )
        
        # Check if user can edit this check
        if (check.submitted_by != user.id and 
            not user.has_permission("can_manage_settings")):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only edit your own checks"
            )
        
        # Update fields
        update_data = check_data.dict(exclude_unset=True)
        
        # Validate dish name if being updated
        if "dish_name" in update_data and update_data["dish_name"] not in settings.DISHES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid dish name. Must be one of: {settings.DISHES}"
            )
        
        for field, value in update_data.items():
            setattr(check, field, value)
        
        check.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(check)
        
        return check
    
    def resolve_check(self, check_id: int, resolution: QualityCheckResolution, user: User) -> QualityCheck:
        """Resolve quality check with resolution notes"""
        check = self.get_check(check_id, user)
        if not check:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quality check not found"
            )
        
        # Update resolution info
        check.status = resolution.status
        check.resolution_notes = resolution.resolution_notes
        check.resolved_at = datetime.utcnow()
        check.resolved_by = user.id
        check.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(check)
        
        return check
    
    def delete_check(self, check_id: int, user: User) -> bool:
        """Delete quality check (admin only)"""
        if not user.has_permission("can_delete_checks"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to delete checks"
            )
        
        check = self.get_check(check_id, user)
        if not check:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quality check not found"
            )
        
        self.db.delete(check)
        self.db.commit()
        
        return True
    
    def get_check_stats(self, 
                       filters: Optional[QualityCheckFilter] = None,
                       user: Optional[User] = None) -> QualityCheckStats:
        """Get quality check statistics"""
        
        query = self.db.query(QualityCheck)
        
        # Apply user branch restrictions
        if user and not user.has_permission("can_view_all_branches"):
            user_branches = self.db.query(Branch.id).filter(
                Branch.name.in_(user.assigned_branches or [])
            ).subquery()
            query = query.filter(QualityCheck.branch_id.in_(user_branches))
        
        # Apply filters if provided
        if filters:
            if filters.branch_id:
                query = query.filter(QualityCheck.branch_id == filters.branch_id)
            if filters.date_from:
                query = query.filter(QualityCheck.created_at >= filters.date_from)
            if filters.date_to:
                query = query.filter(QualityCheck.created_at <= filters.date_to)
        
        # Calculate statistics
        checks = query.all()
        
        if not checks:
            return QualityCheckStats()
        
        total_checks = len(checks)
        average_score = sum(c.overall_score for c in checks) / total_checks
        low_score_count = len([c for c in checks if c.overall_score < settings.ALERT_THRESHOLD])
        low_score_percentage = (low_score_count / total_checks) * 100
        
        # Status breakdown
        status_breakdown = {}
        for status in CheckStatus:
            status_breakdown[status.value] = len([c for c in checks if c.status == status])
        
        # Score distribution
        score_distribution = {}
        for i in range(1, 11):
            score_distribution[str(i)] = len([c for c in checks if c.overall_score == i])
        
        return QualityCheckStats(
            total_checks=total_checks,
            average_score=round(average_score, 2),
            low_score_count=low_score_count,
            low_score_percentage=round(low_score_percentage, 2),
            status_breakdown=status_breakdown,
            score_distribution=score_distribution
        )
    
    async def upload_image(self, check_id: int, file: UploadFile, user: User) -> str:
        """Upload image for quality check"""
        check = self.get_check(check_id, user)
        if not check:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quality check not found"
            )
        
        # Validate file type
        if file.content_type not in ["image/jpeg", "image/jpg", "image/png"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file type. Only JPEG and PNG allowed"
            )
        
        # Validate file size
        if file.size > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File too large. Max size: {settings.MAX_FILE_SIZE} bytes"
            )
        
        # Create upload directory if it doesn't exist
        upload_dir = settings.UPLOAD_DIR
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate unique filename
        file_extension = file.filename.split('.')[-1]
        filename = f"{check_id}_{uuid.uuid4()}.{file_extension}"
        file_path = os.path.join(upload_dir, filename)
        
        # Save file
        try:
            with open(file_path, "wb") as f:
                content = await file.read()
                f.write(content)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save file: {str(e)}"
            )
        
        # Update check with image path
        check.image_path = filename
        check.updated_at = datetime.utcnow()
        self.db.commit()
        
        return filename
    
    def get_low_score_alerts(self, user: User, days_back: int = 7) -> List[QualityCheck]:
        """Get recent low-score quality checks as alerts"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days_back)
        
        query = self.db.query(QualityCheck).options(
            joinedload(QualityCheck.branch),
            joinedload(QualityCheck.submitted_by_user)
        ).filter(
            QualityCheck.overall_score < settings.ALERT_THRESHOLD,
            QualityCheck.created_at >= start_date,
            QualityCheck.status.in_([CheckStatus.OPEN, CheckStatus.IN_PROGRESS])
        )
        
        # Apply user branch restrictions
        if not user.has_permission("can_view_all_branches"):
            user_branches = self.db.query(Branch.id).filter(
                Branch.name.in_(user.assigned_branches or [])
            ).subquery()
            query = query.filter(QualityCheck.branch_id.in_(user_branches))
        
        return query.order_by(desc(QualityCheck.created_at)).limit(20).all()
    
    def bulk_create_checks(self, checks_data: List[QualityCheckCreate], user: User) -> List[QualityCheck]:
        """Create multiple quality checks in bulk"""
        if len(checks_data) > 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot create more than 50 checks at once"
            )
        
        created_checks = []
        
        try:
            for check_data in checks_data:
                # Validate each check individually
                branch = self.db.query(Branch).filter(
                    Branch.id == check_data.branch_id,
                    Branch.is_active == True
                ).first()
                
                if not branch:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Branch not found: {check_data.branch_id}"
                    )
                
                if not user.can_access_branch(branch.name):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"No access to branch: {branch.name}"
                    )
                
                db_check = QualityCheck(
                    **check_data.dict(),
                    submitted_by=user.id,
                    status=CheckStatus.OPEN
                )
                
                self.db.add(db_check)
                created_checks.append(db_check)
            
            self.db.commit()
            
            # Refresh all created checks
            for check in created_checks:
                self.db.refresh(check)
            
            return created_checks
            
        except Exception as e:
            self.db.rollback()
            raise e
