from fastapi import APIRouter, HTTPException, status
from datetime import timedelta
from schemas import UserLogin, Token, UserResponse, UserCreate
from auth import authenticate_user, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, get_password_hash
from database import supabase

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/login", response_model=Token)
async def login(login_data: UserLogin):
    user = authenticate_user(login_data.username, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"]},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse(**user)
    }

@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate):
    # Check if user exists
    existing = supabase.table("users").select("*").eq("username", user.username).execute()
    if existing.data:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # In production, hash password: user.password = get_password_hash(user.password)
    
    # Create user
    result = supabase.table("users").insert({
        "username": user.username,
        "password": user.password,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "phone": user.phone,
        "address": user.address
    }).execute()
    
    if not result.data:
        raise HTTPException(status_code=400, detail="Registration failed")
    
    # If NGO, create NGO record
    if user.role == "ngo":
        supabase.table("ngos").insert({
            "user_id": result.data[0]["id"],
            "organization_name": user.full_name,
            "verified": False
        }).execute()
    
    return UserResponse(**result.data[0])