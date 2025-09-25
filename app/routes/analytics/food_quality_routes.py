from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database.database import get_db
from ..models.food_quality.models import FoodQuality, Chef
from datetime import datetime, timedelta

router = APIRouter(prefix="/food-quality", tags=["food-quality"])

@router.get("/")
async def get_food_quality_records(restaurant_id: int = None, db: Session = Depends(get_db)):
    query = db.query(FoodQuality)
    if restaurant_id:
        query = query.filter(FoodQuality.restaurant_id == restaurant_id)
    records = query.all()
    return records

@router.post("/")
async def create_food_quality_record(
    chef_id: int,
    dish_name: str,
    score: float,
    notes: str = None,
    restaurant_id: int = None,
    db: Session = Depends(get_db)
):
    record = FoodQuality(
        chef_id=chef_id,
        dish_name=dish_name,
        score=score,
        notes=notes,
        restaurant_id=restaurant_id
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record

@router.get("/weekly-comparison/{restaurant_id}")
async def get_weekly_comparison(restaurant_id: int, db: Session = Depends(get_db)):
    # Get current week and previous week averages
    today = datetime.now()
    current_week_start = today - timedelta(days=today.weekday())
    previous_week_start = current_week_start - timedelta(days=7)
    
    # TODO: Implement weekly comparison logic
    return {"message": "Weekly comparison for restaurant {}".format(restaurant_id)}
