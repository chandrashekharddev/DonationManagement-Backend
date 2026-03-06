from fastapi import FastAPI, APIRouter
import os
from supabase import create_client, Client

app = FastAPI(title="Donation Management API")

# Initialize Supabase
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase: Client = None

if supabase_url and supabase_key:
    try:
        supabase = create_client(supabase_url, supabase_key)
        print("✅ Supabase client initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize Supabase client: {e}")
else:
    print("⚠️  SUPABASE_URL or SUPABASE_KEY not set")

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
                "suggestion": "Check SUPABASE_URL and SUPABASE_KEY environment variables",
                "env_vars_set": {
                    "SUPABASE_URL": bool(os.getenv("SUPABASE_URL")),
                    "SUPABASE_KEY": bool(os.getenv("SUPABASE_KEY")),
                    "DATABASE_URL": bool(os.getenv("DATABASE_URL"))
                }
            }
        
        # Test basic connection
        print("Testing Supabase connection...")
        
        # Try to query the users table
        result = supabase.table("users").select("*").limit(5).execute()
        
        # Try to query campaigns
        campaigns = supabase.table("campaigns").select("*").limit(5).execute()
        
        # Get table information
        tables_info = {}
        try:
            # Try to get list of tables (if possible)
            tables = supabase.table("information_schema.tables").select("table_name").eq("table_schema", "public").execute()
            tables_info["available_tables"] = [t["table_name"] for t in tables.data] if tables.data else []
        except:
            tables_info["available_tables"] = "Could not fetch table list"
        
        return {
            "status": "success",
            "message": "✅ Database connection successful",
            "timestamp": str(datetime.now()),
            "database_info": {
                "users_count": len(result.data),
                "users_sample": result.data,
                "campaigns_count": len(campaigns.data),
                "campaigns_sample": campaigns.data,
                **tables_info
            },
            "environment": {
                "supabase_configured": True,
                "database_url_configured": bool(os.getenv("DATABASE_URL")),
                "python_version": os.sys.version
            }
        }
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Database test error: {error_details}")
        
        return {
            "status": "error",
            "message": f"❌ Database connection failed: {str(e)}",
            "error_type": type(e).__name__,
            "error_details": str(error_details)[:500] if error_details else None,
            "suggestion": "Check if your tables exist and your API keys have proper permissions",
            "environment": {
                "supabase_configured": supabase is not None,
                "supabase_url_set": bool(os.getenv("SUPABASE_URL")),
                "supabase_key_set": bool(os.getenv("SUPABASE_KEY")),
                "database_url_set": bool(os.getenv("DATABASE_URL"))
            }
        }

# Add a more comprehensive health check
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
            health_status["database_response_time"] = "ok"
        else:
            health_status["services"]["database"] = "not configured"
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["services"]["database"] = "down"
        health_status["database_error"] = str(e)
        health_status["status"] = "degraded"
    
    return health_status
