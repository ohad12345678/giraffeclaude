from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database.database import get_db
from ..models.restaurants.restaurant import Restaurant

router = APIRouter(prefix="/restaurants", tags=["restaurants"])

@router.get("/", response_model=List[dict])
async def get_restaurants(db: Session = Depends(get_db)):
    restaurants = db.query(Restaurant).all()
    return [{"id": r.id, "name": r.name, "location": r.location} for r in restaurants]

@router.get("/{restaurant_id}")
async def get_restaurant(restaurant_id: int, db: Session = Depends(get_db)):
    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="מסעדה לא נמצאה")
    return {"id": restaurant.id, "name": restaurant.name, "location": restaurant.location}
