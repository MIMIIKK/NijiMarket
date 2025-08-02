from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from app.core.config import settings
from app.database import engine, Base
from app.api import auth, markets, vendors, categories, products

# Create all tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    debug=settings.DEBUG,
    description="NijiMarket API - Connecting local farmers' markets with digital technology"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (uploaded images)
uploads_dir = Path("uploads")
if uploads_dir.exists():
    app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Include API routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(markets.router, prefix="/api/v1")
app.include_router(vendors.router, prefix="/api/v1")
app.include_router(categories.router, prefix="/api/v1")
app.include_router(products.router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.VERSION,
        "status": "Phase 3 Complete - Core Business Logic",
        "features": [
            "Authentication & Authorization",
            "Market Management",
            "Vendor Profiles",
            "Product Catalog",
            "Category Management",
            "Image Upload System",
            "Role-based Access Control"
        ],
        "endpoints": {
            "docs": "/docs",
            "auth": "/api/v1/auth",
            "markets": "/api/v1/markets",
            "vendors": "/api/v1/vendors",
            "categories": "/api/v1/categories",
            "products": "/api/v1/products",
            "health": "/health"
        }
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy", 
        "phase": "3 - Core Business Logic",
        "features_available": [
            "User Authentication",
            "Market Management",
            "Vendor Profiles",
            "Product Listings",
            "Category System",
            "Image Uploads"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)