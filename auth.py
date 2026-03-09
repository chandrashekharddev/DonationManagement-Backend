from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from database import supabase

SECRET_KEY = "your-secret-key-here-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Create OAuth2 scheme - this tells FastAPI to look for the token in the Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def authenticate_user(username: str, password: str):
    user = supabase.table("users").select("*").eq("username", username).execute()
    if not user.data:
        return False
    
    user_data = user.data[0]
    # In production, use hashed passwords
    if user_data["password"] != password:
        return False
    
    return user_data

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not token:
        print("No token provided")
        raise credentials_exception
    
    try:
        print(f"Decoding token: {token[:20]}...")  # Print first 20 chars for debugging
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            print("No username in token payload")
            raise credentials_exception
        print(f"Token decoded successfully for user: {username}")
    except JWTError as e:
        print(f"JWT Error: {str(e)}")
        raise credentials_exception
    
    user = supabase.table("users").select("*").eq("username", username).execute()
    if not user.data:
        print(f"User not found: {username}")
        raise credentials_exception
    
    print(f"User found: {user.data[0]['username']}")
    return user.data[0]

# Optional: Create a function that can handle optional authentication
async def get_current_user_optional(token: str = Depends(oauth2_scheme)):
    """Get current user if token is valid, otherwise return None"""
    if not token:
        return None
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
    except JWTError:
        return None
    
    user = supabase.table("users").select("*").eq("username", username).execute()
    if not user.data:
        return None
    
    return user.data[0]
