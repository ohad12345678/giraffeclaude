from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, JSON, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from enum import Enum
from typing import Optional

from ..utils.database import Base

class CheckStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"  
    RESOLVED = "resolved"
    CLOSED = "closed"

class QualityCheck(Base):
    __tablename__ = "quality_checks"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Basic Information
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False)
    chef_name = Column(String(100), nullable=False)
    dish_name = Column(String(100), nullable=False)
    
    # Overall Score (Required)
    overall_score = Column(Integer, nullable=False)  # 1-10 scale
    
    # Detailed Scores (Optional) 
    taste_score = Column(Integer, nullable=True)  # 1-10 scale
    appearance_score = Column(Integer, nullable=True)  # 1-10 scale
    temperature_score = Column(Integer, nullable=True)  # 1-10 scale
    preparation_time_score = Column(Integer, nullable=True)  # 1-10 scale
    portion_size_score = Column(Integer, nullable=True)  # 1-10 scale
    
    # Additional Information
    notes = Column(Text, nullable=True)
    image_path = Column(String(255), nullable=True)  # Path to uploaded image
    
    # Status and Management
    status = Column(String(20), default=CheckStatus.OPEN, nullable=False)
    priority = Column(String(10), default="medium", nullable=False)  # low, medium, high, urgent
    
    # Resolution tracking
    resolution_notes = Column(Text, nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Submission info
    submitted_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Additional metadata
    metadata = Column(JSON, nullable=True, default={})  # Extra flexible data
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    branch = relationship("Branch", back_populates="quality_checks")
    submitted_by_user = relationship("User", back_populates="quality_checks", foreign_keys=[submitted_by])
    resolved_by_user = relationship("User", foreign_keys=[resolved_by])
    
    def __repr__(self):
        return f"<QualityCheck(dish='{self.dish_name}', branch='{self.branch.name if self.branch else 'Unknown'}', score={self.overall_score})>"
    
    @property
    def is_low_score(self) -> bool:
        """Check if score is below alert threshold"""
        from ..utils.config import settings
        return self.overall_score < settings.ALERT_THRESHOLD
    
    @property
    def average_detailed_score(self) -> Optional[float]:
        """Calculate average of detailed scores if available"""
        scores = [
            self.taste_score,
            self.appearance_score, 
            self.temperature_score,
            self.preparation_time_score,
            self.portion_size_score
        ]
        valid_scores = [s for s in scores if s is not None]
        
        if not valid_scores:
            return None
        return sum(valid_scores) / len(valid_scores)
    
    @property
    def score_breakdown(self) -> dict:
        """Get detailed score breakdown"""
        return {
            "overall": self.overall_score,
            "taste": self.taste_score,
            "appearance": self.appearance_score,
            "temperature": self.temperature_score,
            "preparation_time": self.preparation_time_score,
            "portion_size": self.portion_size_score,
            "average_detailed": self.average_detailed_score
        }