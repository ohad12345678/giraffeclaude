from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from enum import Enum

from ..utils.database import Base

class UserRole(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"  
    BRANCH_MANAGER = "branch_manager"
    VIEWER = "viewer"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(100), nullable=False)
    full_name = Column(String(100), nullable=False)
    
    # Role and permissions
    role = Column(String(20), default=UserRole.VIEWER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Branch assignments (JSON array of branch names)
    assigned_branches = Column(JSON, nullable=True)
    
    # Permissions (JSON object with permission flags)
    permissions = Column(JSON, nullable=True, default={})
    
    # Profile information
    phone = Column(String(20), nullable=True)
    position = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    quality_checks = relationship("QualityCheck", back_populates="submitted_by_user", foreign_keys="QualityCheck.submitted_by")
    
    def __repr__(self):
        return f"<User(username='{self.username}', role='{self.role}')>"
    
    @property
    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN
    
    @property
    def can_access_branch(self, branch_name: str) -> bool:
        if self.role == UserRole.ADMIN:
            return True
        if not self.assigned_branches:
            return False
        return branch_name in self.assigned_branches
    
    def has_permission(self, permission: str) -> bool:
        if self.role == UserRole.ADMIN:
            return True
        return self.permissions.get(permission, False) if self.permissions else False