from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, JSON, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from ..utils.database import Base

class Branch(Base):
    __tablename__ = "branches"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    
    # Location information
    address = Column(String(255), nullable=True)
    city = Column(String(50), nullable=True)  
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    # Contact information
    phone = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    
    # Management
    manager_name = Column(String(100), nullable=True)
    manager_phone = Column(String(20), nullable=True)
    
    # Operational info
    opening_hours = Column(JSON, nullable=True)  # {"sunday": "10:00-22:00", ...}
    seating_capacity = Column(Integer, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Additional metadata
    notes = Column(Text, nullable=True)
    settings = Column(JSON, nullable=True, default={})  # Branch-specific settings
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    quality_checks = relationship("QualityCheck", back_populates="branch", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Branch(name='{self.name}', city='{self.city}')>"
    
    @property
    def total_checks(self) -> int:
        return len(self.quality_checks)
    
    @property
    def average_score(self) -> float:
        if not self.quality_checks:
            return 0.0
        return sum(check.overall_score for check in self.quality_checks if check.overall_score) / len(self.quality_checks)
    
    @property
    def last_check_date(self) -> DateTime:
        if not self.quality_checks:
            return None
        return max(check.created_at for check in self.quality_checks)