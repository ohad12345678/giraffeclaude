# services/google_sheets.py
import pandas as pd
import streamlit as st
from typing import Dict, List, Optional, Tuple
import json
from datetime import datetime
from config import Config

try:
    import gspread
    from google.oauth2.service_account import Credentials
    GSHEETS_AVAILABLE = True
except ImportError:
    GSHEETS_AVAILABLE = False
    st.error("חסרות ספריות Google Sheets. התקן עם: pip install gspread google-auth")

class GoogleSheetsService:
    def __init__(self):
        self.client = None
        self.sheet = None
        self.is_connected = False
        self._setup_connection()
    
    def _setup_connection(self):
        """הקמת חיבור לגוגל שיטס"""
        if not GSHEETS_AVAILABLE:
            return False
        
        try:
            sheet_id = Config.get_google_sheet_id()
            creds_info = Config.get_service_account_info()
            
            if not (sheet_id and creds_info):
                return False
            
            credentials = Credentials.from_service_account_info(
                creds_info, 
                scopes=Config.SCOPES
            )
            
            self.client = gspread.authorize(credentials)
            self.sheet = self.client.open_by_key(sheet_id)
            self.is_connected = True
            return True
            
        except Exception as e:
            st.warning(f"לא ניתן להתחבר לגוגל שיטס: {e}")
            self.is_connected = False
            return False
    
    def is_available(self) -> bool:
        """בדיקה אם השירות זמין"""
        return GSHEETS_AVAILABLE and self.is_connected
    
    def add_quality_check(self, 
                         branch: str, 
                         chef_name: str, 
                         dish_name: str, 
                         overall_score: int,
                         taste_score: Optional[int] = None,
                         appearance_score: Optional[int] = None,
                         temperature_score: Optional[int] = None,
                         preparation_time_score: Optional[int] = None,
                         portion_size_score: Optional[int] = None,
                         notes: str = "",
                         reviewer_name: Optional[str] = None,
                         timestamp: Optional[str] = None) -> bool:
        """הוספת בדיקת איכות לגיליון"""
        if not self.is_available():
            return False
        
        try:
            if not timestamp:
                timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            
            # הכנת השורה להוספה
            row = [
                timestamp,
                branch,
                chef_name,
                dish_name,
                overall_score,
                taste_score or "",
                appearance_score or "",
                temperature_score or "",
                preparation_time_score or "",
                portion_size_score or "",
                notes or "",
                reviewer_name or ""
            ]
            
            # הוספה לגיליון הראשי
            main_sheet = self.sheet.sheet1
            main_sheet.append_row(row)
            
            return True
            
        except Exception as e:
            st.warning(f"שגיאה בהוספה לגוגל שיטס: {e}")
            return False
    
    def create_summary_sheet(self, df: pd.DataFrame) -> bool:
        """יצירת גיליון סיכום"""
        if not self.is_available() or df.empty:
            return False
        
        try:
            # יצירת או עדכון גיליון סיכום
            try:
                summary_sheet = self.sheet.worksheet("סיכום")
                summary_sheet.clear()
            except gspread.WorksheetNotFound:
                summary_sheet = self.sheet.add_worksheet(title="סיכום", rows=100, cols=10)
            
            # הכנת נתוני סיכום
            summary_data = []
            
            # כותרות
            summary_data.append([
                "מדד", "ערך", "תקופה", "עודכן"
            ])
            
            # נתונים כלליים
            total_checks = len(df)
            avg_score = df['overall_score'].mean()
            current_time = datetime.now().strftime("%d/%m/%Y %H:%M")
            
            summary_data.extend([
                ["סה״כ בדיקות", total_checks, "כל התקופה", current_time],
                ["ממוצע כללי", f"{avg_score:.2f}", "כל התקופה", current_time],
            ])
            
            # נתונים לפי סניף
            summary_data.append(["", "", "", ""])  # שורה ריקה
            summary_data.append(["ממוצע לפי סניף:", "", "", ""])
            
            branch_avg = df.groupby('branch')['overall_score'].agg(['mean', 'count']).round(2)
            for branch, row in branch_avg.iterrows():
                summary_data.append([
                    branch, 
                    f"{row['mean']:.2f}", 
                    f"{int(row['count'])} בדיקות",
                    current_time
                ])
            
            # כתיבה לגיליון
            summary_sheet.update('A1', summary_data)
            
            return True
            
        except Exception as e:
            st.warning(f"שגיאה ביצירת גיליון סיכום: {e}")
            return False
    
    def create_weekly_report_sheet(self, df: pd.DataFrame, week_start: datetime) -> bool:
        """יצירת גיליון דוח שבועי"""
        if not self.is_available():
            return False
        
        try:
            # סינון נתונים לשבוע
            week_end = week_start + pd.Timedelta(days=7)
            weekly_df = df[
                (df['created_at'] >= week_start) & 
                (df['created_at'] < week_end)
            ].copy()
            
            if weekly_df.empty:
                return False
            
            # שם הגיליון
            sheet_name = f"שבוע {week_start.strftime('%d.%m.%Y')}"
            
            try:
                weekly_sheet = self.sheet.worksheet(sheet_name)
                weekly_sheet.clear()
            except gspread.WorksheetNotFound:
                weekly_sheet = self.sheet.add_worksheet(title=sheet_name, rows=200, cols=15)
            
            # הכנת הנתונים
            report_data = []
            
            # כותרת הדוח
            report_data.extend([
                [f"דוח שבועי - {week_start.strftime('%d/%m/%Y')} - {week_end.strftime('%d/%m/%Y')}"],
                [""],
                ["סיכום כללי:"],
                [f"סה״כ בדיקות: {len(weekly_df)}"],
                [f"ממוצע כללי: {weekly_df['overall_score'].mean():.2f}"],
                [f"סניפים פעילים: {weekly_df['branch'].nunique()}"],
                [""],
                ["פירוט לפי סניף:"]
            ])
            
            # פירוט לפי סניף
            branch_stats = weekly_df.groupby('branch').agg({
                'overall_score': ['mean', 'min', 'max', 'count']
            }).round(2)
            
            branch_stats.columns = ['ממוצע', 'מינימום', 'מקסימום', 'כמות']
            
            # כותרות טבלה
            report_data.append(["סניף", "ממוצע", "מינימום", "מקסימום", "כמות בדיקות"])
            
            for branch, row in branch_stats.iterrows():
                report_data.append([
                    branch,
                    row['ממוצע'],
                    row['מינימום'],
                    row['מקסימום'],
                    int(row['כמות'])
                ])
            
            # המנות הבעייתיות
            report_data.extend([
                [""],
                ["מנות שדורשות תשומת לב (ציון מתחת ל-7):"]
            ])
            
            low_score_dishes = weekly_df[weekly_df['overall_score'] < 7]
            if not low_score_dishes.empty:
                problem_dishes = low_score_dishes.groupby(['branch', 'dish_name']).agg({
                    'overall_score': 'mean',
                    'chef_name': 'first'
                }).round(2).reset_index()
                
                report_data.append(["סניף", "מנה", "ממוצע", "טבח"])
                for _, row in problem_dishes.iterrows():
                    report_data.append([
                        row['branch'],
                        row['dish_name'],
                        row['overall_score'],
                        row['chef_name']
                    ])
            else:
                report_data.append(["אין מנות עם ציונים נמוכים השבוע! 🎉"])
            
            # נתונים מפורטים
            report_data.extend([
                [""],
                ["נתונים מפורטים:"],
                ["תאריך", "סניף", "טבח", "מנה", "ציון", "הערות"]
            ])
            
            # הוספת כל הבדיקות
            for _, row in weekly_df.iterrows():
                report_data.append([
                    row['created_at'].strftime('%d/%m/%Y %H:%M'),
                    row['branch'],
                    row['chef_name'],
                    row['dish_name'],
                    row['overall_score'],
                    row['notes'] or ""
                ])
            
            # כתיבה לגיליון
            weekly_sheet.update('A1', report_data)
            
            # עיצוב בסיסי
            try:
                # הדגשת כותרת
                weekly_sheet.format('A1', {
                    'textFormat': {'bold': True, 'fontSize': 14},
                    'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}
                })
                
                # הדגשת כותרות טבלאות
                weekly_sheet.format('A3:A8', {'textFormat': {'bold': True}})
                
            except Exception:
                pass  # אם העיצוב נכשל, נמשיך בלי
            
            return True
            
        except Exception as e:
            st.warning(f"שגיאה ביצירת דוח שבועי: {e}")
            return False
    
    def sync_all_data(self, df: pd.DataFrame) -> bool:
        """סנכרון כל הנתונים"""
        if not self.is_available():
            return False
        
        try:
            # יצירת גיליון נתונים מלא
            try:
                data_sheet = self.sheet.worksheet("נתונים מלאים")
                data_sheet.clear()
            except gspread.WorksheetNotFound:
                data_sheet = self.sheet.add_worksheet(title="נתונים מלאים", rows=1000, cols=15)
            
            # הכנת הנתונים לייצוא
            export_df = df[[ 
                'created_at', 'branch', 'chef_name', 'dish_name', 'overall_score',
                'taste_score', 'appearance_score', 'temperature_score', 
                'preparation_time_score', 'portion_size_score', 'notes', 'reviewer_name'
            ]].copy()
            
            # תרגום כותרות
            export_df = export_df.rename(columns={
                'created_at': 'תאריך ושעה',
                'branch': 'סניף',
                'chef_name': 'שם טבח',
                'dish_name': 'שם מנה',
                'overall_score': 'ציון כללי',
                'taste_score': 'ציון טעם',
                'appearance_score': 'ציון מראה',
                'temperature_score': 'ציון טמפרטורה',
                'preparation_time_score': 'ציון זמן הכנה',
                'portion_size_score': 'ציון כמות',
                'notes': 'הערות',
                'reviewer_name': 'שם בודק'
            })
            
            # המרת תאריכים
            export_df['תאריך ושעה'] = export_df['תאריך ושעה'].dt.strftime('%d/%m/%Y %H:%M')
            
            # המרה לרשימה
            data_list = [export_df.columns.values.tolist()]
            data_list.extend(export_df.values.tolist())
            
            # כתיבה לגיליון
            data_sheet.update('A1', data_list)
            
            # יצירת גיליונות נוספים
            self.create_summary_sheet(df)
            
            return True
            
        except Exception as e:
            st.error(f"שגיאה בסנכרון נתונים: {e}")
            return False
    
    def get_sheet_url(self) -> Optional[str]:
        """קבלת כתובת הגיליון"""
        if not self.is_available():
            return None
        
        try:
            return f"https://docs.google.com/spreadsheets/d/{Config.get_google_sheet_id()}"
        except Exception:
            return None
    
    def create_dashboard_sheet(self, df: pd.DataFrame) -> bool:
        """יצירת גיליון דשבורד"""
        if not self.is_available() or df.empty:
            return False
        
        try:
            try:
                dashboard_sheet = self.sheet.worksheet("דשבורד")
                dashboard_sheet.clear()
            except gspread.WorksheetNotFound:
                dashboard_sheet = self.sheet.add_worksheet(title="דשבורד", rows=100, cols=10)
            
            # חישוב מטריקות
            current_time = datetime.now()
            week_ago = current_time - pd.Timedelta(days=7)
            month_ago = current_time - pd.Timedelta(days=30)
            
            recent_df = df[df['created_at'] >= week_ago]
            monthly_df = df[df['created_at'] >= month_ago]
            
            # הכנת דאטה לדשבורד
            dashboard_data = [
                ["🦒 דשבורד איכות ג'ירף", "", "", ""],
                [f"עודכן: {current_time.strftime('%d/%m/%Y %H:%M')}", "", "", ""],
                ["", "", "", ""],
                ["📊 מטריקות שבוע אחרון:", "", "", ""],
                ["מספר בדיקות", len(recent_df), "", ""],
                ["ממוצע ציונים", f"{recent_df['overall_score'].mean():.2f}" if not recent_df.empty else "0", "", ""],
                ["סניפים פעילים", recent_df['branch'].nunique() if not recent_df.empty else 0, "", ""],
                ["", "", "", ""],
                ["📈 מטריקות חודש אחרון:", "", "", ""],
                ["מספר בדיקות", len(monthly_df), "", ""],
                ["ממוצע ציונים", f"{monthly_df['overall_score'].mean():.2f}" if not monthly_df.empty else "0", "", ""],
                ["", "", "", ""],
                ["🏆 ביצועי סניפים (שבוע):", "", "", ""]
            ]
            
            # הוספת ביצועי סניפים
            if not recent_df.empty:
                branch_performance = recent_df.groupby('branch')['overall_score'].agg(['mean', 'count']).round(2)
                branch_performance = branch_performance.sort_values('mean', ascending=False)
                
                dashboard_data.append(["סניף", "ממוצע", "בדיקות", ""])
                for branch, row in branch_performance.iterrows():
                    emoji = "🥇" if row['mean'] >= 8.5 else "🥈" if row['mean'] >= 7.5 else "🥉"
                    dashboard_data.append([
                        f"{emoji} {branch}", 
                        row['mean'], 
                        int(row['count']), 
                        ""
                    ])
            
            # כתיבה לגיליון
            dashboard_sheet.update('A1', dashboard_data)
            
            # עיצוב
            try:
                # כותרת ראשית
                dashboard_sheet.format('A1:D1', {
                    'textFormat': {'bold': True, 'fontSize': 16},
                    'backgroundColor': {'red': 1, 'green': 0.9, 'blue': 0.2},
                    'horizontalAlignment': 'CENTER'
                })
                
                # כותרות משנה
                dashboard_sheet.format('A4', {'textFormat': {'bold': True, 'fontSize': 12}})
                dashboard_sheet.format('A9', {'textFormat': {'bold': True, 'fontSize': 12}})
                dashboard_sheet.format('A13', {'textFormat': {'bold': True, 'fontSize': 12}})
                
                # מיזוג תאים לכותרת
                dashboard_sheet.merge_cells('A1:D1')
                
            except Exception:
                pass  # ממשיכים אם העיצוב נכשל
            
            return True
            
        except Exception as e:
            st.warning(f"שגיאה ביצירת דשבורד: {e}")
            return False

# יצירת אינסטנס גלובלי
sheets_service = GoogleSheetsService()
