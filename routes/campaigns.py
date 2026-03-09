from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from auth import get_current_user
from database import supabase
from schemas import Campaign
from datetime import datetime
import traceback

router = APIRouter(prefix="/campaigns", tags=["campaigns"])

@router.post("/")
async def create_campaign(campaign: Campaign, current_user: dict = Depends(get_current_user)):
    """Create a new campaign (NGO only)"""
    try:
        if current_user["role"] != "ngo":
            raise HTTPException(status_code=403, detail="Only NGOs can create campaigns")
        
        campaign_data = {
            "ngo_id": current_user["id"],
            "title": campaign.title,
            "description": campaign.description,
            "category": campaign.category,
            "campaign_type": campaign.campaign_type,
            "goal_amount": campaign.goal_amount or 0,
            "required_items": campaign.required_items or [],
            "collected_items": [],
            "pickup_required": campaign.pickup_required,
            "pickup_address": campaign.pickup_address,
            "status": "pending",
            "created_at": datetime.utcnow().isoformat()
        }
        
        result = supabase.table("campaigns").insert(campaign_data).execute()
        
        return result.data[0]
        
    except Exception as e:
        print(f"Error creating campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/")
async def get_campaigns(
    status: Optional[str] = None,
    category: Optional[str] = None,
    campaign_type: Optional[str] = None
):
    """Get campaigns with filters"""
    try:
        # FIX: Remove the join that's causing the error
        query = supabase.table("campaigns").select("*")
        
        if status:
            query = query.eq("status", status)
        if category:
            query = query.eq("category", category)
        if campaign_type:
            query = query.eq("campaign_type", campaign_type)
        
        result = query.order("created_at", desc=True).execute()
        
        # Manually add NGO names
        campaigns = result.data if result.data else []
        for campaign in campaigns:
            # Get NGO details
            ngo = supabase.table("users").select("full_name, phone, email")\
                .eq("id", campaign["ngo_id"]).execute()
            if ngo.data:
                campaign["ngo_name"] = ngo.data[0]["full_name"]
                campaign["ngo_phone"] = ngo.data[0].get("phone")
                campaign["ngo_email"] = ngo.data[0].get("email")
        
        return campaigns
        
    except Exception as e:
        print(f"Error fetching campaigns: {e}")
        print(traceback.format_exc())
        return []

@router.get("/ngo/{ngo_id}")
async def get_ngo_campaigns(ngo_id: str):
    """Get campaigns for a specific NGO"""
    try:
        result = supabase.table("campaigns").select("*")\
            .eq("ngo_id", ngo_id)\
            .order("created_at", desc=True).execute()
        
        campaigns = result.data if result.data else []
        
        # Add NGO name
        ngo = supabase.table("users").select("full_name").eq("id", ngo_id).execute()
        ngo_name = ngo.data[0]["full_name"] if ngo.data else "NGO"
        
        for campaign in campaigns:
            campaign["ngo_name"] = ngo_name
        
        return campaigns
        
    except Exception as e:
        print(f"Error fetching NGO campaigns: {e}")
        return []

@router.get("/{campaign_id}")
async def get_campaign(campaign_id: str):
    """Get single campaign details"""
    try:
        # FIX: Remove the join
        result = supabase.table("campaigns").select("*")\
            .eq("id", campaign_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        campaign = result.data[0]
        
        # Add NGO details
        ngo = supabase.table("users").select("full_name, phone, email, address")\
            .eq("id", campaign["ngo_id"]).execute()
        if ngo.data:
            campaign["ngo_name"] = ngo.data[0]["full_name"]
            campaign["ngo_phone"] = ngo.data[0].get("phone")
            campaign["ngo_email"] = ngo.data[0].get("email")
            campaign["ngo_address"] = ngo.data[0].get("address")
        
        return campaign
        
    except Exception as e:
        print(f"Error fetching campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{campaign_id}/activate")
async def activate_campaign(
    campaign_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Activate a campaign (NGO only)"""
    try:
        if current_user["role"] != "ngo":
            raise HTTPException(status_code=403, detail="Only NGOs can activate campaigns")
        
        # Verify ownership
        campaign = supabase.table("campaigns").select("*")\
            .eq("id", campaign_id).execute()
        
        if not campaign.data:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        if campaign.data[0]["ngo_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        # Update status to active
        result = supabase.table("campaigns").update({"status": "active"})\
            .eq("id", campaign_id).execute()
        
        return {
            "message": "Campaign activated successfully",
            "campaign": result.data[0]
        }
        
    except Exception as e:
        print(f"Error activating campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))
        
@router.put("/{campaign_id}")
async def update_campaign(
    campaign_id: str,
    campaign_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Update campaign (NGO only)"""
    try:
        # Verify ownership
        campaign = supabase.table("campaigns").select("*")\
            .eq("id", campaign_id).execute()
        
        if not campaign.data:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        if campaign.data[0]["ngo_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        result = supabase.table("campaigns").update(campaign_data)\
            .eq("id", campaign_id).execute()
        
        return result.data[0]
        
    except Exception as e:
        print(f"Error updating campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Add a test endpoint to check campaigns
@router.get("/test/all")
async def test_all_campaigns():
    """Test endpoint to see all campaigns"""
    try:
        # Get all campaigns
        result = supabase.table("campaigns").select("*").execute()
        
        # Get counts by status
        active = supabase.table("campaigns").select("*", count="exact").eq("status", "active").execute()
        pending = supabase.table("campaigns").select("*", count="exact").eq("status", "pending").execute()
        
        return {
            "total_campaigns": len(result.data) if result.data else 0,
            "active_campaigns": active.count if hasattr(active, 'count') else len(active.data),
            "pending_campaigns": pending.count if hasattr(pending, 'count') else len(pending.data),
            "campaigns": result.data
        }
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}
