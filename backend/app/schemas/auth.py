from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List, Dict, Any
from datetime import datetime

from ..models.user import UserRole
from .common import BaseResponse

class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: str
    role: UserRole = UserRole.VIEWER
    assigned_branches: Optional[List[str]] = None
    phone: Optional[str] = None
    position: Optional[str] = None
    notes: Optional[str] = None

class UserCreate(UserBase):
    password: str
    permissions: Optional[Dict[str, Any]] = None
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        return v
    
    @validator('username')
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters long')
        if not v.isalnum():
            raise ValueError('Username must contain only letters and numbers')
        return v

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    assigned_branches: Optional[List[str]] = None
    phone: Optional[str] = None
    position: Optional[str] = None
    notes: Optional[str] = None
    permissions: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class UserInDB(UserBase):
    id: int
    is_active: bool
    permissions: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class User(UserInDB):
    pass

class UserSummary(BaseModel):
    id: int
    username: str
    full_name: str
    role: UserRole
    is_active: bool
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserSummary

class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[int] = None
    role: Optional[str] = None

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseResponse):
    data: Optional[Token] = None

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 6:
            raise ValueError('New password must be at least 6 characters long')
        return v

class ResetPasswordRequest(BaseModel):
    username: str
    email: EmailStr

class UserPermissions(BaseModel):
    can_view_all_branches: bool = False
    can_manage_users: bool = False
    can_export_data: bool = False
    can_access_ai: bool = False
    can_manage_settings: bool = False
    can_delete_checks: bool = False
    
class RolePermissions(BaseModel):
    admin: UserPermissions = UserPermissions(
        can_view_all_branches=True,
        can_manage_users=True,
        can_export_data=True,
        can_access_ai=True,
        can_manage_settings=True,
        can_delete_checks=True
    )
    manager: UserPermissions = UserPermissions(
        can_view_all_branches=True,
        can_export_data=True,
        can_access_ai=True
    )
    branch_manager: UserPermissions = UserPermissions(
        can_export_data=True
    )
    viewer: UserPermissions = UserPermissions()
