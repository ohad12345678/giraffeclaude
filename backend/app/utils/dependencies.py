from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from .database import get_db
from .security import verify_token, check_permission, validate_branch_access
from ..models.user import User

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    scopes={
        "admin": "Full administrative access",
        "manager": "Manager access to all branches",
        "branch_manager": "Access to specific branches only", 
        "viewer": "Read-only access"
    }
)

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user"""
    token_data = verify_token(token)
    
    user = db.query(User).filter(
        User.username == token_data.username,
        User.is_active == True
    ).first()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def require_permission(permission: str):
    """Decorator to require specific permission"""
    def permission_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if not check_permission(current_user.permissions or {}, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permission: {permission}"
            )
        return current_user
    return permission_checker

def require_role(required_role: str):
    """Decorator to require specific role"""
    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role != required_role and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required role: {required_role}"
            )
        return current_user
    return role_checker

def require_branch_access(branch: str):
    """Decorator to require access to specific branch"""
    def branch_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if not validate_branch_access(current_user.assigned_branches or [], branch):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"No access to branch: {branch}"
            )
        return current_user
    return branch_checker

# Pre-built dependency functions
get_admin_user = require_role("admin")
get_manager_user = require_role("manager")

def get_user_with_export_permission():
    return require_permission("can_export_data")

def get_user_with_ai_access():
    return require_permission("can_access_ai")
