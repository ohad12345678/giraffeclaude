from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from ..restaurants.restaurant import Base

class FoodQuality(Base):
    __tablename__ = "food_quality"
    
    id = Column(Integer, primary_key=True, index=True)
    chef_id = Column(Integer, ForeignKey("chefs.id"))
    dish_name = Column(String(100))
    score = Column(Float)
    notes = Column(Text)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    chef = relationship("Chef", back_populates="food_quality_records")
    restaurant = relationship("Restaurant", back_populates="food_quality_records")

class Chef(Base):
    __tablename__ = "chefs"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    restaurant = relationship("Restaurant", back_populates="chefs")
    food_quality_records = relationship("FoodQuality", back_populates="chef")
