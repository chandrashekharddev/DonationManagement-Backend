@app.get("/test-db")
async def test_database():
    """Test database connection"""
    try:
        if supabase is None:
            return {
                "status": "error",
                "message": "Supabase client not initialized",
                "suggestion": "Check SUPABASE_URL and SUPABASE_KEY environment variables"
            }
        
        # Try to query the users table
        result = supabase.table("users").select("*").limit(5).execute()
        
        # Try to query campaigns
        campaigns = supabase.table("campaigns").select("*").limit(5).execute()
        
        return {
            "status": "success",
            "message": "✅ Database connection successful",
            "users_count": len(result.data),
            "users_sample": result.data,
            "campaigns_count": len(campaigns.data),
            "campaigns_sample": campaigns.data,
            "database_url_configured": bool(os.getenv("DATABASE_URL"))
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"❌ Database connection failed: {str(e)}",
            "error_type": type(e).__name__
        }
