# config.py
import os
from typing import List, Dict
import streamlit as st

class Config:
    # Database
    DB_PATH = "food_quality.db"
    
    # Branches and Staff
    BRANCHES: List[str] = [
        "חיפה", "ראשל״צ", "רמה״ח", "נס ציונה", "לנדמרק", 
        "פתח תקווה", "הרצליה", "סביון"
    ]

    DISHES: List[str] = [
        "פאד תאי", "מלאזית", "פיליפינית", "אפגנית",
        "קארי דלעת", "סצ'ואן", "ביף רייס",
        "אורז מטוגן", "מאקי סלמון", "מאקי טונה",
        "ספייסי סלמון", "נודלס ילדים",
        "סלט תאילנדי", "סלט בריאות", "סלט דג לבן", 
        "אגרול", "גיוזה", "וון",
    ]

    CHEFS_BY_BRANCH: Dict[str, List[str]] = {
        "פתח תקווה": ["שן", "זאנג", "דאי", "לי", "ין", "יו"],
        "הרצליה": ["יון", "שיגווה", "באו באו", "האו", "טו", "זאנג", "טאנג", "צונג"],
        "נס ציונה": ["לי פנג", "זאנג", "צ'ו", "פנג"],
        "סביון": ["בין בין", "וואנג", "וו", "סונג", "ג'או"],
        "ראשל״צ": ["ג'או", "זאנג", "צ'ה", "ליו", "מא", "רן"],
        "חיפה": ["סונג", "לי", "ליו", "ג'או"],
        "רמה״ח": ["ין", "סי", "ליו", "הואן", "פרנק", "זאנג", "זאו לי"],
        "לנדמרק": [
            "יו", "מא", "וואנג הואנבין", "וואנג ג'ינלאי", "ג'או", "אוליבר", 
            "זאנג", "בי", "יאנג זימינג", "יאנג רונגשטן", "דונג", "וואנג פוקוואן"
        ],
    }
    
    # Quality Categories
    QUALITY_CATEGORIES = {
        "טעם": ["מתוק מדי", "מלוח מדי", "חמוץ מדי", "חד מדי", "פשוט", "מושלם"],
        "מראה": ["לא אטרקטיביי", "רגיל", "יפה", "מושלם"],
        "טמפרטורה": ["קר", "פושר", "חם", "חם מדי"],
        "זמן הכנה": ["איטי מדי", "רגיל", "מהיר"],
        "כמות": ["קטן מדי", "מתאים", "גדול מדי"]
    }
    
    # Thresholds
    MIN_CHEF_TOP_M = 5
    MIN_CHEF_WEEK_M = 2
    MIN_DISH_WEEK_M = 2
    
    # Colors
    COLORS = {
        "primary": "#10b981",
        "amber": "#FFE07A",
        "tile_green": "#d7fde7",
        "green_50": "#ecfdf5",
        "text": "#0d0f12",
        "border": "#e7ebf0"
    }
    
    # API Keys
    @staticmethod
    def get_openai_key() -> str:
        return st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY", "")
    
    @staticmethod
    def get_anthropic_key() -> str:
        return st.secrets.get("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_API_KEY", "")
    
    @staticmethod
    def get_google_sheet_id() -> str:
        sid = st.secrets.get("GOOGLE_SHEET_ID") or os.getenv("GOOGLE_SHEET_ID")
        if sid: 
            return sid
        url = st.secrets.get("GOOGLE_SHEET_URL") or os.getenv("GOOGLE_SHEET_URL")
        if url and "/spreadsheets/d/" in url:
            try: 
                return url.split("/spreadsheets/d/")[1].split("/")[0]
            except: 
                return ""
        return ""
    
    @staticmethod
    def get_service_account_info() -> dict:
        raw = (st.secrets.get("GOOGLE_SERVICE_ACCOUNT_JSON")
               or os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
               or st.secrets.get("google_service_account")
               or os.getenv("GOOGLE_SERVICE_ACCOUNT"))
        if not raw: 
            return {}
        if isinstance(raw, dict): 
            return raw
        try: 
            import json
            return json.loads(raw)
        except: 
            return {}

    # Google Sheets
    SCOPES = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
