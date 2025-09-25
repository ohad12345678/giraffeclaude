from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

DATABASE_URL = "sqlite:///./kitchen_management.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Restaurant(Base):
    __tablename__ = "restaurants"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True)
    location = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True)
    hashed_password = Column(String(200))
    role = Column(String(50))
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Chef(Base):
    __tablename__ = "chefs"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

class FoodQuality(Base):
    __tablename__ = "food_quality"
    
    id = Column(Integer, primary_key=True, index=True)
    chef_name = Column(String(100))
    dish_name = Column(String(100))
    score = Column(Float)
    notes = Column(Text)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200))
    description = Column(Text)
    due_date = Column(DateTime)
    task_type = Column(String(50))
    completed = Column(Boolean, default=False)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    Base.metadata.create_all(bind=engine)
