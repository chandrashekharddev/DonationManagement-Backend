#!/usr/bin/env python3
import os
import uvicorn

if __name__ == "__main__":
    # Create uploads directory if it doesn't exist
    uploads_dir = "uploads"
    if not os.path.exists(uploads_dir):
        os.makedirs(uploads_dir)
        print(f"Created uploads directory: {uploads_dir}")
    
    # Create any other necessary directories
    temp_dir = "temp"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
        print(f"Created temp directory: {temp_dir}")
    
    # Get port from environment variable (Render provides this)
    port = int(os.environ.get("PORT", 10000))
    
    # Log environment info (helpful for debugging)
    print(f"Python version: {os.sys.version}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"PORT environment variable: {os.environ.get('PORT', 'Not set')}")
    print(f"Starting server on port {port}...")
    
    # Run the FastAPI app
    uvicorn.run(
        "app.main:app",  # Adjust this if your app structure is different
        host="0.0.0.0",
        port=port,
        reload=False,  # Set to False for production
        log_level="info"
    )
