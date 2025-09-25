from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    RESTAURANT = "restaurant"
    HEADQUARTERS = "headquarters"

class TaskType(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"

# Auth Models
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    role: UserRole
    restaurant_id: Optional[int] = None

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserInDB(BaseModel):
    id: int
    username: str
    role: UserRole
    restaurant_id: Optional[int]
    is_active: bool

# Restaurant Models
class Restaurant(BaseModel):
    id: int
    name: str
    location: str

class RestaurantCreate(BaseModel):
    name: str
    location: str

# Chef Models
class ChefBase(BaseModel):
    name: str
    restaurant_id: int

class ChefCreate(ChefBase):
    pass

class Chef(ChefBase):
    id: int
    created_at: datetime

# Food Quality Models
class FoodQualityBase(BaseModel):
    chef_name: str
    dish_name: str
    score: float = Field(..., ge=1, le=10, description="ציון בין 1 ל-10")
    notes: Optional[str] = None
    restaurant_id: int

class FoodQualityCreate(FoodQualityBase):
    pass

class FoodQuality(FoodQualityBase):
    id: int
    created_at: datetime

# Task Models
class TaskBase(BaseModel):
    title: str
    description: str
    due_date: datetime
    task_type: TaskType
    restaurant_id: int

class TaskCreate(TaskBase):
    pass

class Task(TaskBase):
    id: int
    completed: bool = False
    created_at: datetime

class TaskUpdate(BaseModel):
    completed: Optional[bool] = None
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[datetime] = None

# Response Models
class APIResponse(BaseModel):
    message: str
    data: Optional[dict] = None
