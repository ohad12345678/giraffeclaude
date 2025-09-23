from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from ..utils.database import Base

class Category(Base):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    name_en = Column(String(100), nullable=True)  # English name
    description = Column(Text, nullable=True)
    
    # Category type (dish_category, quality_metric, etc.)
    category_type = Column(String(50), nullable=False, default="dish_category")
    
    # Hierarchy support
    parent_id = Column(Integer, nullable=True)
    order_index = Column(Integer, default=0)  # For sorting
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Additional settings
    settings = Column(JSON, nullable=True, default={})
    
    # Timestamps  
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<Category(name='{self.name}', type='{self.category_type}')>"
