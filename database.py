import os
from supabase import create_client, Client
from dotenv import load_dotenv
import urllib.parse

# Load environment variables
load_dotenv()

# Get Supabase credentials
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
database_url = os.getenv("DATABASE_URL")

print("=" * 50)
print("Starting Supabase connection...")
print(f"SUPABASE_URL: {url}")
print(f"SUPABASE_KEY configured: {'Yes' if key else 'No'}")
print(f"DATABASE_URL configured: {'Yes' if database_url else 'No'}")
print("=" * 50)

# Create Supabase client
try:
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
    
    supabase: Client = create_client(url, key)
    print("✅ Supabase client created successfully")
    
    # Test the connection by trying to query the users table
    test_query = supabase.table("users").select("*").limit(1).execute()
    print("✅ Database connection test successful")
    print(f"Test query result: {test_query.data}")
    
except Exception as e:
    print(f"❌ Error connecting to Supabase: {e}")
    supabase = None
