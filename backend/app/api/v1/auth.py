from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ...utils.database import get_db
from ...utils.dependencies import (
    get_current_active_user, get_admin_user, require_permission
)
from ...services.auth_service import AuthService
from ...schemas.auth import (
    LoginResponse, Token, User, UserCreate, UserUpdate, 
    ChangePasswordRequest, UserSummary
)
from ...schemas.common import BaseResponse
from ...models.user import User as UserModel

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=LoginResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """User login endpoint"""
    auth_service = AuthService(db)
    
    # Create login request from form data
    from ...schemas.auth import LoginRequest
    login_request = LoginRequest(
        username=form_data.username,
        password=form_data.password
    )
    
    # Authenticate user
    user = auth_service.authenticate_user(login_request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    token_data = auth_service.create_access_token_for_user(user)
    
    return LoginResponse(
        status="success",
        message="Login successful",
        data=Token(**token_data)
    )

@router.get("/me", response_model=User)
async def get_current_user_info(
    current_user: UserModel = Depends(get_current_active_user)
):
    """Get current user information"""
    return current_user

@router.post("/change-password", response_model=BaseResponse)
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Change current user password"""
    auth_service = AuthService(db)
    
    success = auth_service.change_password(current_user, password_data)
    
    return BaseResponse(
        status="success",
        message="Password changed successfully"
    )

@router.post("/users", response_model=User)
async def create_user(
    user_data: UserCreate,
    current_user: UserModel = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Create new user (admin only)"""
    auth_service = AuthService(db)
    
    new_user = auth_service.create_user(user_data, current_user)
    
    return new_user

@router.get("/users", response_model=List[UserSummary])
async def get_users(
    current_user: UserModel = Depends(require_permission("can_manage_users")),
    db: Session = Depends(get_db)
):
    """Get all users (admin only)"""
    users = db.query(UserModel).filter(UserModel.is_active == True).all()
    return users

@router.get("/users/{user_id}", response_model=User)
async def get_user(
    user_id: int,
    current_user: UserModel = Depends(require_permission("can_manage_users")),
    db: Session = Depends(get_db)
):
    """Get specific user by ID"""
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user

@router.put("/users/{user_id}", response_model=User)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update user information"""
    auth_service = AuthService(db)
    
    updated_user = auth_service.update_user(user_id, user_data, current_user)
    
    return updated_user

@router.post("/users/{user_id}/deactivate", response_model=User)
async def deactivate_user(
    user_id: int,
    current_user: UserModel = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Deactivate user (admin only)"""
    auth_service = AuthService(db)
    
    deactivated_user = auth_service.deactivate_user(user_id, current_user)
    
    return deactivated_user

@router.post("/refresh", response_model=LoginResponse)
async def refresh_token(
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Refresh access token"""
    auth_service = AuthService(db)
    
    token_data = auth_service.create_access_token_for_user(current_user)
    
    return LoginResponse(
        status="success",
        message="Token refreshed successfully",
        data=Token(**token_data)
    )
