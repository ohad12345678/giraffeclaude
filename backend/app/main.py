from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import os

from .api import v1_router
from .utils.config import settings
from .utils.database import create_tables, init_db

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Production-ready quality management system for Giraffe restaurant chain",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create upload directory
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

# Serve uploaded files
if os.path.exists(settings.UPLOAD_DIR):
    app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Include routers
app.include_router(v1_router, prefix="/api")

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "🦒 Giraffe Quality Management API",
        "version": settings.APP_VERSION,
        "status": "running",
        "docs_url": "/docs" if settings.DEBUG else "disabled"
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z",
        "version": settings.APP_VERSION
    }

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    if settings.DEBUG:
        import traceback
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "Internal server error",
                "detail": str(exc),
                "traceback": traceback.format_exc() if settings.DEBUG else None
            }
        )
    else:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error", 
                "message": "Internal server error"
            }
        )

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize database and create sample data"""
    try:
        create_tables()
        init_db()
        print("✅ Database initialized successfully")
        
        # Print available endpoints in debug mode
        if settings.DEBUG:
            print("\n📋 Available API Endpoints:")
            for route in app.routes:
                if hasattr(route, 'methods') and hasattr(route, 'path'):
                    methods = ', '.join(route.methods)
                    print(f"  {methods} {route.path}")
            
            print(f"\n🔗 API Documentation: http://localhost:8000/docs")
            print(f"🔗 Alternative Docs: http://localhost:8000/redoc")
            
    except Exception as e:
        print(f"❌ Error during startup: {e}")
        
# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources"""
    print("🛑 Shutting down Giraffe Quality API...")

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info" if settings.DEBUG else "warning"
    )