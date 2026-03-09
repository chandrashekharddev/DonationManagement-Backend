from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional, List

# Authentication Schemas
class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict  # Will contain user information

class UserCreate(BaseModel):
    username: str
    password: str
    email: str
    full_name: str
    role: str  # "admin", "ngo", "user"
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

# User Model
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

# NGO Model
class NGO(BaseModel):
    id: Optional[str] = None
    user_id: str
    organization_name: str
    registration_number: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None
    verified: bool = False

# Required Item Schema for Campaign (keep for future use)
class RequiredItem(BaseModel):
    item_name: str
    description: Optional[str] = None
    quantity_needed: int
    quantity_collected: int = 0
    unit: str  # e.g., "pieces", "kg", "liters", "boxes"
    is_urgent: bool = False

# Campaign Model - FIXED: Made all new fields optional with defaults
class Campaign(BaseModel):
    id: Optional[str] = None
    ngo_id: Optional[str] = None  # Make optional as it will be set from current_user
    title: str
    description: Optional[str] = None
    category: str
    # Make all new fields optional with defaults to prevent validation errors
    campaign_type: Optional[str] = "both"  # Made optional
    goal_amount: float = 0  # Keep as required but with default
    raised_amount: float = 0
    required_items: Optional[List[RequiredItem]] = None  # Already optional
    collected_items: Optional[List[dict]] = None  # Already optional
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: str = "pending"
    image_url: Optional[str] = None
    pickup_required: Optional[bool] = False  # Made optional
    pickup_address: Optional[str] = None  # Already optional
    created_at: Optional[datetime] = None

# Campaign Response (with NGO details)
class CampaignResponse(BaseModel):
    id: str
    ngo_id: str
    ngo_name: Optional[str] = None
    title: str
    description: Optional[str] = None
    category: str
    campaign_type: Optional[str] = "both"  # Made optional
    goal_amount: float
    raised_amount: float
    required_items: Optional[List[RequiredItem]] = None
    status: str
    image_url: Optional[str] = None
    pickup_required: Optional[bool] = False  # Made optional
    pickup_address: Optional[str] = None
    created_at: Optional[datetime] = None

# Item Donation Model
class ItemDonation(BaseModel):
    id: Optional[str] = None
    user_id: str
    campaign_id: str
    donation_id: Optional[str] = None
    item_name: str
    quantity: int
    unit: str
    condition: str = "new"
    delivery_method: str = "pickup"
    pickup_address: Optional[str] = None
    pickup_date: Optional[datetime] = None
    volunteer_id: Optional[str] = None
    status: str = "pending"
    notes: Optional[str] = None
    created_at: Optional[datetime] = None

# Donation Model
class Donation(BaseModel):
    id: Optional[str] = None
    user_id: str
    campaign_id: str
    donation_type: Optional[str] = "money"  # Made optional
    amount: float = 0
    items: Optional[List[dict]] = None
    payment_method: Optional[str] = None
    transaction_id: Optional[str] = None
    status: str = "completed"
    donated_at: Optional[datetime] = None

# Donation Response
class DonationResponse(BaseModel):
    id: str
    user_id: str
    user_name: Optional[str] = None
    campaign_id: str
    campaign_title: Optional[str] = None
    donation_type: Optional[str] = "money"  # Made optional
    amount: float = 0
    items: Optional[List[dict]] = None
    status: str
    donated_at: Optional[datetime] = None

# Volunteer Model
class Volunteer(BaseModel):
    id: Optional[str] = None
    user_id: str
    ngo_id: str
    status: str = "active"
    available_areas: List[str] = []
    max_pickups_per_day: int = 5
    current_pickups: int = 0
    joined_at: Optional[datetime] = None

# Pickup Assignment Model
class PickupAssignment(BaseModel):
    id: Optional[str] = None
    donation_id: str
    volunteer_id: str
    scheduled_time: datetime
    pickup_address: str
    donor_phone: str
    donor_name: Optional[str] = None
    status: str = "assigned"
    completed_at: Optional[datetime] = None
    notes: Optional[str] = None

# Notification Model
class Notification(BaseModel):
    id: Optional[str] = None
    user_id: str
    title: str
    message: Optional[str] = None
    type: str
    read: bool = False
    created_at: Optional[datetime] = None

# Notification Response
class NotificationResponse(BaseModel):
    id: str
    title: str
    message: Optional[str] = None
    type: str
    read: bool
    created_at: Optional[datetime] = None

# Dashboard Statistics Model
class DashboardStats(BaseModel):
    total_donations: float
    total_campaigns: int
    total_ngos: int
    total_users: int
    active_campaigns: int
    recent_donations: List[dict]
    recent_campaigns: List[dict]

# Password Change Model
class PasswordChange(BaseModel):
    current_password: str
    new_password: str

# Campaign Update Model
class CampaignUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    goal_amount: Optional[float] = None
    status: Optional[str] = None
    image_url: Optional[str] = None
    required_items: Optional[List[RequiredItem]] = None

# Donation Status Update
class DonationStatusUpdate(BaseModel):
    status: str
    volunteer_id: Optional[str] = None
    notes: Optional[str] = None

# Volunteer Registration
class VolunteerRegistration(BaseModel):
    ngo_id: str
    available_areas: List[str]
    max_pickups_per_day: Optional[int] = 5

# Pickup Assignment Create
class PickupAssignmentCreate(BaseModel):
    donation_id: str
    scheduled_time: datetime
    notes: Optional[str] = None
