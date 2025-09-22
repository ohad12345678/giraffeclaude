# database.py
import sqlite3
import pandas as pd
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from config import Config
import streamlit as st

class DatabaseManager:
    def __init__(self):
        self.db_path = Config.DB_PATH
        self.init_database()
    
    def get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path, check_same_thread=False)
    
    def init_database(self):
        """יצירת הטבלאות בבסיס הנתונים"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # טבלת משתמשים
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin', 'manager', 'viewer')),
            branch TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP),
            last_login TEXT
        )
        """)
        
        # טבלת בדיקות איכות מעודכנת
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS quality_checks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            branch TEXT NOT NULL,
            chef_name TEXT NOT NULL,
            dish_name TEXT NOT NULL,
            overall_score INTEGER NOT NULL CHECK(overall_score BETWEEN 1 AND 10),
            taste_score INTEGER CHECK(taste_score BETWEEN 1 AND 10),
            appearance_score INTEGER CHECK(appearance_score BETWEEN 1 AND 10),
            temperature_score INTEGER CHECK(temperature_score BETWEEN 1 AND 10),
            preparation_time_score INTEGER CHECK(preparation_time_score BETWEEN 1 AND 10),
            portion_size_score INTEGER CHECK(portion_size_score BETWEEN 1 AND 10),
            notes TEXT,
            image_path TEXT,
            created_at TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP),
            submitted_by TEXT,
            reviewer_name TEXT,
            is_followup INTEGER DEFAULT 0,
            parent_check_id INTEGER,
            status TEXT DEFAULT 'open' CHECK(status IN ('open', 'in_progress', 'resolved', 'closed')),
            FOREIGN KEY (parent_check_id) REFERENCES quality_checks (id)
        )
        """)
        
        # טבלת קטגוריות מוצרים
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS dish_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            target_score REAL DEFAULT 8.0,
            is_active INTEGER DEFAULT 1
        )
        """)
        
        # טבלת סניפים עם פרטים נוספים
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS branches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            address TEXT,
            manager_name TEXT,
            phone TEXT,
            email TEXT,
            target_score REAL DEFAULT 8.0,
            is_active INTEGER DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP)
        )
        """)
        
        # טבלת הגדרות מערכת
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            value TEXT,
            description TEXT,
            updated_at TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP)
        )
        """)
        
        # טבלת יומן פעילות
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT NOT NULL,
            table_name TEXT,
            record_id INTEGER,
            old_values TEXT,
            new_values TEXT,
            ip_address TEXT,
            user_agent TEXT,
            created_at TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """)
        
        # יצירת אינדקסים
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_quality_branch_date ON quality_checks(branch, created_at)",
            "CREATE INDEX IF NOT EXISTS idx_quality_chef_dish_date ON quality_checks(chef_name, dish_name, created_at)",
            "CREATE INDEX IF NOT EXISTS idx_quality_score_date ON quality_checks(overall_score, created_at)",
            "CREATE INDEX IF NOT EXISTS idx_activity_log_date ON activity_log(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_users_branch ON users(branch)"
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
        
        # הוספת נתוני ברירת מחדל
        self._insert_default_data(cursor)
        
        conn.commit()
        conn.close()
    
    def _insert_default_data(self, cursor):
        """הוספת נתוני ברירת מחדל"""
        # הוספת סניפים
        for branch in Config.BRANCHES:
            cursor.execute("""
                INSERT OR IGNORE INTO branches (name, is_active) 
                VALUES (?, 1)
            """, (branch,))
        
        # הוספת קטגוריות מנות
        categories = [
            ("מנות עיקריות", "מנות עיקריות כמו פאד תאי, ביף רייס"),
            ("מאקי וסושי", "מאקי סלמון, טונה וכד'"),
            ("סלטים", "סלט תאילנדי, בריאות וכד'"),
            ("מנות ילדים", "נודלס ילדים וכד'"),
            ("מנות פתיחה", "אגרול, גיוזה, וון")
        ]
        
        for name, desc in categories:
            cursor.execute("""
                INSERT OR IGNORE INTO dish_categories (name, description) 
                VALUES (?, ?)
            """, (name, desc))
        
        # הגדרות ברירת מחדל
        default_settings = [
            ("min_chef_reviews_weekly", "2", "מספר ביקורות מינימלי לטבח בשבוע"),
            ("min_dish_reviews_weekly", "2", "מספר ביקורות מינימלי למנה בשבוע"),
            ("target_overall_score", "8.0", "ציון מטרה כללי"),
            ("auto_sync_sheets", "true", "סנכרון אוטומטי לגוגל שיטס"),
            ("alert_low_score", "6.0", "התראה על ציון נמוך"),
        ]
        
        for key, value, desc in default_settings:
            cursor.execute("""
                INSERT OR IGNORE INTO settings (key, value, description) 
                VALUES (?, ?, ?)
            """, (key, value, desc))
    
    @st.cache_data(ttl=15)
    def load_quality_checks(_self) -> pd.DataFrame:
        """טעינת כל בדיקות האיכות"""
        conn = _self.get_connection()
        query = """
        SELECT 
            id, branch, chef_name, dish_name, 
            overall_score, taste_score, appearance_score, 
            temperature_score, preparation_time_score, portion_size_score,
            notes, image_path, created_at, submitted_by, reviewer_name,
            is_followup, parent_check_id, status
        FROM quality_checks 
        ORDER BY created_at DESC
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if "created_at" in df.columns:
            df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce", utc=True)
        
        return df
    
    def load_quality_checks_fresh(self) -> pd.DataFrame:
        """טעינה טריה ללא cache"""
        conn = self.get_connection()
        query = """
        SELECT 
            id, branch, chef_name, dish_name, 
            overall_score, taste_score, appearance_score, 
            temperature_score, preparation_time_score, portion_size_score,
            notes, image_path, created_at, submitted_by, reviewer_name,
            is_followup, parent_check_id, status
        FROM quality_checks 
        ORDER BY created_at DESC
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if "created_at" in df.columns:
            df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce", utc=True)
        
        return df
    
    def insert_quality_check(self, 
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
                           image_path: Optional[str] = None,
                           submitted_by: Optional[str] = None,
                           reviewer_name: Optional[str] = None,
                           is_followup: bool = False,
                           parent_check_id: Optional[int] = None) -> int:
        """הוספת בדיקת איכות חדשה"""
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO quality_checks (
                branch, chef_name, dish_name, overall_score,
                taste_score, appearance_score, temperature_score,
                preparation_time_score, portion_size_score,
                notes, image_path, created_at, submitted_by, reviewer_name,
                is_followup, parent_check_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            branch.strip(), chef_name.strip(), dish_name.strip(), int(overall_score),
            taste_score, appearance_score, temperature_score,
            preparation_time_score, portion_size_score,
            (notes or "").strip(), image_path, timestamp, submitted_by, reviewer_name,
            1 if is_followup else 0, parent_check_id
        ))
        
        check_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return check_id
    
    def get_branches_data(self) -> pd.DataFrame:
        """קבלת נתוני סניפים"""
        conn = self.get_connection()
        df = pd.read_sql_query("""
            SELECT name, address, manager_name, phone, email, target_score, is_active 
            FROM branches 
            WHERE is_active = 1
            ORDER BY name
        """, conn)
        conn.close()
        return df
    
    def get_dish_categories(self) -> pd.DataFrame:
        """קבלת קטגוריות מנות"""
        conn = self.get_connection()
        df = pd.read_sql_query("""
            SELECT name, description, target_score 
            FROM dish_categories 
            WHERE is_active = 1
            ORDER BY name
        """, conn)
        conn.close()
        return df
    
    def get_settings(self) -> Dict[str, str]:
        """קבלת הגדרות המערכת"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT key, value FROM settings")
        settings = {row[0]: row[1] for row in cursor.fetchall()}
        conn.close()
        return settings
    
    def update_setting(self, key: str, value: str):
        """עדכון הגדרה"""
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE settings SET value = ?, updated_at = ? WHERE key = ?
        """, (value, timestamp, key))
        conn.commit()
        conn.close()
    
    def log_activity(self, user_id: Optional[int], action: str, 
                    table_name: Optional[str] = None,
                    record_id: Optional[int] = None,
                    old_values: Optional[str] = None,
                    new_values: Optional[str] = None):
        """רישום פעילות במערכת"""
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO activity_log (
                user_id, action, table_name, record_id, 
                old_values, new_values, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, action, table_name, record_id, old_values, new_values, timestamp))
        conn.commit()
        conn.close()
    
    def clear_cache(self):
        """ניקוי cache"""
        self.load_quality_checks.clear()

# יצירת אינסטנס גלובלי
db_manager = DatabaseManager()
