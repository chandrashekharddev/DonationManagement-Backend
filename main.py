from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import supabase  # Import the client from database.py
from routes import auth, users, campaigns, donations
from datetime import datetime
import os

app = FastAPI(title="Donation Management API")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://donation-management5.vercel.app",  # Your Vercel frontend
        "http://localhost:5500",                     # Local development
        "http://127.0.0.1:5500",                      # Local development
        "https://donationmanagement-backend-2.onrender.com"  # Backend itself
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allows all headers
    expose_headers=["*"],  # Exposes all headers
)

# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(campaigns.router)
app.include_router(donations.router)

@app.get("/")
async def root():
    return {
        "message": "Donation Management API",
        "status": "running",
        "database_configured": supabase is not None
    }

@app.get("/test-db")
async def test_database():
    """Test database connection"""
    try:
        if supabase is None:
            return {
                "status": "error",
                "message": "❌ Supabase client not initialized",
                "suggestion": "Check SUPABASE_URL and SUPABASE_KEY environment variables in Render",
                "env_vars_set": {
                    "SUPABASE_URL": bool(os.getenv("SUPABASE_URL")),
                    "SUPABASE_KEY": bool(os.getenv("SUPABASE_KEY")),
                }
            }
        
        # Test basic connection
        print("Testing Supabase connection...")
        
        # Try to query the users table
        result = supabase.table("users").select("*").limit(5).execute()
        
        return {
            "status": "success",
            "message": "✅ Database connection successful",
            "timestamp": str(datetime.now()),
            "data": result.data
        }
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Database test error: {error_details}")
        
        return {
            "status": "error",
            "message": f"❌ Database connection failed: {str(e)}",
            "error_type": type(e).__name__
        }

@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint"""
    health_status = {
        "status": "healthy",
        "timestamp": str(datetime.now()),
        "services": {
            "api": "up",
            "database": "unknown"
        }
    }
    
    # Check database
    try:
        if supabase:
            # Simple query to check database
            result = supabase.table("users").select("id").limit(1).execute()
            health_status["services"]["database"] = "up"
        else:
            health_status["services"]["database"] = "not configured"
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["services"]["database"] = "down"
        health_status["database_error"] = str(e)
        health_status["status"] = "degraded"
    
    return health_status
