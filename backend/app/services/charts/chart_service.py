from sqlalchemy.orm import Session
from ..models.food_quality.models import FoodQuality
from datetime import datetime, timedelta
from typing import Dict, List

def get_weekly_scores_chart_data(db: Session, restaurant_id: int) -> Dict:
    today = datetime.now()
    current_week_start = today - timedelta(days=today.weekday())
    previous_week_start = current_week_start - timedelta(days=7)
    
    # Current week data
    current_week_records = db.query(FoodQuality).filter(
        FoodQuality.restaurant_id == restaurant_id,
        FoodQuality.created_at >= current_week_start
    ).all()
    
    # Previous week data
    previous_week_records = db.query(FoodQuality).filter(
        FoodQuality.restaurant_id == restaurant_id,
        FoodQuality.created_at >= previous_week_start,
        FoodQuality.created_at < current_week_start
    ).all()
    
    current_avg = sum([r.score for r in current_week_records]) / len(current_week_records) if current_week_records else 0
    previous_avg = sum([r.score for r in previous_week_records]) / len(previous_week_records) if previous_week_records else 0
    
    return {
        "current_week_average": current_avg,
        "previous_week_average": previous_avg,
        "improvement": current_avg - previous_avg,
        "current_week_records": len(current_week_records),
        "previous_week_records": len(previous_week_records)
    }

def get_top_dishes_data(db: Session, restaurant_id: int) -> List[Dict]:
    # Get top 10 dishes by average score
    from sqlalchemy import func
    
    top_dishes = db.query(
        FoodQuality.dish_name,
        func.avg(FoodQuality.score).label('avg_score'),
        func.count(FoodQuality.id).label('count')
    ).filter(
        FoodQuality.restaurant_id == restaurant_id
    ).group_by(FoodQuality.dish_name).order_by(
        func.avg(FoodQuality.score).desc()
    ).limit(10).all()
    
    return [
        {
            "dish_name": dish.dish_name,
            "average_score": float(dish.avg_score),
            "count": dish.count
        }
        for dish in top_dishes
    ]
