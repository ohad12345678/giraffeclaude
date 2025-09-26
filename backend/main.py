from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from models import *
from database import get_db, create_tables
import database as db_models
from auth import *

app = FastAPI(title="Kitchen Management API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database tables and initial data on startup
@app.on_event("startup")
async def startup_event():
    create_tables()
    db = next(get_db())
    
    # Add initial restaurants if empty
    if db.query(db_models.Restaurant).count() == 0:
        initial_restaurants = [
            db_models.Restaurant(id=1, name="חיפה", location="חיפה"),
            db_models.Restaurant(id=2, name="הרצליה", location="הרצליה"),
            db_models.Restaurant(id=3, name="פתח תקווה", location="פתח תקווה"),
            db_models.Restaurant(id=4, name="נס ציונה", location="נס ציונה"),
            db_models.Restaurant(id=5, name="רמה\"ח", location="רמת החיל"),
            db_models.Restaurant(id=6, name="סביון", location="סביון"),
            db_models.Restaurant(id=7, name="מודיעין", location="מודיעין"),
            db_models.Restaurant(id=8, name="לנדמק", location="לנדמק"),
            db_models.Restaurant(id=9, name="ראשלצ", location="ראש לציון")
        ]
        db.add_all(initial_restaurants)
        db.commit()
    
    # Add initial users if empty
    if db.query(db_models.User).count() == 0:
        initial_users = [
            # משתמש מטה
            db_models.User(
                username="headquarters",
                hashed_password=get_password_hash("admin123"),
                role="headquarters",
                restaurant_id=None
            ),
            # משתמשי מסעדות לדוגמה
            db_models.User(
                username="haifa_user",
                hashed_password=get_password_hash("haifa123"),
                role="restaurant",
                restaurant_id=1
            ),
            db_models.User(
                username="herzliya_user", 
                hashed_password=get_password_hash("herzliya123"),
                role="restaurant",
                restaurant_id=2
            )
        ]
        db.add_all(initial_users)
        db.commit()

# Auth endpoints
@app.post("/auth/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="שם משתמש או סיסמה שגויים",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/auth/register", response_model=UserInDB)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = get_user_by_username(db, user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="שם המשתמש כבר קיים")
    
    hashed_password = get_password_hash(user.password)
    db_user = db_models.User(
        username=user.username,
        hashed_password=hashed_password,
        role=user.role,
        restaurant_id=user.restaurant_id
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return UserInDB(
        id=db_user.id,
        username=db_user.username,
        role=UserRole(db_user.role),
        restaurant_id=db_user.restaurant_id,
        is_active=db_user.is_active
    )

@app.get("/auth/me", response_model=UserInDB)
async def read_users_me(current_user: db_models.User = Depends(get_current_active_user)):
    return UserInDB(
        id=current_user.id,
        username=current_user.username,
        role=UserRole(current_user.role),
        restaurant_id=current_user.restaurant_id,
        is_active=current_user.is_active
    )

# Protected Restaurant endpoints
@app.get("/restaurants", response_model=List[Restaurant])
async def get_restaurants(current_user: db_models.User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    if current_user.role == "headquarters":
        restaurants = db.query(db_models.Restaurant).all()
    else:
        restaurants = db.query(db_models.Restaurant).filter(db_models.Restaurant.id == current_user.restaurant_id).all()
    return restaurants

@app.get("/restaurants/{restaurant_id}", response_model=Restaurant)
async def get_restaurant(restaurant_id: int, current_user: db_models.User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    if not check_restaurant_access(current_user, restaurant_id):
        raise HTTPException(status_code=403, detail="אין הרשאה לגשת למסעדה זו")
    
    restaurant = db.query(db_models.Restaurant).filter(db_models.Restaurant.id == restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="מסעדה לא נמצאה")
    return restaurant

# Protected Food Quality endpoints
@app.get("/food-quality/", response_model=List[FoodQuality])
async def get_food_quality(restaurant_id: Optional[int] = None, current_user: db_models.User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    query = db.query(db_models.FoodQuality)
    
    if current_user.role == "restaurant":
        # משתמש מסעדה רואה רק את המסעדה שלו
        query = query.filter(db_models.FoodQuality.restaurant_id == current_user.restaurant_id)
    elif restaurant_id:
        # משתמש מטה יכול לבחור מסעדה ספציפית
        query = query.filter(db_models.FoodQuality.restaurant_id == restaurant_id)
    
    return query.all()

@app.post("/food-quality/", response_model=FoodQuality)
async def create_food_quality(food_quality: FoodQualityCreate, current_user: db_models.User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    # וודא שמשתמש המסעדה יכול להוסיף רק למסעדה שלו
    if current_user.role == "restaurant" and food_quality.restaurant_id != current_user.restaurant_id:
        raise HTTPException(status_code=403, detail="אין הרשאה להוסיף נתונים למסעדה זו")
    
    db_food_quality = db_models.FoodQuality(
        chef_name=food_quality.chef_name,
        dish_name=food_quality.dish_name,
        score=food_quality.score,
        notes=food_quality.notes,
        restaurant_id=food_quality.restaurant_id
    )
    db.add(db_food_quality)
    db.commit()
    db.refresh(db_food_quality)
    return db_food_quality

@app.get("/", response_model=APIResponse)
async def root():
    return APIResponse(message="Kitchen Management API - עם מערכת אימות!", data={"version": "1.0.0"})

@app.get("/health", response_model=APIResponse)
async def health_check():
    return APIResponse(message="המערכת תקינה", data={"status": "healthy", "database": "SQLite", "auth": "JWT"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
