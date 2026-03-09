from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import supabase
from routes import auth, users, campaigns, donations, volunteers  # Add volunteers
from datetime import datetime
import os

app = FastAPI(title="Donation Management API")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://donation-management6.vercel.app",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "https://donationmanagement-backend-2.onrender.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(campaigns.router)
app.include_router(donations.router)
app.include_router(volunteers.router)  # Add volunteer routes

@app.get("/")
async def root():
    return {
        "message": "Donation Management API",
        "status": "running",
        "version": "2.0",
        "features": ["money_donations", "item_donations", "volunteer_management"],
        "database_configured": supabase is not None
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
    
    try:
        if supabase:
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
