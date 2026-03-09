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
        
        if not result.data:
            raise HTTPException(status_code=400, detail="Failed to create donation")
        
        # Update campaign raised amount
        campaign = supabase.table("campaigns").select("raised_amount")\
            .eq("id", campaign_id).execute()
        
        if campaign.data:
            new_amount = campaign.data[0]["raised_amount"] + amount
            supabase.table("campaigns").update({"raised_amount": new_amount})\
                .eq("id", campaign_id).execute()
        
        return {"message": "Donation successful", "data": result.data[0]}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating money donation: {e}")
        print(traceback.format_exc())
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
            "amount": 0,  # Add amount field
            "status": "pending" if delivery_method == "pickup" else "completed",
            "donated_at": datetime.utcnow().isoformat()
        }
        
        donation_result = supabase.table("donations").insert(donation_data).execute()
        
        if not donation_result.data:
            raise HTTPException(status_code=400, detail="Failed to create donation")
            
        donation_id = donation_result.data[0]["id"]
        
        # Check if item_donations table exists, if not, just update campaign
        try:
            # Create item donation records
            for item in items:
                item_data = {
                    "user_id": current_user["id"],
                    "campaign_id": campaign_id,
                    "donation_id": donation_id,
                    "item_name": item["name"],
                    "quantity": item["quantity"],
                    "unit": item.get("unit", "pieces"),
                    "condition": item.get("condition", "new"),
                    "delivery_method": delivery_method,
                    "pickup_address": pickup_address if delivery_method == "pickup" else None,
                    "status": "pending" if delivery_method == "pickup" else "delivered",
                    "notes": notes,
                    "created_at": datetime.utcnow().isoformat()
                }
                
                supabase.table("item_donations").insert(item_data).execute()
        except Exception as e:
            print(f"Note: item_donations table might not exist yet: {e}")
        
        # Update campaign collected items
        campaign = supabase.table("campaigns").select("collected_items")\
            .eq("id", campaign_id).execute()
        
        if campaign.data:
            collected = campaign.data[0].get("collected_items", [])
            for item in items:
                collected.append({
                    "item_name": item["name"],
                    "quantity": item["quantity"],
                    "unit": item.get("unit", "pieces"),
                    "donated_by": current_user["id"],
                    "donated_at": datetime.utcnow().isoformat()
                })
            
            supabase.table("campaigns").update({"collected_items": collected})\
                .eq("id", campaign_id).execute()
        
        message = "Donation recorded successfully"
        if delivery_method == "pickup":
            message += ". A volunteer will contact you for pickup."
        
        return {"message": message, "donation_id": donation_id}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating item donation: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user")
async def get_user_donations(current_user: dict = Depends(get_current_user)):
    """Get user's donation history"""
    try:
        # Get money donations - FIX: Remove joins, fetch separately
        money_result = supabase.table("donations").select("*")\
            .eq("user_id", current_user["id"])\
            .eq("donation_type", "money")\
            .order("donated_at", desc=True).execute()
        
        money_donations = []
        for d in money_result.data or []:
            # Get campaign title separately
            campaign = supabase.table("campaigns").select("title")\
                .eq("id", d["campaign_id"]).execute()
            d["campaigns"] = {"title": campaign.data[0]["title"] if campaign.data else "Unknown"}
            money_donations.append(d)
        
        # Get item donations
        try:
            item_result = supabase.table("item_donations").select("*")\
                .eq("user_id", current_user["id"])\
                .order("created_at", desc=True).execute()
            
            item_donations = []
            for d in item_result.data or []:
                campaign = supabase.table("campaigns").select("title")\
                    .eq("id", d["campaign_id"]).execute()
                d["campaigns"] = {"title": campaign.data[0]["title"] if campaign.data else "Unknown"}
                item_donations.append(d)
        except:
            item_donations = []
        
        return {
            "money_donations": money_donations,
            "item_donations": item_donations
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
            money = supabase.table("donations").select("*")\
                .eq("campaign_id", campaign_id)\
                .eq("donation_type", "money")\
                .order("donated_at", desc=True).execute()
            
            # Add user details manually
            money_donations = []
            for d in money.data or []:
                user = supabase.table("users").select("full_name, email, phone")\
                    .eq("id", d["user_id"]).execute()
                if user.data:
                    d["users"] = user.data[0]
                money_donations.append(d)
            
            result["money_donations"] = money_donations
        
        if not donation_type or donation_type == "items":
            try:
                items = supabase.table("item_donations").select("*")\
                    .eq("campaign_id", campaign_id)\
                    .order("created_at", desc=True).execute()
                
                # Add user details manually
                item_donations = []
                for d in items.data or []:
                    user = supabase.table("users").select("full_name, phone, address")\
                        .eq("id", d["user_id"]).execute()
                    if user.data:
                        d["users"] = user.data[0]
                    item_donations.append(d)
                
                result["item_donations"] = item_donations
            except:
                result["item_donations"] = []
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching campaign donations: {e}")
        print(traceback.format_exc())
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
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Item donation not found")
        
        return {"message": f"Status updated to {status}", "data": result.data[0]}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating donation status: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
