from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from ..database.database import get_db
from ..models.food_quality.models import FoodQuality
from datetime import datetime, timedelta
import json

router = APIRouter(prefix="/reports", tags=["reports"])

@router.get("/weekly/{restaurant_id}")
async def get_weekly_report(restaurant_id: int = None, db: Session = Depends(get_db)):
    # Generate weekly report data
    weeks_data = []
    
    for i in range(4):  # Last 4 weeks
        week_start = datetime.now() - timedelta(weeks=i+1)
        week_end = week_start + timedelta(days=7)
        
        week_records = db.query(FoodQuality).filter(
            FoodQuality.created_at >= week_start,
            FoodQuality.created_at < week_end
        )
        
        if restaurant_id:
            week_records = week_records.filter(FoodQuality.restaurant_id == restaurant_id)
        
        records = week_records.all()
        
        if records:
            avg_score = sum(r.score for r in records) / len(records)
            # Get most popular dish
            dish_counts = {}
            for record in records:
                dish_counts[record.dish_name] = dish_counts.get(record.dish_name, 0) + 1
            top_dish = max(dish_counts.keys(), key=lambda x: dish_counts[x]) if dish_counts else "N/A"
            
            weeks_data.append({
                "period": f"שבוע {i+1}",
                "averageScore": avg_score,
                "totalRecords": len(records),
                "topDish": top_dish,
                "improvementTrend": 0  # Calculate based on previous week
            })
    
    # Calculate improvement trends
    for i in range(1, len(weeks_data)):
        if weeks_data[i]["averageScore"] > 0:
            weeks_data[i-1]["improvementTrend"] = (
                (weeks_data[i-1]["averageScore"] - weeks_data[i]["averageScore"]) / weeks_data[i]["averageScore"] * 100
            )
    
    return weeks_data

@router.get("/monthly/{restaurant_id}")
async def get_monthly_report(restaurant_id: int = None, db: Session = Depends(get_db)):
    # Similar logic for monthly data
    return [{"period": "חודש זה", "averageScore": 7.5, "totalRecords": 100, "topDish": "פסטה", "improvementTrend": 2.5}]

@router.get("/export/weekly/pdf/{restaurant_id}")
async def export_weekly_pdf(restaurant_id: int = None):
    # Generate PDF report (placeholder)
    return Response(
        content="PDF report would be generated here",
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=weekly_report.pdf"}
    )
