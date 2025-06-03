# app/main.py
"""Main FastAPI application with feature-based routing"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Import feature routers
from app.features.reports.router import router as reports_router
from app.features.calculations.router import router as calculations_router
from app.features.datawarehouse.router import router as datawarehouse_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    print("Initializing databases...")
    
    try:
        # Import database functions
        from app.core.database import (
            create_dw_tables, 
            create_config_tables, 
            seed_sample_data, 
            seed_default_calculations
        )
        
        # Create database tables
        await create_dw_tables()
        await create_config_tables()
        print("✅ Database tables created")
        
        # Seed sample data
        await seed_sample_data()
        print("✅ Sample data seeded")
        
        # Seed default calculations
        await seed_default_calculations()
        print("✅ Default calculations seeded")
        
        print("🚀 Application startup complete!")
        
    except Exception as e:
        print(f"❌ Error during startup: {e}")
        raise
    
    yield
    
    # Shutdown
    print("Application shutdown")

# Create FastAPI application
app = FastAPI(
    title="Reporting System API",
    description="API for generating financial reports with configurable calculations",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include feature routers
app.include_router(reports_router, prefix="/api/reports", tags=["reports"])
app.include_router(calculations_router, prefix="/api/calculations", tags=["calculations"])
app.include_router(datawarehouse_router, prefix="/api/reports", tags=["datawarehouse"])

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Reporting system is running"}

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Reporting System API",
        "version": "1.0.0",
        "docs_url": "/docs",
        "health_url": "/health",
        "features": [
            "reports", 
            "calculations", 
            "datawarehouse"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)