from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database.database import get_db
from ..services.ai.ai_service import ai_service
from pydantic import BaseModel

router = APIRouter(prefix="/ai", tags=["ai"])

class QueryRequest(BaseModel):
    question: str
    restaurant_id: int = None

@router.post("/query")
async def ai_query(request: QueryRequest, db: Session = Depends(get_db)):
    try:
        result = ai_service.query_database(db, request.question)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI query failed: {str(e)}")

@router.get("/suggestions/{restaurant_id}")
async def get_suggestions(restaurant_id: int, db: Session = Depends(get_db)):
    # Generate automatic suggestions based on data
    suggestions = [
        "מה הציון הממוצע השבוע?",
        "איך המסעדה שלי מתאימה ביחס לאחרות?",
        "מה המנה עם הציון הגבוה ביותר?",
        "האם יש שיפור השבוע?"
    ]
    return {"suggestions": suggestions}
