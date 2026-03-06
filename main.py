from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import auth, campaigns, donations, users

app = FastAPI(title="HopeShare API", version="1.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5500", "http://127.0.0.1:5500", "https://your-frontend.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(campaigns.router)
app.include_router(donations.router)
app.include_router(users.router)

@app.get("/")
async def root():
    return {"message": "Welcome to HopeShare API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}