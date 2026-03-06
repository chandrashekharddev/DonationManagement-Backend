from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date

class UserLogin(BaseModel):
    username: str
    password: str

class UserCreate(BaseModel):
    username: str
    password: str
    email: str
    full_name: str
    role: str
    phone: Optional[str] = None
    address: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    full_name: str
    role: str
    phone: Optional[str] = None
    address: Optional[str] = None
    created_at: Optional[datetime] = None

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class CampaignCreate(BaseModel):
    title: str
    description: Optional[str] = None
    category: str
    goal_amount: float
    end_date: Optional[date] = None
    image_url: Optional[str] = None

class CampaignResponse(BaseModel):
    id: str
    ngo_id: str
    ngo_name: Optional[str] = None
    title: str
    description: Optional[str] = None
    category: str
    goal_amount: float
    raised_amount: float
    status: str
    image_url: Optional[str] = None
    created_at: Optional[datetime] = None

class DonationCreate(BaseModel):
    campaign_id: str
    amount: float
    payment_method: Optional[str] = None

class DonationResponse(BaseModel):
    id: str
    user_id: str
    user_name: Optional[str] = None
    campaign_id: str
    campaign_title: Optional[str] = None
    amount: float
    status: str
    donated_at: Optional[datetime] = None

class NotificationResponse(BaseModel):
    id: str
    title: str
    message: Optional[str] = None
    type: str
    read: bool
    created_at: Optional[datetime] = None

class DashboardStats(BaseModel):
    total_donations: float
    total_campaigns: int
    total_ngos: int
    total_users: int
    active_campaigns: int
    recent_donations: List[DonationResponse]
    recent_campaigns: List[CampaignResponse]