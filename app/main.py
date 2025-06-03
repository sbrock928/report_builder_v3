# app/main.py (Corrected imports)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.reporting.routers.report_router import router as report_router
from app.core.database import create_all_tables, seed_default_calculations, seed_sample_data

app = FastAPI(title="Data Warehouse Reporting API", version="1.0.0")

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(report_router)

@app.on_event("startup")
async def startup_event():
    """Initialize both SQLite databases on startup"""
    print("Initializing databases...")
    
    # Create all tables
    create_all_tables()
    print("✅ Database tables created")
    
    # Seed sample data warehouse data
    seed_sample_data()
    print("✅ Sample data seeded")
    
    # Seed default calculations
    seed_default_calculations()
    print("✅ Default calculations seeded")
    
    print("🚀 Application startup complete!")

@app.get("/")
async def root():
    return {"message": "Data Warehouse Reporting API is running"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        from app.core.database import DWSessionLocal, ConfigSessionLocal
        
        # Test DW connection
        dw_db = DWSessionLocal()
        dw_db.execute("SELECT 1")
        dw_db.close()
        
        # Test Config connection
        config_db = ConfigSessionLocal()
        config_db.execute("SELECT 1")
        config_db.close()
        
        return {
            "status": "healthy",
            "databases": {
                "data_warehouse": "connected",
                "config": "connected"
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

@app.get("/api/database/stats")
async def database_stats():
    """Get database statistics"""
    from app.core.database import DWSessionLocal, ConfigSessionLocal
    from app.datawarehouse.models import Deal, Tranche, TrancheBal
    from app.config.models import Calculation
    
    dw_db = DWSessionLocal()
    config_db = ConfigSessionLocal()
    
    try:
        stats = {
            "data_warehouse": {
                "deals": dw_db.query(Deal).count(),
                "tranches": dw_db.query(Tranche).count(),
                "tranche_balances": dw_db.query(TrancheBal).count(),
                "cycles": dw_db.query(TrancheBal.cycle_cde).distinct().count()
            },
            "config": {
                "calculations": config_db.query(Calculation).filter(Calculation.is_active == True).count(),
                "total_calculations": config_db.query(Calculation).count()
            }
        }
        return stats
    finally:
        dw_db.close()
        config_db.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)