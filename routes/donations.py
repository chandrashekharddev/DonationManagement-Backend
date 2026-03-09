from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from auth import get_current_user
from database import supabase
from schemas import Donation, ItemDonation
from datetime import datetime
import traceback

router = APIRouter(prefix="/donations", tags=["donations"])

@router.post("/money")
async def create_money_donation(
    campaign_id: str,
    amount: float,
    payment_method: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Create a monetary donation"""
    try:
        if current_user["role"] != "user":
            raise HTTPException(status_code=403, detail="Only users can donate")
        
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
        
        # Update campaign raised amount
        campaign = supabase.table("campaigns").select("raised_amount")\
            .eq("id", campaign_id).execute()
        
        if campaign.data:
            new_amount = campaign.data[0]["raised_amount"] + amount
            supabase.table("campaigns").update({"raised_amount": new_amount})\
                .eq("id", campaign_id).execute()
        
        return {"message": "Donation successful", "data": result.data[0]}
        
    except Exception as e:
        print(f"Error creating money donation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/items")
async def create_item_donation(
    campaign_id: str,
    items: List[dict],
    delivery_method: str = "dropoff",
    pickup_address: Optional[str] = None,
    notes: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Create an in-kind donation"""
    try:
        if current_user["role"] != "user":
            raise HTTPException(status_code=403, detail="Only users can donate")
        
        # Create main donation record
        donation_data = {
            "user_id": current_user["id"],
            "campaign_id": campaign_id,
            "donation_type": "items",
            "items": items,
            "status": "pending" if delivery_method == "pickup" else "completed",
            "donated_at": datetime.utcnow().isoformat()
        }
        
        donation_result = supabase.table("donations").insert(donation_data).execute()
        donation_id = donation_result.data[0]["id"]
        
        # Create item donation records
        for item in items:
            item_data = {
                "user_id": current_user["id"],
                "campaign_id": campaign_id,
                "donation_id": donation_id,
                "item_name": item["name"],
                "quantity": item["quantity"],
                "unit": item["unit"],
                "condition": item.get("condition", "new"),
                "delivery_method": delivery_method,
                "pickup_address": pickup_address if delivery_method == "pickup" else None,
                "status": "pending" if delivery_method == "pickup" else "delivered",
                "notes": notes,
                "created_at": datetime.utcnow().isoformat()
            }
            
            supabase.table("item_donations").insert(item_data).execute()
            
            # Update campaign collected items
            campaign = supabase.table("campaigns").select("collected_items")\
                .eq("id", campaign_id).execute()
            
            if campaign.data:
                collected = campaign.data[0].get("collected_items", [])
                collected.append({
                    "item_name": item["name"],
                    "quantity": item["quantity"],
                    "unit": item["unit"],
                    "donated_by": current_user["id"],
                    "donated_at": datetime.utcnow().isoformat()
                })
                
                supabase.table("campaigns").update({"collected_items": collected})\
                    .eq("id", campaign_id).execute()
        
        message = "Donation recorded successfully"
        if delivery_method == "pickup":
            message += ". A volunteer will contact you for pickup."
        
        return {"message": message, "donation_id": donation_id}
        
    except Exception as e:
        print(f"Error creating item donation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user")
async def get_user_donations(current_user: dict = Depends(get_current_user)):
    """Get user's donation history"""
    try:
        # Get money donations
        money_donations = supabase.table("donations").select(
            "*, campaigns(title)"
        ).eq("user_id", current_user["id"]).eq("donation_type", "money")\
        .order("donated_at", desc=True).execute()
        
        # Get item donations
        item_donations = supabase.table("item_donations").select(
            "*, campaigns(title)"
        ).eq("user_id", current_user["id"])\
        .order("created_at", desc=True).execute()
        
        return {
            "money_donations": money_donations.data,
            "item_donations": item_donations.data
        }
        
    except Exception as e:
        print(f"Error fetching user donations: {e}")
        return {"money_donations": [], "item_donations": []}

@router.get("/campaign/{campaign_id}")
async def get_campaign_donations(
    campaign_id: str,
    donation_type: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get donations for a campaign (NGO only)"""
    try:
        if current_user["role"] != "ngo":
            raise HTTPException(status_code=403, detail="Only NGOs can view campaign donations")
        
        # Verify campaign ownership
        campaign = supabase.table("campaigns").select("ngo_id")\
            .eq("id", campaign_id).execute()
        
        if not campaign.data or campaign.data[0]["ngo_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        result = {}
        
        if not donation_type or donation_type == "money":
            money = supabase.table("donations").select(
                "*, users(full_name, email, phone)"
            ).eq("campaign_id", campaign_id).eq("donation_type", "money")\
            .order("donated_at", desc=True).execute()
            result["money_donations"] = money.data
        
        if not donation_type or donation_type == "items":
            items = supabase.table("item_donations").select(
                "*, users(full_name, phone, address)"
            ).eq("campaign_id", campaign_id)\
            .order("created_at", desc=True).execute()
            result["item_donations"] = items.data
        
        return result
        
    except Exception as e:
        print(f"Error fetching campaign donations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/item/{item_donation_id}/status")
async def update_item_donation_status(
    item_donation_id: str,
    status: str,
    volunteer_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Update item donation status (NGO or Volunteer)"""
    try:
        update_data = {"status": status}
        
        if status == "picked_up" and volunteer_id:
            update_data["volunteer_id"] = volunteer_id
        
        result = supabase.table("item_donations").update(update_data)\
            .eq("id", item_donation_id).execute()
        
        return {"message": f"Status updated to {status}", "data": result.data[0]}
        
    except Exception as e:
        print(f"Error updating donation status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
