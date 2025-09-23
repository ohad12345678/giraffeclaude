from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import os

from .config import settings

# Create engine
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {},
    echo=settings.DEBUG
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base model
Base = declarative_base()

# Metadata for migrations
metadata = MetaData()

def get_db() -> Generator[Session, None, None]:
    """
    Dependency function to get database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """
    Create all tables in database
    """
    Base.metadata.create_all(bind=engine)

def init_db():
    """
    Initialize database with sample data
    """
    from ..models.user import User
    from ..services.auth_service import get_password_hash
    
    db = SessionLocal()
    try:
        # Check if admin user exists
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            admin_user = User(
                username="admin",
                email="admin@giraffe-kitchens.co.il",
                full_name="מנהל מערכת",
                hashed_password=get_password_hash("admin123"),
                role="admin",
                is_active=True,
                permissions={
                    "can_view_all_branches": True,
                    "can_manage_users": True,
                    "can_export_data": True,
                    "can_access_ai": True
                }
            )
            db.add(admin_user)
            
        # Create demo manager user
        manager_user = db.query(User).filter(User.username == "manager").first()
        if not manager_user:
            manager_user = User(
                username="manager",
                email="manager@giraffe-kitchens.co.il", 
                full_name="מנהל איכות",
                hashed_password=get_password_hash("manager123"),
                role="manager",
                is_active=True,
                assigned_branches=settings.BRANCHES,
                permissions={
                    "can_view_all_branches": True,
                    "can_export_data": True,
                    "can_access_ai": True
                }
            )
            db.add(manager_user)
            
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error initializing database: {e}")
    finally:
        db.close()
