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
        
        if not result.data:
            raise HTTPException(status_code=400, detail="Failed to create campaign")
        
        # Get the created campaign with NGO name
        created_campaign = result.data[0]
        
        # Add NGO name
        ngo = supabase.table("users").select("full_name").eq("id", current_user["id"]).execute()
        if ngo.data:
            created_campaign["ngo_name"] = ngo.data[0]["full_name"]
        
        return created_campaign
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating campaign: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/")
async def get_campaigns(
    status: Optional[str] = None,
    category: Optional[str] = None,
    campaign_type: Optional[str] = None
):
    """Get campaigns with filters"""
    try:
        # Build query
        query = supabase.table("campaigns").select("*")
        
        # Apply filters
        if status:
            query = query.eq("status", status)
        if category:
            query = query.eq("category", category)
        if campaign_type:
            query = query.eq("campaign_type", campaign_type)
        
        # Execute query
        result = query.order("created_at", desc=True).execute()
        
        # Manually add NGO names
        campaigns = result.data if result.data else []
        
        for campaign in campaigns:
            try:
                # Get NGO details
                ngo = supabase.table("users").select("full_name, phone, email")\
                    .eq("id", campaign["ngo_id"]).execute()
                if ngo.data:
                    campaign["ngo_name"] = ngo.data[0]["full_name"]
                    campaign["ngo_phone"] = ngo.data[0].get("phone")
                    campaign["ngo_email"] = ngo.data[0].get("email")
                else:
                    campaign["ngo_name"] = "Unknown NGO"
            except Exception as e:
                print(f"Error fetching NGO details for campaign {campaign.get('id')}: {e}")
                campaign["ngo_name"] = "Unknown NGO"
        
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
        try:
            ngo = supabase.table("users").select("full_name").eq("id", ngo_id).execute()
            ngo_name = ngo.data[0]["full_name"] if ngo.data else "NGO"
        except:
            ngo_name = "NGO"
        
        for campaign in campaigns:
            campaign["ngo_name"] = ngo_name
            
            # Calculate item progress if needed
            if campaign.get("required_items"):
                total_items = len(campaign["required_items"])
                collected_items = sum(1 for item in campaign["required_items"] if item.get("quantity_collected", 0) >= item.get("quantity_needed", 1))
                campaign["items_progress"] = (collected_items / total_items * 100) if total_items > 0 else 0
        
        return campaigns
        
    except Exception as e:
        print(f"Error fetching NGO campaigns: {e}")
        print(traceback.format_exc())
        return []

@router.get("/{campaign_id}")
async def get_campaign(campaign_id: str):
    """Get single campaign details"""
    try:
        result = supabase.table("campaigns").select("*")\
            .eq("id", campaign_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        campaign = result.data[0]
        
        # Add NGO details
        try:
            ngo = supabase.table("users").select("full_name, phone, email, address")\
                .eq("id", campaign["ngo_id"]).execute()
            if ngo.data:
                campaign["ngo_name"] = ngo.data[0]["full_name"]
                campaign["ngo_phone"] = ngo.data[0].get("phone")
                campaign["ngo_email"] = ngo.data[0].get("email")
                campaign["ngo_address"] = ngo.data[0].get("address")
        except Exception as e:
            print(f"Error fetching NGO details: {e}")
            campaign["ngo_name"] = "Unknown NGO"
        
        return campaign
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching campaign: {e}")
        print(traceback.format_exc())
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
        
        if not result.data:
            raise HTTPException(status_code=400, detail="Failed to activate campaign")
        
        activated_campaign = result.data[0]
        
        # Add NGO name
        ngo = supabase.table("users").select("full_name").eq("id", current_user["id"]).execute()
        if ngo.data:
            activated_campaign["ngo_name"] = ngo.data[0]["full_name"]
        
        return {
            "message": "Campaign activated successfully",
            "campaign": activated_campaign
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error activating campaign: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{campaign_id}/deactivate")
async def deactivate_campaign(
    campaign_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Deactivate a campaign (NGO or Admin only)"""
    try:
        if current_user["role"] not in ["ngo", "admin"]:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        # Verify ownership for NGOs
        if current_user["role"] == "ngo":
            campaign = supabase.table("campaigns").select("*")\
                .eq("id", campaign_id).execute()
            
            if not campaign.data:
                raise HTTPException(status_code=404, detail="Campaign not found")
            
            if campaign.data[0]["ngo_id"] != current_user["id"]:
                raise HTTPException(status_code=403, detail="Not authorized")
        
        # Update status to inactive/completed
        result = supabase.table("campaigns").update({"status": "completed"})\
            .eq("id", campaign_id).execute()
        
        return {
            "message": "Campaign deactivated successfully",
            "campaign": result.data[0] if result.data else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deactivating campaign: {e}")
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
        
        # Remove fields that shouldn't be updated
        allowed_updates = {}
        for key in ["title", "description", "category", "goal_amount", "required_items", 
                   "pickup_required", "pickup_address", "image_url"]:
            if key in campaign_data:
                allowed_updates[key] = campaign_data[key]
        
        if not allowed_updates:
            raise HTTPException(status_code=400, detail="No valid fields to update")
        
        result = supabase.table("campaigns").update(allowed_updates)\
            .eq("id", campaign_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=400, detail="Failed to update campaign")
        
        return result.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating campaign: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{campaign_id}")
async def delete_campaign(
    campaign_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a campaign (Admin only)"""
    try:
        if current_user["role"] != "admin":
            raise HTTPException(status_code=403, detail="Only admins can delete campaigns")
        
        result = supabase.table("campaigns").delete()\
            .eq("id", campaign_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        return {"message": "Campaign deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Test endpoint to check campaigns
@router.get("/test/all")
async def test_all_campaigns():
    """Test endpoint to see all campaigns"""
    try:
        # Get all campaigns
        result = supabase.table("campaigns").select("*").execute()
        campaigns = result.data if result.data else []
        
        # Get counts by status
        active = supabase.table("campaigns").select("*", count="exact").eq("status", "active").execute()
        pending = supabase.table("campaigns").select("*", count="exact").eq("status", "pending").execute()
        completed = supabase.table("campaigns").select("*", count="exact").eq("status", "completed").execute()
        
        # Add NGO names to each campaign
        for campaign in campaigns:
            try:
                ngo = supabase.table("users").select("full_name").eq("id", campaign["ngo_id"]).execute()
                if ngo.data:
                    campaign["ngo_name"] = ngo.data[0]["full_name"]
            except:
                campaign["ngo_name"] = "Unknown"
        
        return {
            "total_campaigns": len(campaigns),
            "active_campaigns": active.count if hasattr(active, 'count') else len(active.data),
            "pending_campaigns": pending.count if hasattr(pending, 'count') else len(pending.data),
            "completed_campaigns": completed.count if hasattr(completed, 'count') else len(completed.data),
            "campaigns": campaigns
        }
    except Exception as e:
        return {
            "error": str(e),
            "traceback": traceback.format_exc()
        }

# Get campaign statistics
@router.get("/stats/overview")
async def get_campaign_stats():
    """Get overview statistics of all campaigns"""
    try:
        # Get all campaigns
        result = supabase.table("campaigns").select("*").execute()
        campaigns = result.data if result.data else []
        
        total_goal = sum(c.get("goal_amount", 0) for c in campaigns)
        total_raised = sum(c.get("raised_amount", 0) for c in campaigns)
        
        # Count by category
        categories = {}
        for c in campaigns:
            cat = c.get("category", "Other")
            categories[cat] = categories.get(cat, 0) + 1
        
        return {
            "total_campaigns": len(campaigns),
            "total_goal_amount": total_goal,
            "total_raised_amount": total_raised,
            "overall_progress": (total_raised / total_goal * 100) if total_goal > 0 else 0,
            "campaigns_by_category": categories,
            "active_count": len([c for c in campaigns if c.get("status") == "active"]),
            "pending_count": len([c for c in campaigns if c.get("status") == "pending"]),
            "completed_count": len([c for c in campaigns if c.get("status") == "completed"])
        }
    except Exception as e:
        print(f"Error getting campaign stats: {e}")
        return {"error": str(e)}
