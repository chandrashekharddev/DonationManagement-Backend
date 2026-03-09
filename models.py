from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional, List

class User(BaseModel):
    id: Optional[str] = None
    username: str
    password: str
    email: str
    full_name: str
    role: str
    phone: Optional[str] = None
    address: Optional[str] = None
    created_at: Optional[datetime] = None

class NGO(BaseModel):
    id: Optional[str] = None
    user_id: str
    organization_name: str
    registration_number: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None
    verified: bool = False

# Required Item Schema for Campaign
class RequiredItem(BaseModel):
    item_name: str
    quantity_needed: int
    quantity_collected: int = 0
    unit: str
    is_urgent: bool = False

class Campaign(BaseModel):
    id: Optional[str] = None
    ngo_id: Optional[str] = None  # Make optional as it will be set from current_user
    title: str
    description: Optional[str] = None
    category: str
    campaign_type: str = "both"  # "money", "items", or "both"
    goal_amount: Optional[float] = 0
    raised_amount: float = 0
    required_items: Optional[List[RequiredItem]] = None
    collected_items: Optional[List[dict]] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: str = "pending"
    image_url: Optional[str] = None
    pickup_required: bool = False
    pickup_address: Optional[str] = None
    created_at: Optional[datetime] = None

class Donation(BaseModel):
    id: Optional[str] = None
    user_id: str
    campaign_id: str
    amount: float
    payment_method: Optional[str] = None
    transaction_id: Optional[str] = None
    status: str = "completed"
    donated_at: Optional[datetime] = None

class Notification(BaseModel):
    id: Optional[str] = None
    user_id: str
    title: str
    message: Optional[str] = None
    type: str
    read: bool = False
    created_at: Optional[datetime] = None
