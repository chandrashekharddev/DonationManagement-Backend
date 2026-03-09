from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from auth import get_current_user
from database import supabase
from schemas import Donation, ItemDonation
from datetime import datetime
import traceback

router = APIRouter(prefix="/donations", tags=["donations"])

@router.post("/money")
async def create_money_donation(
    request: dict,
    current_user: dict = Depends(get_current_user)
):
    """Create a monetary donation - accepts both JSON and form data"""
    try:
        if current_user["role"] != "user":
            raise HTTPException(status_code=403, detail="Only users can donate")
        
        # Extract data from request (works with both JSON and form data)
        campaign_id = request.get("campaign_id")
        amount = request.get("amount")
        payment_method = request.get("payment_method")
        
        # Validate required fields
        if not campaign_id:
            raise HTTPException(status_code=400, detail="campaign_id is required")
        
        if not amount:
            raise HTTPException(status_code=400, detail="amount is required")
        
        # Convert amount to float
        try:
            amount = float(amount)
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="amount must be a valid number")
        
        if amount <= 0:
            raise HTTPException(status_code=400, detail="amount must be greater than 0")
        
        # Check if campaign exists
        campaign = supabase.table("campaigns").select("*").eq("id", campaign_id).execute()
        if not campaign.data:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        # Check if campaign is active
        if campaign.data[0]["status"] != "active":
            raise HTTPException(status_code=400, detail="Can only donate to active campaigns")
        
        donation_data = {
            "user_id": current_user["id"],
            "campaign_id": campaign_id,
            "donation_type": "money",
            "amount": amount,
            "payment_method": payment_method,
            "status": "completed",
            "donated_at": datetime.utcnow().isoformat()
        }
        
        print(f"Creating money donation: {donation_data}")
        
        result = supabase.table("donations").insert(donation_data).execute()
        
        if not result.data:
            raise HTTPException(status_code=400, detail="Failed to create donation")
        
        # Update campaign raised amount
        new_amount = campaign.data[0]["raised_amount"] + amount
        supabase.table("campaigns").update({"raised_amount": new_amount})\
            .eq("id", campaign_id).execute()
        
        return {
            "message": "Donation successful",
            "donation": result.data[0]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating money donation: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

# Alternative version if you want to keep your original signature
@router.post("/money-v2")
async def create_money_donation_v2(
    campaign_id: str = Query(..., description="Campaign ID"),
    amount: float = Query(..., description="Donation amount"),
    payment_method: Optional[str] = Query(None, description="Payment method"),
    current_user: dict = Depends(get_current_user)
):
    """Create a monetary donation using query parameters"""
    try:
        if current_user["role"] != "user":
            raise HTTPException(status_code=403, detail="Only users can donate")
        
        if amount <= 0:
            raise HTTPException(status_code=400, detail="Amount must be greater than 0")
        
        # Check if campaign exists
        campaign = supabase.table("campaigns").select("*").eq("id", campaign_id).execute()
        if not campaign.data:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        if campaign.data[0]["status"] != "active":
            raise HTTPException(status_code=400, detail="Can only donate to active campaigns")
        
        donation_data = {
            "user_id": current_user["id"],
            "campaign_id": campaign_id,
            "donation_type": "money",
            "amount": amount,
            "payment_method": payment_method,
            "status": "completed",
            "donated_at": datetime.utcnow().isoformat()
        }
        
        result = supabase.table("donations").insert(donation_data).execute()
        
        if not result.data:
            raise HTTPException(status_code=400, detail="Failed to create donation")
        
        # Update campaign raised amount
        new_amount = campaign.data[0]["raised_amount"] + amount
        supabase.table("campaigns").update({"raised_amount": new_amount})\
            .eq("id", campaign_id).execute()
        
        return {"message": "Donation successful", "donation": result.data[0]}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating money donation: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

# Keep your original endpoint but make it more robust
@router.post("/money-original")
async def create_money_donation_original(
    campaign_id: str,
    amount: float,
    payment_method: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Create a monetary donation - original version"""
    try:
        if current_user["role"] != "user":
            raise HTTPException(status_code=403, detail="Only users can donate")
        
        if amount <= 0:
            raise HTTPException(status_code=400, detail="Amount must be greater than 0")
        
        # Check if campaign exists
        campaign = supabase.table("campaigns").select("*").eq("id", campaign_id).execute()
        if not campaign.data:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        if campaign.data[0]["status"] != "active":
            raise HTTPException(status_code=400, detail="Can only donate to active campaigns")
        
        donation_data = {
            "user_id": current_user["id"],
            "campaign_id": campaign_id,
            "donation_type": "money",
            "amount": amount,
            "payment_method": payment_method,
            "status": "completed",
            "donated_at": datetime.utcnow().isoformat()
        }
        
        print(f"Creating money donation: {donation_data}")
        
        result = supabase.table("donations").insert(donation_data).execute()
        
        if not result.data:
            raise HTTPException(status_code=400, detail="Failed to create donation")
        
        # Update campaign raised amount
        new_amount = campaign.data[0]["raised_amount"] + amount
        supabase.table("campaigns").update({"raised_amount": new_amount})\
            .eq("id", campaign_id).execute()
        
        return {"message": "Donation successful", "donation": result.data[0]}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating money donation: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
