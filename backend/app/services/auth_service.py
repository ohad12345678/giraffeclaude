from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from ..models.user import User, UserRole
from ..schemas.auth import UserCreate, UserUpdate, LoginRequest, ChangePasswordRequest
from ..utils.security import verify_password, get_password_hash, create_access_token
from ..utils.config import settings

class AuthService:
    def __init__(self, db: Session):
        self.db = db
    
    def authenticate_user(self, login_data: LoginRequest) -> Optional[User]:
        """Authenticate user with username/password"""
        user = self.db.query(User).filter(
            User.username == login_data.username,
            User.is_active == True
        ).first()
        
        if not user or not verify_password(login_data.password, user.hashed_password):
            return None
        
        # Update last login time
        user.last_login = datetime.utcnow()
        self.db.commit()
        
        return user
    
    def create_user(self, user_data: UserCreate, creator: User) -> User:
        """Create new user (admin only)"""
        # Check if creator has permission
        if creator.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admin can create users"
            )
        
        # Check if username already exists
        if self.db.query(User).filter(User.username == user_data.username).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists"
            )
        
        # Check if email already exists  
        if self.db.query(User).filter(User.email == user_data.email).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )
        
        # Validate branches
        if user_data.assigned_branches:
            invalid_branches = set(user_data.assigned_branches) - set(settings.BRANCHES)
            if invalid_branches:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid branches: {list(invalid_branches)}"
                )
        
        # Create user
        db_user = User(
            username=user_data.username,
            email=user_data.email,
            full_name=user_data.full_name,
            hashed_password=get_password_hash(user_data.password),
            role=user_data.role,
            assigned_branches=user_data.assigned_branches,
            phone=user_data.phone,
            position=user_data.position,
            notes=user_data.notes,
            permissions=user_data.permissions or self._get_default_permissions(user_data.role)
        )
        
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        
        return db_user
    
    def update_user(self, user_id: int, user_data: UserUpdate, updater: User) -> User:
        """Update existing user"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check permissions
        if updater.role != UserRole.ADMIN and updater.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        # Update fields
        update_data = user_data.dict(exclude_unset=True)
        
        # Validate branches if being updated
        if "assigned_branches" in update_data and update_data["assigned_branches"]:
            invalid_branches = set(update_data["assigned_branches"]) - set(settings.BRANCHES)
            if invalid_branches:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid branches: {list(invalid_branches)}"
                )
        
        # Update permissions based on role if role is changing
        if "role" in update_data:
            update_data["permissions"] = self._get_default_permissions(update_data["role"])
        
        for field, value in update_data.items():
            setattr(user, field, value)
        
        user.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def change_password(self, user: User, password_data: ChangePasswordRequest) -> bool:
        """Change user password"""
        if not verify_password(password_data.current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        user.hashed_password = get_password_hash(password_data.new_password)
        user.updated_at = datetime.utcnow()
        self.db.commit()
        
        return True
    
    def create_access_token_for_user(self, user: User) -> Dict[str, Any]:
        """Create access token for authenticated user"""
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        token_data = {
            "sub": user.username,
            "user_id": user.id,
            "role": user.role,
            "permissions": user.permissions or {}
        }
        
        access_token = create_access_token(
            data=token_data,
            expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": {
                "id": user.id,
                "username": user.username,
                "full_name": user.full_name,
                "role": user.role,
                "is_active": user.is_active
            }
        }
    
    def deactivate_user(self, user_id: int, deactivator: User) -> User:
        """Deactivate user (admin only)"""
        if deactivator.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admin can deactivate users"
            )
        
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if user.id == deactivator.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot deactivate yourself"
            )
        
        user.is_active = False
        user.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def _get_default_permissions(self, role: UserRole) -> Dict[str, Any]:
        """Get default permissions based on role"""
        permissions = {
            UserRole.ADMIN: {
                "can_view_all_branches": True,
                "can_manage_users": True,
                "can_export_data": True,
                "can_access_ai": True,
                "can_manage_settings": True,
                "can_delete_checks": True
            },
            UserRole.MANAGER: {
                "can_view_all_branches": True,
                "can_export_data": True,
                "can_access_ai": True,
                "can_manage_settings": False,
                "can_delete_checks": False
            },
            UserRole.BRANCH_MANAGER: {
                "can_view_all_branches": False,
                "can_export_data": True,
                "can_access_ai": False,
                "can_manage_settings": False,
                "can_delete_checks": False
            },
            UserRole.VIEWER: {
                "can_view_all_branches": False,
                "can_export_data": False,
                "can_access_ai": False,
                "can_manage_settings": False,
                "can_delete_checks": False
            }
        }
        
        return permissions.get(role, permissions[UserRole.VIEWER])
