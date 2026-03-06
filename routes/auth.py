from fastapi import APIRouter, HTTPException, status
from datetime import timedelta
from schemas import UserLogin, Token, UserResponse, UserCreate
from auth import authenticate_user, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, get_password_hash
from database import supabase
import traceback

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/login", response_model=Token)
async def login(login_data: UserLogin):
    try:
        print(f"Login attempt for username: {login_data.username}")
        
        user = authenticate_user(login_data.username, login_data.password)
        if not user:
            print(f"❌ Authentication failed for {login_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        print(f"✅ Authentication successful for {login_data.username}")
        print(f"User data: {user}")
        
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user["username"], "role": user["role"]},
            expires_delta=access_token_expires
        )
        
        # Ensure all required fields are present
        user_response = UserResponse(
            id=user["id"],
            username=user["username"],
            email=user.get("email", ""),
            full_name=user.get("full_name", ""),
            role=user["role"],
            phone=user.get("phone"),
            address=user.get("address"),
            created_at=user.get("created_at")
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user_response
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Unexpected error in login: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed due to server error"
        )

@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate):
    try:
        print(f"Registration attempt for username: {user.username}")
        
        # Check if user exists
        existing = supabase.table("users").select("*").eq("username", user.username).execute()
        if existing.data:
            raise HTTPException(status_code=400, detail="Username already registered")
        
        # Check if email exists
        existing_email = supabase.table("users").select("*").eq("email", user.email).execute()
        if existing_email.data:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # In production, hash password: user.password = get_password_hash(user.password)
        
        # Create user
        user_data = {
            "username": user.username,
            "password": user.password,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "phone": user.phone or "",
            "address": user.address or ""
        }
        
        result = supabase.table("users").insert(user_data).execute()
        
        if not result.data:
            raise HTTPException(status_code=400, detail="Registration failed")
        
        new_user = result.data[0]
        print(f"✅ User registered successfully: {user.username}")
        
        # If NGO, create NGO record
        if user.role == "ngo":
            try:
                supabase.table("ngos").insert({
                    "user_id": new_user["id"],
                    "organization_name": user.full_name,
                    "verified": False
                }).execute()
                print(f"✅ NGO record created for {user.username}")
            except Exception as e:
                print(f"⚠️ Error creating NGO record: {e}")
        
        # Return user data
        return UserResponse(
            id=new_user["id"],
            username=new_user["username"],
            email=new_user["email"],
            full_name=new_user["full_name"],
            role=new_user["role"],
            phone=new_user.get("phone"),
            address=new_user.get("address"),
            created_at=new_user.get("created_at")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in register: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")
