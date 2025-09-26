from typing import Dict, List
from sqlalchemy.orm import Session
from ..models.food_quality.models import FoodQuality
from ..models.restaurants.restaurant import Restaurant
import json

class KitchenAIService:
    def __init__(self):
        self.context = {}
    
    def query_database(self, db: Session, question: str) -> Dict:
        question_lower = question.lower()
        
        if "ממוצע" in question or "average" in question_lower:
            return self._handle_average_query(db, question)
        elif "מסעדה" in question or "restaurant" in question_lower:
            return self._handle_restaurant_query(db, question)
        elif "השבוע" in question or "שבוע" in question:
            return self._handle_weekly_query(db, question)
        else:
            return self._handle_general_query(db, question)
    
    def _handle_average_query(self, db: Session, question: str) -> Dict:
        # Calculate overall averages
        from sqlalchemy import func
        
        avg_score = db.query(func.avg(FoodQuality.score)).scalar()
        
        return {
            "answer": f"הציון הממוצע הכללי במערכת הוא {avg_score:.2f}",
            "data": {"average_score": avg_score},
            "query_type": "average"
        }
    
    def _handle_restaurant_query(self, db: Session, question: str) -> Dict:
        restaurants = db.query(Restaurant).all()
        restaurant_data = []
        
        for restaurant in restaurants:
            from sqlalchemy import func
            avg_score = db.query(func.avg(FoodQuality.score)).filter(
                FoodQuality.restaurant_id == restaurant.id
            ).scalar()
            
            restaurant_data.append({
                "name": restaurant.name,
                "average_score": avg_score or 0
            })
        
        return {
            "answer": "נתוני המסעדות:",
            "data": restaurant_data,
            "query_type": "restaurants"
        }
    
    def _handle_weekly_query(self, db: Session, question: str) -> Dict:
        from datetime import datetime, timedelta
        
        today = datetime.now()
        week_start = today - timedelta(days=today.weekday())
        
        weekly_records = db.query(FoodQuality).filter(
            FoodQuality.created_at >= week_start
        ).all()
        
        if weekly_records:
            avg_score = sum([r.score for r in weekly_records]) / len(weekly_records)
            return {
                "answer": f"הציון הממוצע השבוע הוא {avg_score:.2f} ({len(weekly_records)} הערכות)",
                "data": {"weekly_average": avg_score, "count": len(weekly_records)},
                "query_type": "weekly"
            }
        else:
            return {
                "answer": "לא נמצאו נתונים לשבוע הנוכחי",
                "data": {},
                "query_type": "weekly"
            }
    
    def _handle_general_query(self, db: Session, question: str) -> Dict:
        return {
            "answer": "אני יכול לעזור לך עם שאלות על ממוצעי ציונים, נתוני מסעדות, וסטטיסטיקות שבועיות.",
            "data": {},
            "query_type": "general"
        }

ai_service = KitchenAIService()
