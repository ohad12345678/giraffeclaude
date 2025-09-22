# services/auth_service.py
import streamlit as st
import hashlib
import secrets
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
import json
from config import Config

class AuthService:
    def __init__(self):
        self.db_path = Config.DB_PATH
        self.session_timeout = timedelta(hours=8)  # 8 שעות
        self._init_auth_tables()
        self._create_default_admin()
    
    def _init_auth_tables(self):
        """יצירת טבלאות אימות"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # טבלת משתמשים מתקדמת
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            full_name TEXT NOT NULL,
            email TEXT,
            role TEXT NOT NULL CHECK(role IN ('admin', 'manager', 'branch_manager', 'viewer')),
            branch TEXT,
            permissions TEXT,  -- JSON של הרשאות מותאמות
            is_active INTEGER DEFAULT 1,
            last_login TEXT,
            login_attempts INTEGER DEFAULT 0,
            locked_until TEXT,
            created_at TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP),
            created_by INTEGER,
            FOREIGN KEY (created_by) REFERENCES users (id)
        )
        """)
        
        # טבלת סשנים
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            session_token TEXT UNIQUE NOT NULL,
            created_at TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP),
            expires_at TEXT NOT NULL,
            ip_address TEXT,
            user_agent TEXT,
            is_active INTEGER DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """)
        
        # טבלת יומן כניסות
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS login_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT NOT NULL,
            login_time TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP),
            ip_address TEXT,
            user_agent TEXT,
            success INTEGER NOT NULL,
            failure_reason TEXT
        )
        """)
        
        conn.commit()
        conn.close()
    
    def _create_default_admin(self):
        """יצירת משתמש admin ברירת מחדל"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # בדיקה אם כבר קיים admin
        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
        admin_count = cursor.fetchone()[0]
        
        if admin_count == 0:
            # יצירת admin ברירת מחדל
            password = "admin123"  # סיסמה זמנית
            salt = secrets.token_hex(16)
            password_hash = self._hash_password(password, salt)
            
            permissions = json.dumps({
                "can_create_users": True,
                "can_delete_users": True,
                "can_view_all_branches": True,
                "can_export_data": True,
                "can_manage_settings": True,
                "can_view_analytics": True
            })
            
            cursor.execute("""
                INSERT INTO users (username, password_hash, salt, full_name, email, role, permissions)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, ("admin", password_hash, salt, "מנהל מערכת", "admin@giraffe.co.il", "admin", permissions))
            
            st.info("🔑 נוצר משתמש admin ברירת מחדל: admin / admin123 (יש לשנות סיסמה!)")
        
        conn.commit()
        conn.close()
    
    def _hash_password(self, password: str, salt: str) -> str:
        """הצפנת סיסמה"""
        return hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex()
    
    def _generate_session_token(self) -> str:
        """יצירת טוקן סשן"""
        return secrets.token_urlsafe(32)
    
    def authenticate_user(self, username: str, password: str, ip_address: str = None, user_agent: str = None) -> Optional[Dict]:
        """אימות משתמש"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # בדיקת נעילת משתמש
            cursor.execute("""
                SELECT id, password_hash, salt, full_name, email, role, branch, permissions, 
                       is_active, login_attempts, locked_until
                FROM users WHERE username = ?
            """, (username,))
            
            user_data = cursor.fetchone()
            
            # רישום ניסיון כניסה
            success = False
            failure_reason = None
            user_id = None
            
            if not user_data:
                failure_reason = "שם משתמש לא קיים"
            else:
                user_id, password_hash, salt, full_name, email, role, branch, permissions, is_active, login_attempts, locked_until = user_data
                
                # בדיקת נעילה
                if locked_until:
                    lock_time = datetime.fromisoformat(locked_until)
                    if datetime.now() < lock_time:
                        failure_reason = f"חשבון נעול עד {lock_time.strftime('%H:%M:%S')}"
                    else:
                        # ביטול נעילה
                        cursor.execute("UPDATE users SET locked_until = NULL, login_attempts = 0 WHERE id = ?", (user_id,))
                
                if not failure_reason and not is_active:
                    failure_reason = "חשבון לא פעיל"
                
                if not failure_reason:
                    # בדיקת סיסמה
                    if self._hash_password(password, salt) == password_hash:
                        success = True
                        # איפוס ניסיונות כושלים
                        cursor.execute("UPDATE users SET login_attempts = 0, locked_until = NULL, last_login = ? WHERE id = ?", 
                                     (datetime.now().isoformat(), user_id))
                    else:
                        failure_reason = "סיסמה שגויה"
                        login_attempts += 1
                        
                        # נעילת חשבון אחרי 5 ניסיונות כושלים
                        if login_attempts >= 5:
                            locked_until = (datetime.now() + timedelta(minutes=30)).isoformat()
                            cursor.execute("UPDATE users SET login_attempts = ?, locked_until = ? WHERE id = ?", 
                                         (login_attempts, locked_until, user_id))
                            failure_reason = "חשבון נעול ל-30 דקות (יותר מדי ניסיונות כושלים)"
                        else:
                            cursor.execute("UPDATE users SET login_attempts = ? WHERE id = ?", (login_attempts, user_id))
            
            # רישום יומן
            cursor.execute("""
                INSERT INTO login_logs (user_id, username, ip_address, user_agent, success, failure_reason)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, username, ip_address, user_agent, 1 if success else 0, failure_reason))
            
            if success:
                # יצירת סשן
                session_token = self._generate_session_token()
                expires_at = (datetime.now() + self.session_timeout).isoformat()
                
                cursor.execute("""
                    INSERT INTO user_sessions (user_id, session_token, expires_at, ip_address, user_agent)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, session_token, expires_at, ip_address, user_agent))
                
                conn.commit()
                
                return {
                    'user_id': user_id,
                    'username': username,
                    'full_name': full_name,
                    'email': email,
                    'role': role,
                    'branch': branch,
                    'permissions': json.loads(permissions) if permissions else {},
                    'session_token': session_token
                }
            else:
                conn.commit()
                return None
                
        except Exception as e:
            conn.rollback()
            st.error(f"שגיאה באימות: {e}")
            return None
        finally:
            conn.close()
    
    def validate_session(self, session_token: str) -> Optional[Dict]:
        """אימות סשן"""
        if not session_token:
            return None
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT u.id, u.username, u.full_name, u.email, u.role, u.branch, u.permissions, u.is_active,
                       s.expires_at
                FROM user_sessions s
                JOIN users u ON s.user_id = u.id
                WHERE s.session_token = ? AND s.is_active = 1 AND u.is_active = 1
            """, (session_token,))
            
            session_data = cursor.fetchone()
            
            if not session_data:
                return None
            
            user_id, username, full_name, email, role, branch, permissions, is_active, expires_at = session_data
            
            # בדיקת תפוגה
            if datetime.now() > datetime.fromisoformat(expires_at):
                # סשן פג תוקף
                cursor.execute("UPDATE user_sessions SET is_active = 0 WHERE session_token = ?", (session_token,))
                conn.commit()
                return None
            
            # הארכת סשן
            new_expires_at = (datetime.now() + self.session_timeout).isoformat()
            cursor.execute("UPDATE user_sessions SET expires_at = ? WHERE session_token = ?", 
                         (new_expires_at, session_token))
            conn.commit()
            
            return {
                'user_id': user_id,
                'username': username,
                'full_name': full_name,
                'email': email,
                'role': role,
                'branch': branch,
                'permissions': json.loads(permissions) if permissions else {},
                'session_token': session_token
            }
            
        except Exception as e:
            st.error(f"שגיאה באימות סשן: {e}")
            return None
        finally:
            conn.close()
    
    def logout_user(self, session_token: str) -> bool:
        """התנתקות משתמש"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("UPDATE user_sessions SET is_active = 0 WHERE session_token = ?", (session_token,))
            conn.commit()
            return True
        except Exception:
            return False
        finally:
            conn.close()
    
    def create_user(self, username: str, password: str, full_name: str, email: str, role: str, 
                   branch: Optional[str] = None, permissions: Optional[Dict] = None, 
                   created_by_id: Optional[int] = None) -> bool:
        """יצירת משתמש חדש"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # בדיקת קיום שם משתמש
            cursor.execute("SELECT COUNT(*) FROM users WHERE username = ?", (username,))
            if cursor.fetchone()[0] > 0:
                st.error("שם משתמש כבר קיים")
                return False
            
            # הצפנת סיסמה
            salt = secrets.token_hex(16)
            password_hash = self._hash_password(password, salt)
            
            # הרשאות ברירת מחדל לפי תפקיד
            if not permissions:
                permissions = self._get_default_permissions(role)
            
            permissions_json = json.dumps(permissions)
            
            cursor.execute("""
                INSERT INTO users (username, password_hash, salt, full_name, email, role, branch, permissions, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (username, password_hash, salt, full_name, email, role, branch, permissions_json, created_by_id))
            
            conn.commit()
            return True
            
        except Exception as e:
            conn.rollback()
            st.error(f"שגיאה ביצירת משתמש: {e}")
            return False
        finally:
            conn.close()
    
    def _get_default_permissions(self, role: str) -> Dict:
        """הרשאות ברירת מחדל לפי תפקיד"""
        if role == "admin":
            return {
                "can_create_users": True,
                "can_delete_users": True,
                "can_view_all_branches": True,
                "can_export_data": True,
                "can_manage_settings": True,
                "can_view_analytics": True,
                "can_use_ai_features": True
            }
        elif role == "manager":
            return {
                "can_create_users": False,
                "can_delete_users": False,
                "can_view_all_branches": True,
                "can_export_data": True,
                "can_manage_settings": False,
                "can_view_analytics": True,
                "can_use_ai_features": True
            }
        elif role == "branch_manager":
            return {
                "can_create_users": False,
                "can_delete_users": False,
                "can_view_all_branches": False,
                "can_export_data": True,
                "can_manage_settings": False,
                "can_view_analytics": True,
                "can_use_ai_features": False
            }
        else:  # viewer
            return {
                "can_create_users": False,
                "can_delete_users": False,
                "can_view_all_branches": False,
                "can_export_data": False,
                "can_manage_settings": False,
                "can_view_analytics": False,
                "can_use_ai_features": False
            }
    
    def check_permission(self, user: Dict, permission: str) -> bool:
        """בדיקת הרשאה ספציפית"""
        if not user:
            return False
        
        # אדמין תמיד מורשה
        if user.get('role') == 'admin':
            return True
        
        permissions = user.get('permissions', {})
        return permissions.get(permission, False)
    
    def get_users_list(self) -> List[Dict]:
        """קבלת רשימת משתמשים"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT id, username, full_name, email, role, branch, is_active, 
                       last_login, created_at, login_attempts
                FROM users
                ORDER BY created_at DESC
            """)
            
            users = []
            for row in cursor.fetchall():
                users.append({
                    'id': row[0],
                    'username': row[1],
                    'full_name': row[2],
                    'email': row[3],
                    'role': row[4],
                    'branch': row[5],
                    'is_active': bool(row[6]),
                users.append({
                    'id': row[0],
                    'username': row[1],
                    'full_name': row[2],
                    'email': row[3],
                    'role': row[4],
                    'branch': row[5],
                    'is_active': bool(row[6]),
                    'last_login': row[7],
                    'created_at': row[8],
                    'login_attempts': row[9]
                })
            
            return users
            
        except Exception as e:
            st.error(f"שגיאה בקבלת רשימת משתמשים: {e}")
            return []
        finally:
            conn.close()
    
    def update_user_status(self, user_id: int, is_active: bool) -> bool:
        """עדכון סטטוס משתמש"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("UPDATE users SET is_active = ? WHERE id = ?", (1 if is_active else 0, user_id))
            
            # אם המשתמש הושבת, ביטול כל הסשנים שלו
            if not is_active:
                cursor.execute("UPDATE user_sessions SET is_active = 0 WHERE user_id = ?", (user_id,))
            
            conn.commit()
            return True
        except Exception:
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """שינוי סיסמה"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # אימות סיסמה נוכחית
            cursor.execute("SELECT password_hash, salt FROM users WHERE id = ?", (user_id,))
            user_data = cursor.fetchone()
            
            if not user_data:
                return False
            
            password_hash, salt = user_data
            
            if self._hash_password(old_password, salt) != password_hash:
                st.error("סיסמה נוכחית שגויה")
                return False
            
            # יצירת סיסמה חדשה
            new_salt = secrets.token_hex(16)
            new_password_hash = self._hash_password(new_password, new_salt)
            
            cursor.execute("UPDATE users SET password_hash = ?, salt = ? WHERE id = ?", 
                         (new_password_hash, new_salt, user_id))
            
            conn.commit()
            return True
            
        except Exception as e:
            conn.rollback()
            st.error(f"שגיאה בשינוי סיסמה: {e}")
            return False
        finally:
            conn.close()
    
    def reset_user_password(self, user_id: int, new_password: str) -> bool:
        """איפוס סיסמה על ידי אדמין"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            new_salt = secrets.token_hex(16)
            new_password_hash = self._hash_password(new_password, new_salt)
            
            cursor.execute("""
                UPDATE users 
                SET password_hash = ?, salt = ?, login_attempts = 0, locked_until = NULL 
                WHERE id = ?
            """, (new_password_hash, new_salt, user_id))
            
            conn.commit()
            return True
            
        except Exception:
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def get_user_activity_logs(self, user_id: Optional[int] = None, days: int = 30) -> List[Dict]:
        """קבלת יומני פעילות"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            if user_id:
                cursor.execute("""
                    SELECT username, login_time, ip_address, success, failure_reason
                    FROM login_logs
                    WHERE user_id = ? AND login_time > datetime('now', '-{} days')
                    ORDER BY login_time DESC
                """.format(days), (user_id,))
            else:
                cursor.execute("""
                    SELECT username, login_time, ip_address, success, failure_reason
                    FROM login_logs
                    WHERE login_time > datetime('now', '-{} days')
                    ORDER BY login_time DESC
                """.format(days))
            
            logs = []
            for row in cursor.fetchall():
                logs.append({
                    'username': row[0],
                    'login_time': row[1],
                    'ip_address': row[2],
                    'success': bool(row[3]),
                    'failure_reason': row[4]
                })
            
            return logs
            
        except Exception as e:
            st.error(f"שגיאה בקבלת יומני פעילות: {e}")
            return []
        finally:
            conn.close()
    
    def clean_expired_sessions(self):
        """ניקוי סשנים שפגו תוקף"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("UPDATE user_sessions SET is_active = 0 WHERE expires_at < ?", 
                         (datetime.now().isoformat(),))
            conn.commit()
        except Exception:
            pass
        finally:
            conn.close()

# יצירת אינסטנס גלובלי
auth_service = AuthService()
