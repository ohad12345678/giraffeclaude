from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from ..restaurants.restaurant import Base

class ChefTraining(Base):
    __tablename__ = "chef_training"
    
    id = Column(Integer, primary_key=True, index=True)
    chef_id = Column(Integer, ForeignKey("chefs.id"))
    training_title = Column(String(200))
    description = Column(Text)
    completed = Column(Boolean, default=False)
    completed_date = Column(DateTime)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    chef = relationship("Chef")
    restaurant = relationship("Restaurant")
