from typing import Dict, List, Optional, Any
import json
import asyncio
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from anthropic import Anthropic

from ..models.quality_check import QualityCheck
from ..models.branch import Branch
from ..utils.config import settings

class ClaudeService:
    def __init__(self, db: Session):
        self.db = db
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY) if settings.ANTHROPIC_API_KEY else None
    
    async def analyze_trends(self, 
                           period_days: int = 30, 
                           branches: Optional[List[str]] = None) -> Dict[str, Any]:
        """Analyze quality trends using Claude AI"""
        if not self.client:
            return {"error": "Claude AI not configured"}
        
        # Get data for analysis
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=period_days)
        
        query = self.db.query(QualityCheck).filter(
            QualityCheck.created_at >= start_date,
            QualityCheck.created_at <= end_date
        )
        
        if branches:
            branch_ids = self.db.query(Branch.id).filter(Branch.name.in_(branches)).subquery()
            query = query.filter(QualityCheck.branch_id.in_(branch_ids))
        
        checks = query.all()
        
        if not checks:
            return {"insight": "לא נמצאו נתונים מספיקים לניתוח בתקופה זו."}
        
        # Prepare data for Claude
        analysis_data = self._prepare_analysis_data(checks)
        
        try:
            prompt = self._create_analysis_prompt(analysis_data, period_days)
            
            message = await asyncio.create_task(
                self._call_claude_async(prompt)
            )
            
            return self._parse_claude_response(message)
            
        except Exception as e:
            return {"error": f"שגיאה בניתוח: {str(e)}"}
    
    async def answer_question(self, question: str, context_days: int = 7) -> Dict[str, Any]:
        """Answer specific questions about quality data using Claude"""
        if not self.client:
            return {"error": "Claude AI not configured"}
        
        # Get recent data for context
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=context_days)
        
        checks = self.db.query(QualityCheck).filter(
            QualityCheck.created_at >= start_date
        ).all()
        
        if not checks:
            return {"answer": "לא נמצאו נתונים אחרונים לניתוח."}
        
        try:
            context_data = self._prepare_analysis_data(checks)
            prompt = self._create_question_prompt(question, context_data, context_days)
            
            message = await asyncio.create_task(
                self._call_claude_async(prompt)
            )
            
            return {"answer": message, "context_period": f"{context_days} ימים"}
            
        except Exception as e:
            return {"error": f"שגיאה במענה על השאלה: {str(e)}"}
    
    async def generate_weekly_report(self, week_start: datetime) -> Dict[str, Any]:
        """Generate comprehensive weekly report using Claude"""
        if not self.client:
            return {"error": "Claude AI not configured"}
        
        week_end = week_start + timedelta(days=7)
        
        # Get week's data
        checks = self.db.query(QualityCheck).filter(
            QualityCheck.created_at >= week_start,
            QualityCheck.created_at < week_end
        ).all()
        
        if not checks:
            return {"report": f"לא בוצעו בדיקות איכות בשבוע {week_start.strftime('%d/%m/%Y')} - {week_end.strftime('%d/%m/%Y')}"}
        
        try:
            # Get comparative data (previous week)
            prev_week_start = week_start - timedelta(days=7)
            prev_checks = self.db.query(QualityCheck).filter(
                QualityCheck.created_at >= prev_week_start,
                QualityCheck.created_at < week_start
            ).all()
            
            report_data = {
                "current_week": self._prepare_analysis_data(checks),
                "previous_week": self._prepare_analysis_data(prev_checks) if prev_checks else None,
                "week_period": f"{week_start.strftime('%d/%m/%Y')} - {week_end.strftime('%d/%m/%Y')}"
            }
            
            prompt = self._create_report_prompt(report_data)
            
            message = await asyncio.create_task(
                self._call_claude_async(prompt)
            )
            
            return self._parse_report_response(message, report_data)
            
        except Exception as e:
            return {"error": f"שגיאה ביצירת הדוח: {str(e)}"}
    
    async def detect_anomalies(self, days_back: int = 14) -> Dict[str, Any]:
        """Detect quality anomalies using Claude AI"""
        if not self.client:
            return {"error": "Claude AI not configured"}
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days_back)
        
        checks = self.db.query(QualityCheck).filter(
            QualityCheck.created_at >= start_date
        ).all()
        
        if len(checks) < 10:
            return {"anomalies": [], "message": "נדרשים לפחות 10 רישומים לזיהוי חריגות"}
        
        try:
            anomaly_data = self._prepare_anomaly_data(checks)
            prompt = self._create_anomaly_prompt(anomaly_data, days_back)
            
            message = await asyncio.create_task(
                self._call_claude_async(prompt)
            )
            
            return self._parse_anomaly_response(message)
            
        except Exception as e:
            return {"error": f"שגיאה בזיהוי חריגות: {str(e)}"}
    
    def _prepare_analysis_data(self, checks: List[QualityCheck]) -> Dict[str, Any]:
        """Prepare quality check data for Claude analysis"""
        if not checks:
            return {}
        
        # Group by branch
        branch_data = {}
        chef_performance = {}
        dish_performance = {}
        
        for check in checks:
            branch_name = check.branch.name if check.branch else "לא ידוע"
            
            # Branch statistics
            if branch_name not in branch_data:
                branch_data[branch_name] = {
                    "checks": [],
                    "total_score": 0,
                    "count": 0,
                    "low_scores": 0
                }
            
            branch_data[branch_name]["checks"].append({
                "score": check.overall_score,
                "chef": check.chef_name,
                "dish": check.dish_name,
                "date": check.created_at.strftime("%Y-%m-%d"),
                "notes": check.notes
            })
            branch_data[branch_name]["total_score"] += check.overall_score
            branch_data[branch_name]["count"] += 1
            if check.overall_score < settings.ALERT_THRESHOLD:
                branch_data[branch_name]["low_scores"] += 1
            
            # Chef performance
            chef_key = f"{check.chef_name}@{branch_name}"
            if chef_key not in chef_performance:
                chef_performance[chef_key] = {
                    "name": check.chef_name,
                    "branch": branch_name,
                    "scores": [],
                    "dishes": set()
                }
            chef_performance[chef_key]["scores"].append(check.overall_score)
            chef_performance[chef_key]["dishes"].add(check.dish_name)
            
            # Dish performance
            if check.dish_name not in dish_performance:
                dish_performance[check.dish_name] = {
                    "scores": [],
                    "branches": set(),
                    "chefs": set()
                }
            dish_performance[check.dish_name]["scores"].append(check.overall_score)
            dish_performance[check.dish_name]["branches"].add(branch_name)
            dish_performance[check.dish_name]["chefs"].add(check.chef_name)
        
        # Calculate averages
        for branch in branch_data.values():
            branch["average_score"] = branch["total_score"] / branch["count"]
            branch["low_score_percentage"] = (branch["low_scores"] / branch["count"]) * 100
        
        # Convert sets to lists for JSON serialization
        for dish in dish_performance.values():
            dish["branches"] = list(dish["branches"])
            dish["chefs"] = list(dish["chefs"])
            dish["average_score"] = sum(dish["scores"]) / len(dish["scores"])
        
        for chef in chef_performance.values():
            chef["dishes"] = list(chef["dishes"])
            chef["average_score"] = sum(chef["scores"]) / len(chef["scores"])
        
        return {
            "total_checks": len(checks),
            "overall_average": sum(check.overall_score for check in checks) / len(checks),
            "period": {
                "start": min(check.created_at for check in checks).strftime("%Y-%m-%d"),
                "end": max(check.created_at for check in checks).strftime("%Y-%m-%d")
            },
            "branches": branch_data,
            "chefs": {k: v for k, v in chef_performance.items()},
            "dishes": dish_performance,
            "low_score_threshold": settings.ALERT_THRESHOLD
        }
    
    def _prepare_anomaly_data(self, checks: List[QualityCheck]) -> Dict[str, Any]:
        """Prepare data for anomaly detection"""
        # Calculate rolling averages and identify sudden changes
        checks_by_date = {}
        for check in checks:
            date_key = check.created_at.strftime("%Y-%m-%d")
            if date_key not in checks_by_date:
                checks_by_date[date_key] = []
            checks_by_date[date_key].append(check)
        
        daily_averages = {}
        for date, day_checks in checks_by_date.items():
            daily_averages[date] = sum(c.overall_score for c in day_checks) / len(day_checks)
        
        return {
            "daily_averages": daily_averages,
            "total_checks": len(checks),
            "individual_checks": [
                {
                    "id": check.id,
                    "score": check.overall_score,
                    "branch": check.branch.name if check.branch else "Unknown",
                    "chef": check.chef_name,
                    "dish": check.dish_name,
                    "date": check.created_at.strftime("%Y-%m-%d %H:%M"),
                    "is_low": check.overall_score < settings.ALERT_THRESHOLD
                }
                for check in checks
            ]
        }
    
    def _create_analysis_prompt(self, data: Dict[str, Any], period_days: int) -> str:
        """Create prompt for trend analysis"""
        return f"""
אתה מנתח איכות מזון מומחה ברשת מסעדות ג'ירף. נתח את נתוני בדיקות האיכות של {period_days} הימים האחרונים ותן תובנות בעברית.

נתונים לניתוח:
{json.dumps(data, ensure_ascii=False, indent=2)}

אנא ספק ניתוח מקיף הכולל:
1. **מצב כללי**: הערכה של הביצועים הכלליים
2. **מגמות חיוביות**: שיפורים שזוהו
3. **אזורי דאגה**: בעיות הדורשות תשומת לב
4. **השוואת סניפים**: ביצועים יחסיים
5. **המלצות פעולה**: צעדים קונקרטיים לשיפור
6. **סניפים בפוקוס**: סניפים הדורשים תשומת לב מיוחדת

השב בפורמט JSON:
{{
  "summary": "סיכום כללי של המצב",
  "positive_trends": ["מגמה חיובית 1", "מגמה חיובית 2"],
  "concerns": ["דאגה 1", "דאגה 2"],
  "branch_insights": {{"שם_סניף": "תובנה על הסניף"}},
  "recommendations": ["המלצה 1", "המלצה 2"],
  "priority_branches": [
    {{"name": "שם סניף", "reason": "סיבה לתשומת לב", "suggested_actions": ["פעולה 1", "פעולה 2"]}}
  ]
}}
"""
    
    def _create_question_prompt(self, question: str, context_data: Dict[str, Any], context_days: int) -> str:
        """Create prompt for answering specific questions"""
        return f"""
אתה מנתח איכות מזון מומחה ברשת מסעדות ג'ירף. ענה על השאלה הבאה על בסיס נתוני {context_days} הימים האחרונים:

שאלה: {question}

נתוני הקשר:
{json.dumps(context_data, ensure_ascii=False, indent=2)}

אנא ענה בעברית בצורה ברורה ומקצועית, תוך התבססות על הנתונים הקיימים. אם הנתונים לא מספיקים, ציין זאת במפורש.
"""
    
    def _create_report_prompt(self, report_data: Dict[str, Any]) -> str:
        """Create prompt for weekly report generation"""
        return f"""
אתה מנתח איכות מזון מומחה ברשת מסעדות ג'ירף. צור דוח שבועי מקיף בעברית עבור השבוע {report_data['week_period']}.

נתוני השבוע:
{json.dumps(report_data, ensure_ascii=False, indent=2)}

צור דוח מקצועי הכולל:
1. **סיכום מנהלים**: תמצית של 2-3 משפטים למנהלים
2. **נתונים עיקריים**: סטטיסטיקות חשובות
3. **ביצועי סניפים**: דירוג וניתוח ביצועים
4. **שיפורים ובעיות**: מה השתפר ומה דורש תשומת לב
5. **המלצות השבוע**: פעולות קונקרטיות
6. **מוקד השבוע הבא**: על מה להתמקד

השב בפורמט JSON מובנה עם כל הסעיפים לעיל.
"""
    
    def _create_anomaly_prompt(self, anomaly_data: Dict[str, Any], days_back: int) -> str:
        """Create prompt for anomaly detection"""
        return f"""
אתה מנתח איכות מזון מומחה ברשת מסעדות ג'ירף. זהה חריגות וביצועים חריגים בנתוני {days_back} הימים האחרונים.

נתונים לבדיקה:
{json.dumps(anomaly_data, ensure_ascii=False, indent=2)}

זהה וחלק חריגות כגון:
- ירידות חדות בציונים
- ביצועים חריגים של שפים או סניפים
- דפוסים חשודים
- שיפורים או הדרדרויות מהירות

השב בפורמט JSON:
{{
  "anomalies_found": מספר החריגות,
  "critical_issues": ["בעיה קריטית 1"],
  "performance_anomalies": ["חריגת ביצועים 1"],
  "recommendations": ["המלצה לטיפול 1"],
  "monitoring_suggestions": ["הצעה למעקב 1"]
}}
"""
    
    async def _call_claude_async(self, prompt: str) -> str:
        """Make async call to Claude API"""
        loop = asyncio.get_event_loop()
        
        def sync_call():
            try:
                message = self.client.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=2000,
                    temperature=0.3,
                    messages=[{"role": "user", "content": prompt}]
                )
                return message.content[0].text
            except Exception as e:
                return f"שגיאה בקריאה ל-Claude: {str(e)}"
        
        return await loop.run_in_executor(None, sync_call)
    
    def _parse_claude_response(self, response: str) -> Dict[str, Any]:
        """Parse Claude response into structured data"""
        try:
            # Try to extract JSON from response
            if response.startswith('{'):
                return json.loads(response)
            else:
                # If not JSON, return as text insight
                return {"insight": response}
        except json.JSONDecodeError:
            return {"insight": response}
    
    def _parse_report_response(self, response: str, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Claude report response"""
        parsed = self._parse_claude_response(response)
        parsed["generated_at"] = datetime.utcnow().isoformat()
        parsed["period"] = report_data["week_period"]
        return parsed
    
    def _parse_anomaly_response(self, response: str) -> Dict[str, Any]:
        """Parse Claude anomaly detection response"""
        parsed = self._parse_claude_response(response)
        parsed["detected_at"] = datetime.utcnow().isoformat()
        return parsed
