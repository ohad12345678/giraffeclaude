# utils/helpers.py
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
import re

def format_score(score: float, include_emoji: bool = True) -> str:
    """עיצוב ציון עם אמוג'י"""
    if pd.isna(score):
        return "—"
    
    emoji = ""
    if include_emoji:
        if score >= 9:
            emoji = "🟢"
        elif score >= 7:
            emoji = "🟡"
        elif score >= 5:
            emoji = "🟠"
        else:
            emoji = "🔴"
    
    return f"{emoji} {score:.1f}" if emoji else f"{score:.1f}"

def score_to_emoji(score: int) -> str:
    """המרת ציון לאמוג'י"""
    if score >= 9:
        return "🟢"
    elif score >= 7:
        return "🟡"
    elif score >= 5:
        return "🟠"
    else:
        return "🔴"

def score_to_text(score: int) -> str:
    """המרת ציון לטקסט"""
    if score >= 9:
        return "מצוין"
    elif score >= 7:
        return "טוב"
    elif score >= 5:
        return "סביר"
    else:
        return "חלש"

def calculate_trend(current: float, previous: float) -> Dict[str, Any]:
    """חישוב מגמה בין שני ערכים"""
    if pd.isna(current) or pd.isna(previous):
        return {"direction": "stable", "change": 0, "percentage": 0}
    
    change = current - previous
    percentage = (change / previous * 100) if previous != 0 else 0
    
    if abs(change) < 0.1:
        direction = "stable"
        icon = "➡️"
    elif change > 0:
        direction = "up"
        icon = "⬆️"
    else:
        direction = "down"
        icon = "⬇️"
    
    return {
        "direction": direction,
        "change": change,
        "percentage": percentage,
        "icon": icon,
        "text": f"{icon} {change:+.1f} ({percentage:+.1f}%)"
    }

def format_date_hebrew(date: datetime) -> str:
    """עיצוב תאריך בעברית"""
    if pd.isna(date):
        return "—"
    
    hebrew_days = {
        0: "שני", 1: "שלישי", 2: "רביעי", 3: "חמישי",
        4: "שישי", 5: "שבת", 6: "ראשון"
    }
    
    hebrew_months = {
        1: "ינואר", 2: "פברואר", 3: "מרץ", 4: "אפריל",
        5: "מאי", 6: "יוני", 7: "יולי", 8: "אוגוסט",
        9: "ספטמבר", 10: "אוקטובר", 11: "נובמבר", 12: "דצמבר"
    }
    
    day_name = hebrew_days[date.weekday()]
    month_name = hebrew_months[date.month]
    
    return f"{day_name}, {date.day} ב{month_name} {date.year}"

def safe_divide(numerator: float, denominator: float, default: float = 0) -> float:
    """חלוקה בטוחה"""
    if denominator == 0 or pd.isna(denominator) or pd.isna(numerator):
        return default
    return numerator / denominator

def filter_dataframe_by_date(df: pd.DataFrame, days: int, date_column: str = 'created_at') -> pd.DataFrame:
    """סינון DataFrame לפי מספר ימים אחורה"""
    if df.empty:
        return df
    
    cutoff_date = datetime.now() - timedelta(days=days)
    return df[df[date_column] >= cutoff_date].copy()

def get_week_range(date: datetime) -> Tuple[datetime, datetime]:
    """קבלת טווח השבוע (ראשון-שבת)"""
    # בישראל השבוע מתחיל ביום ראשון
    days_since_sunday = (date.weekday() + 1) % 7
    week_start = date - timedelta(days=days_since_sunday)
    week_end = week_start + timedelta(days=6)
    
    return week_start.replace(hour=0, minute=0, second=0, microsecond=0), \
           week_end.replace(hour=23, minute=59, second=59, microsecond=999999)

def create_metric_card(title: str, value: Any, delta: Optional[str] = None, 
                      help_text: Optional[str] = None) -> str:
    """יצירת כרטיס מטריקה בHTML"""
    delta_html = f"<div class='metric-delta'>{delta}</div>" if delta else ""
    help_html = f"<div class='metric-help'>{help_text}</div>" if help_text else ""
    
    return f"""
    <div class="metric-card">
        <div class="metric-title">{title}</div>
        <div class="metric-value">{value}</div>
        {delta_html}
        {help_html}
    </div>
    """

def validate_email(email: str) -> bool:
    """אימות כתובת אימייל"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def sanitize_filename(filename: str) -> str:
    """ניקוי שם קובץ מתווים לא חוקיים"""
    # הסרת תווים לא חוקיים
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # הסרת רווחים כפולים
    sanitized = re.sub(r'\s+', ' ', sanitized).strip()
    # הגבלת אורך
    if len(sanitized) > 200:
        sanitized = sanitized[:200]
    
    return sanitized

def chunks(lst: List, n: int) -> List[List]:
    """חלוקת רשימה לחלקים"""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def format_number_hebrew(number: float, decimal_places: int = 1) -> str:
    """עיצוב מספר בעברית"""
    if pd.isna(number):
        return "—"
    
    formatted = f"{number:.{decimal_places}f}"
    
    # הוספת פסיקים לאלפים
    parts = formatted.split('.')
    parts[0] = f"{int(parts[0]):,}".replace(',', ',')
    
    return '.'.join(parts) if len(parts) > 1 else parts[0]

def get_color_by_score(score: float) -> str:
    """קבלת צבע לפי ציון"""
    if pd.isna(score):
        return "#999999"
    elif score >= 8.5:
        return "#10b981"  # ירוק
    elif score >= 7:
        return "#f59e0b"  # כתום
    elif score >= 5:
        return "#eab308"  # צהוב
    else:
        return "#ef4444"  # אדום

def create_alert_message(title: str, message: str, alert_type: str = "info") -> str:
    """יצירת הודעת התראה"""
    colors = {
        "success": "#10b981",
        "warning": "#f59e0b", 
        "error": "#ef4444",
        "info": "#3b82f6"
    }
    
    color = colors.get(alert_type, colors["info"])
    
    return f"""
    <div style="
        background: {color}22;
        border: 1px solid {color};
        border-radius: 8px;
        padding: 12px 16px;
        margin: 8px 0;
        color: {color};
    ">
        <strong>{title}</strong><br>
        {message}
    </div>
    """

def group_data_by_period(df: pd.DataFrame, period: str = 'D', date_column: str = 'created_at') -> pd.DataFrame:
    """קיבוץ נתונים לפי תקופה"""
    if df.empty:
        return df
    
    return df.groupby(df[date_column].dt.to_period(period)).agg({
        'overall_score': ['mean', 'count', 'min', 'max'],
        'branch': 'nunique',
        'dish_name': 'nunique'
    }).round(2)

def create_summary_stats(df: pd.DataFrame) -> Dict[str, Any]:
    """יצירת סטטיסטיקות סיכום"""
    if df.empty:
        return {
            "total_checks": 0,
            "average_score": 0,
            "unique_branches": 0,
            "unique_dishes": 0,
            "unique_chefs": 0,
            "score_distribution": {},
            "date_range": {"start": None, "end": None}
        }
    
    return {
        "total_checks": len(df),
        "average_score": float(df['overall_score'].mean()),
        "unique_branches": int(df['branch'].nunique()),
        "unique_dishes": int(df['dish_name'].nunique()),
        "unique_chefs": int(df['chef_name'].nunique()),
        "score_distribution": df['overall_score'].value_counts().to_dict(),
        "date_range": {
            "start": df['created_at'].min(),
            "end": df['created_at'].max()
        }
    }
