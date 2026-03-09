from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional, List

# Existing models (keep these)
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

# Updated Campaign model with items support
class Campaign(BaseModel):
    id: Optional[str] = None
    ngo_id: str
    title: str
    description: Optional[str] = None
    category: str
    campaign_type: str = "both"  # "money", "items", or "both"
    goal_amount: Optional[float] = 0  # For monetary goals
    raised_amount: float = 0
    required_items: Optional[List[dict]] = None  # List of items needed
    collected_items: Optional[List[dict]] = None  # Items collected so far
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: str = "pending"
    image_url: Optional[str] = None
    pickup_required: bool = False  # Whether items need pickup
    pickup_address: Optional[str] = None
    created_at: Optional[datetime] = None

# New models for in-kind donations
class RequiredItem(BaseModel):
    id: Optional[str] = None
    campaign_id: str
    item_name: str
    description: Optional[str] = None
    quantity_needed: int
    quantity_collected: int = 0
    unit: str  # e.g., "pieces", "kg", "liters", "boxes"
    is_urgent: bool = False

class ItemDonation(BaseModel):
    id: Optional[str] = None
    user_id: str
    campaign_id: str
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

class Volunteer(BaseModel):
    id: Optional[str] = None
    user_id: str
    ngo_id: str
    status: str = "active"  # "active", "inactive", "busy"
    available_areas: List[str] = []
    max_pickups_per_day: int = 5
    current_pickups: int = 0
    joined_at: Optional[datetime] = None

class PickupAssignment(BaseModel):
    id: Optional[str] = None
    donation_id: str
    volunteer_id: str
    scheduled_time: datetime
    pickup_address: str
    donor_phone: str
    status: str = "assigned"  # "assigned", "in_progress", "completed", "failed"
    completed_at: Optional[datetime] = None
    notes: Optional[str] = None

# Updated Donation model to support both types
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

class Notification(BaseModel):
    id: Optional[str] = None
    user_id: str
    title: str
    message: Optional[str] = None
    type: str
    read: bool = False
    created_at: Optional[datetime] = None
