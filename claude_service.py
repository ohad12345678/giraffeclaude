# claude_service.py
import pandas as pd
import streamlit as st
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import json
from config import Config

class ClaudeAnalysisService:
    def __init__(self):
        self.api_key = Config.get_anthropic_key()
        self.client = None
        if self.api_key:
            try:
                import anthropic
                self.client = anthropic.Anthropic(api_key=self.api_key)
            except ImportError:
                st.error("חסרה הספריה anthropic. התקן עם: pip install anthropic")
    
    def is_available(self) -> bool:
        """בדיקה אם Claude זמין"""
        return self.client is not None and self.api_key
    
    def prepare_data_summary(self, df: pd.DataFrame, max_rows: int = 500) -> str:
        """הכנת סיכום הנתונים לשליחה ל-Claude"""
        if df.empty:
            return "אין נתונים זמינים לניתוח"
        
        # הגבלת כמות הנתונים
        df_limited = df.head(max_rows) if len(df) > max_rows else df.copy()
        
        # סיכום כללי
        summary = {
            "total_checks": len(df),
            "date_range": {
                "start": df['created_at'].min().strftime("%Y-%m-%d") if not df.empty else None,
                "end": df['created_at'].max().strftime("%Y-%m-%d") if not df.empty else None
            },
            "branches": df['branch'].unique().tolist(),
            "avg_overall_score": float(df['overall_score'].mean()) if 'overall_score' in df.columns else None,
            "score_distribution": df['overall_score'].value_counts().to_dict() if 'overall_score' in df.columns else {}
        }
        
        # נתונים אחרונים (שבוע)
        week_ago = pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=7)
        recent_df = df[df['created_at'] >= week_ago] if not df.empty else pd.DataFrame()
        
        recent_summary = {}
        if not recent_df.empty:
            recent_summary = {
                "checks_last_week": len(recent_df),
                "avg_score_last_week": float(recent_df['overall_score'].mean()),
                "branches_active": recent_df['branch'].nunique(),
                "dishes_checked": recent_df['dish_name'].nunique(),
                "lowest_scoring_dishes": recent_df.groupby('dish_name')['overall_score'].mean().nsmallest(3).to_dict(),
                "highest_scoring_dishes": recent_df.groupby('dish_name')['overall_score'].mean().nlargest(3).to_dict()
            }
        
        # הכנת CSV מקוצר
        csv_data = df_limited[['branch', 'chef_name', 'dish_name', 'overall_score', 'created_at', 'notes']].to_csv(index=False)
        
        return f"""
נתוני איכות מזון - רשת ג'ירף:

סיכום כללי:
{json.dumps(summary, indent=2, ensure_ascii=False)}

נתונים אחרונים (7 ימים):
{json.dumps(recent_summary, indent=2, ensure_ascii=False)}

נתונים גולמיים (עד {max_rows} רשומות):
{csv_data}
"""
    
    def analyze_quality_trends(self, df: pd.DataFrame) -> str:
        """ניתוח מגמות איכות"""
        if not self.is_available():
            return "שירות Claude אינו זמין. נא לבדוק את מפתח ה-API."
        
        data_summary = self.prepare_data_summary(df)
        
        prompt = f"""
אתה אנליסט איכות מזון מומחה לרשת מסעדות ג'ירף. 
עליך לנתח את הנתונים המצורפים ולספק תובנות מקצועיות בעברית.

דרישות לניתוח:
1. זהה מגמות בציוני האיכות
2. מצא חריגות ובעיות פוטנציאליות
3. ספק המלצות קונקרטיות לשיפור
4. התמקד בשיפור חוויית הלקוח
5. זהה הזדמנויות לייעול תהליכים

הנתונים:
{data_summary}

אנא ספק ניתוח מקיף כולל:
- מגמות ראשיות
- נקודות חוזק וחולשה
- המלצות מעשיות לשיפור
- זיהוי סניפים או מנות הזקוקים לתשומת לב מיוחדת
"""

        try:
            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=2000,
                temperature=0.3,
                messages=[
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ]
            )
            return response.content[0].text
        except Exception as e:
            return f"שגיאה בקריאה ל-Claude: {str(e)}"
    
    def answer_custom_question(self, df: pd.DataFrame, question: str) -> str:
        """מענה לשאלה מותאמת"""
        if not self.is_available():
            return "שירות Claude אינו זמין. נא לבדוק את מפתח ה-API."
        
        data_summary = self.prepare_data_summary(df)
        
        prompt = f"""
אתה אנליסט נתוני איכות מזון לרשת ג'ירף. 
ענה על השאלה הבאה בעברית בהתבסס על הנתונים המצורפים.

שאלה: {question}

נתונים:
{data_summary}

אנא ספק תשובה מקיפה ומנומקת עם דוגמאות ספציפיות מהנתונים.
"""

        try:
            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1500,
                temperature=0.2,
                messages=[
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ]
            )
            return response.content[0].text
        except Exception as e:
            return f"שגיאה בקריאה ל-Claude: {str(e)}"
    
    def generate_weekly_report(self, df: pd.DataFrame, branch: Optional[str] = None) -> str:
        """יצירת דוח שבועי"""
        if not self.is_available():
            return "שירות Claude אינו זמין."
        
        # סינון נתונים לשבוע האחרון
        week_ago = pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=7)
        weekly_df = df[df['created_at'] >= week_ago].copy()
        
        if branch:
            weekly_df = weekly_df[weekly_df['branch'] == branch]
        
        if weekly_df.empty:
            return "אין מספיק נתונים ליצירת דוח ש
