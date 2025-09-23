from pydantic_settings import BaseSettings
from typing import List, Optional

class Settings(BaseSettings):
    # App Configuration
    APP_NAME: str = "Giraffe Quality Management API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = "sqlite:///./giraffe_quality.db"
    
    # Security
    SECRET_KEY: str = "change-in-production-giraffe-quality-2024"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # AI Integration
    ANTHROPIC_API_KEY: Optional[str] = None
    
    # Google Sheets Integration (Optional)
    GOOGLE_SHEETS_CREDENTIALS: Optional[str] = None
    GOOGLE_SHEET_ID: Optional[str] = None
    
    # Business Data - Predefined Lists
    BRANCHES: List[str] = [
        "חיפה", "ראשל״צ", "רמה״ח", "נס ציונה", 
        "לנדמרק", "פתח תקווה", "הרצליה", "סביון"
    ]
    
    DISHES: List[str] = [
        "פאד תאי", "מלאזית", "פיליפינית", "אפגנית",
        "קארי דלעת", "סצ'ואן", "ביף רייס"
    ]
    
    # Quality Score Settings
    MIN_SCORE: int = 1
    MAX_SCORE: int = 10
    ALERT_THRESHOLD: float = 6.0
    
    # File Upload
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE: int = 5 * 1024 * 1024  # 5MB
    ALLOWED_EXTENSIONS: List[str] = ["jpg", "jpeg", "png", "pdf"]
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    
    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173"
    ]

    class Config:
        env_file = ".env"
        case_sensitive = True

# Global settings instance
settings = Settings()
