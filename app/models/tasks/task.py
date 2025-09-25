from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from ..restaurants.restaurant import Base

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200))
    description = Column(Text)
    completed = Column(Boolean, default=False)
    due_date = Column(DateTime)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    task_type = Column(String(50))  # 'daily' or 'weekly'
    
    # Relationships
    restaurant = relationship("Restaurant", back_populates="tasks")
