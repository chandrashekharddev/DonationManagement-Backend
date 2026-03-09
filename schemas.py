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

# Required Item Schema for Campaign
class RequiredItem(BaseModel):
    item_name: str
    description: Optional[str] = None
    quantity_needed: int
    quantity_collected: int = 0
    unit: str  # e.g., "pieces", "kg", "liters", "boxes"
    is_urgent: bool = False

# Campaign Model
class Campaign(BaseModel):
    id: Optional[str] = None
    ngo_id: str
    title: str
    description: Optional[str] = None
    category: str
    campaign_type: str = "both"  # "money", "items", or "both"
    goal_amount: Optional[float] = 0  # For monetary goals
    raised_amount: float = 0
    required_items: Optional[List[RequiredItem]] = None  # List of items needed
    collected_items: Optional[List[dict]] = None  # Items collected so far
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: str = "pending"  # "pending", "active", "completed", "cancelled"
    image_url: Optional[str] = None
    pickup_required: bool = False  # Whether items need pickup
    pickup_address: Optional[str] = None
    created_at: Optional[datetime] = None

# Campaign Response (with NGO details)
class CampaignResponse(BaseModel):
    id: str
    ngo_id: str
    ngo_name: Optional[str] = None
    title: str
    description: Optional[str] = None
    category: str
    campaign_type: str
    goal_amount: float
    raised_amount: float
    required_items: Optional[List[RequiredItem]] = None
    status: str
    image_url: Optional[str] = None
    pickup_required: bool
    pickup_address: Optional[str] = None
    created_at: Optional[datetime] = None

# Item Donation Model
class ItemDonation(BaseModel):
    id: Optional[str] = None
    user_id: str
    campaign_id: str
    donation_id: Optional[str] = None  # Reference to main donation
    item_name: str
    quantity: int
    unit: str
    condition: str = "new"  # "new", "gently_used", "used"
    delivery_method: str = "pickup"  # "pickup", "dropoff"
    pickup_address: Optional[str] = None
    pickup_date: Optional[datetime] = None
    volunteer_id: Optional[str] = None  # Assigned volunteer
    status: str = "pending"  # "pending", "scheduled", "picked_up", "delivered", "cancelled"
    notes: Optional[str] = None
    created_at: Optional[datetime] = None

# Donation Model (supports both money and items)
class Donation(BaseModel):
    id: Optional[str] = None
    user_id: str
    campaign_id: str
    donation_type: str = "money"  # "money" or "items"
    amount: Optional[float] = 0  # For monetary donations
    items: Optional[List[dict]] = None  # For item donations
    payment_method: Optional[str] = None
    transaction_id: Optional[str] = None
    status: str = "completed"
    donated_at: Optional[datetime] = None

# Donation Response (with user and campaign details)
class DonationResponse(BaseModel):
    id: str
    user_id: str
    user_name: Optional[str] = None
    campaign_id: str
    campaign_title: Optional[str] = None
    donation_type: str
    amount: Optional[float] = 0
    items: Optional[List[dict]] = None
    status: str
    donated_at: Optional[datetime] = None

# Volunteer Model
class Volunteer(BaseModel):
    id: Optional[str] = None
    user_id: str
    ngo_id: str
    status: str = "active"  # "active", "inactive", "busy"
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
    status: str = "assigned"  # "assigned", "in_progress", "completed", "failed"
    completed_at: Optional[datetime] = None
    notes: Optional[str] = None

# Notification Model
class Notification(BaseModel):
    id: Optional[str] = None
    user_id: str
    title: str
    message: Optional[str] = None
    type: str  # "donation", "campaign", "pickup", "system"
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
    recent_donations: List[dict]  # List of donation objects
    recent_campaigns: List[dict]   # List of campaign objects

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
