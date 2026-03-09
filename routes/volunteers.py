from fastapi import APIRouter, Depends, HTTPException
from typing import List
from auth import get_current_user
from database import supabase
from schemas import Volunteer, PickupAssignment
from datetime import datetime
import traceback

router = APIRouter(prefix="/volunteers", tags=["volunteers"])

@router.post("/register")
async def register_as_volunteer(
    ngo_id: str,
    available_areas: List[str],
    current_user: dict = Depends(get_current_user)
):
    """Register as a volunteer for an NGO"""
    try:
        if current_user["role"] != "user":
            raise HTTPException(status_code=400, detail="Only users can be volunteers")
        
        # Check if already registered
        existing = supabase.table("volunteers").select("*")\
            .eq("user_id", current_user["id"])\
            .eq("ngo_id", ngo_id).execute()
        
        if existing.data:
            raise HTTPException(status_code=400, detail="Already registered as volunteer")
        
        volunteer_data = {
            "user_id": current_user["id"],
            "ngo_id": ngo_id,
            "status": "active",
            "available_areas": available_areas,
            "max_pickups_per_day": 5,
            "current_pickups": 0,
            "joined_at": datetime.utcnow().isoformat()
        }
        
        result = supabase.table("volunteers").insert(volunteer_data).execute()
        
        return {"message": "Registered as volunteer successfully", "data": result.data[0]}
        
    except Exception as e:
        print(f"Error in volunteer registration: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ngo/{ngo_id}")
async def get_ngo_volunteers(ngo_id: str, current_user: dict = Depends(get_current_user)):
    """Get all volunteers for an NGO (NGO only)"""
    try:
        if current_user["role"] != "ngo":
            raise HTTPException(status_code=403, detail="Only NGOs can view volunteers")
        
        result = supabase.table("volunteers").select(
            "*, users!volunteers_user_id(full_name, phone, email)"
        ).eq("ngo_id", ngo_id).execute()
        
        return result.data
        
    except Exception as e:
        print(f"Error fetching volunteers: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/available-pickups")
async def get_available_pickups(current_user: dict = Depends(get_current_user)):
    """Get available pickups for volunteers"""
    try:
        # Get pending item donations that need pickup
        result = supabase.table("item_donations").select(
            "*, campaigns!item_donations_campaign_id(title, ngo_id), users!item_donations_user_id(full_name, phone, address)"
        ).eq("status", "pending").eq("delivery_method", "pickup").execute()
        
        return result.data
        
    except Exception as e:
        print(f"Error fetching available pickups: {e}")
        return []

@router.post("/assign-pickup")
async def assign_pickup(
    donation_id: str,
    scheduled_time: datetime,
    current_user: dict = Depends(get_current_user)
):
    """Volunteer assigns themselves to a pickup"""
    try:
        # Check if volunteer exists
        volunteer = supabase.table("volunteers").select("*")\
            .eq("user_id", current_user["id"]).execute()
        
        if not volunteer.data:
            raise HTTPException(status_code=400, detail="Not registered as volunteer")
        
        # Check donation exists and is pending
        donation = supabase.table("item_donations").select("*")\
            .eq("id", donation_id).execute()
        
        if not donation.data:
            raise HTTPException(status_code=404, detail="Donation not found")
        
        if donation.data[0]["status"] != "pending":
            raise HTTPException(status_code=400, detail="Donation already assigned")
        
        # Create pickup assignment
        assignment_data = {
            "donation_id": donation_id,
            "volunteer_id": volunteer.data[0]["id"],
            "scheduled_time": scheduled_time.isoformat(),
            "pickup_address": donation.data[0]["pickup_address"],
            "donor_phone": donation.data[0].get("donor_phone", ""),
            "status": "assigned"
        }
        
        result = supabase.table("pickup_assignments").insert(assignment_data).execute()
        
        # Update donation status
        supabase.table("item_donations").update({"status": "assigned"}).eq("id", donation_id).execute()
        
        # Update volunteer's current pickups count
        supabase.table("volunteers").update({
            "current_pickups": volunteer.data[0]["current_pickups"] + 1
        }).eq("id", volunteer.data[0]["id"]).execute()
        
        return {"message": "Pickup assigned successfully", "data": result.data[0]}
        
    except Exception as e:
        print(f"Error assigning pickup: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/complete-pickup/{assignment_id}")
async def complete_pickup(assignment_id: str, current_user: dict = Depends(get_current_user)):
    """Mark pickup as completed"""
    try:
        # Get assignment
        assignment = supabase.table("pickup_assignments").select("*")\
            .eq("id", assignment_id).execute()
        
        if not assignment.data:
            raise HTTPException(status_code=404, detail="Assignment not found")
        
        # Update assignment
        supabase.table("pickup_assignments").update({
            "status": "completed",
            "completed_at": datetime.utcnow().isoformat()
        }).eq("id", assignment_id).execute()
        
        # Update donation status
        supabase.table("item_donations").update({
            "status": "picked_up"
        }).eq("id", assignment.data[0]["donation_id"]).execute()
        
        # Update volunteer's current pickups count
        volunteer = supabase.table("volunteers").select("*")\
            .eq("user_id", current_user["id"]).execute()
        
        if volunteer.data:
            supabase.table("volunteers").update({
                "current_pickups": max(0, volunteer.data[0]["current_pickups"] - 1)
            }).eq("id", volunteer.data[0]["id"]).execute()
        
        return {"message": "Pickup completed successfully"}
        
    except Exception as e:
        print(f"Error completing pickup: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/my-pickups")
async def get_my_pickups(current_user: dict = Depends(get_current_user)):
    """Get pickups assigned to current volunteer"""
    try:
        volunteer = supabase.table("volunteers").select("*")\
            .eq("user_id", current_user["id"]).execute()
        
        if not volunteer.data:
            return []
        
        result = supabase.table("pickup_assignments").select(
            "*, item_donations!pickup_assignments_donation_id(*, campaigns(title), users(full_name, phone, address))"
        ).eq("volunteer_id", volunteer.data[0]["id"]).order("scheduled_time").execute()
        
        return result.data
        
    except Exception as e:
        print(f"Error fetching my pickups: {e}")
        return []
