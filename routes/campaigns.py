from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from database import supabase
from schemas import CampaignCreate, CampaignResponse
from auth import get_current_user
import traceback

router = APIRouter(prefix="/campaigns", tags=["campaigns"])

@router.get("/", response_model=List[CampaignResponse])
async def get_campaigns(status: Optional[str] = None):
    """Get all campaigns with optional status filter"""
    try:
        print(f"Fetching campaigns with status: {status}")
        
        # Check if supabase is connected
        if supabase is None:
            print("❌ Supabase client not initialized")
            return []
        
        # Build query
        query = supabase.table("campaigns").select("*")
        if status:
            query = query.eq("status", status)
        
        # Execute query
        result = query.execute()
        print(f"✅ Found {len(result.data)} campaigns")
        
        # Transform data to match response model
        campaigns = []
        for item in result.data:
            # Get NGO name separately if needed
            ngo_name = "Unknown NGO"
            if item.get("ngo_id"):
                try:
                    ngo_result = supabase.table("users").select("full_name").eq("id", item["ngo_id"]).execute()
                    if ngo_result.data:
                        ngo_name = ngo_result.data[0].get("full_name", "Unknown NGO")
                except Exception as e:
                    print(f"Error fetching NGO name: {e}")
            
            campaigns.append({
                "id": item.get("id"),
                "ngo_id": item.get("ngo_id"),
                "ngo_name": ngo_name,
                "title": item.get("title", ""),
                "description": item.get("description", ""),
                "category": item.get("category", "Other"),
                "goal_amount": float(item.get("goal_amount", 0)),
                "raised_amount": float(item.get("raised_amount", 0)),
                "status": item.get("status", "pending"),
                "image_url": item.get("image_url", ""),
                "created_at": item.get("created_at")
            })
        
        return campaigns
        
    except Exception as e:
        print(f"❌ Error in get_campaigns: {str(e)}")
        print(traceback.format_exc())
        # Return empty list instead of throwing error
        return []

@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(campaign_id: str):
    """Get a single campaign by ID"""
    try:
        print(f"Fetching campaign with ID: {campaign_id}")
        
        result = supabase.table("campaigns").select("*").eq("id", campaign_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        campaign = result.data[0]
        
        # Get NGO name
        ngo_name = "Unknown NGO"
        if campaign.get("ngo_id"):
            try:
                ngo_result = supabase.table("users").select("full_name").eq("id", campaign["ngo_id"]).execute()
                if ngo_result.data:
                    ngo_name = ngo_result.data[0].get("full_name", "Unknown NGO")
            except Exception as e:
                print(f"Error fetching NGO name: {e}")
        
        return {
            "id": campaign.get("id"),
            "ngo_id": campaign.get("ngo_id"),
            "ngo_name": ngo_name,
            "title": campaign.get("title", ""),
            "description": campaign.get("description", ""),
            "category": campaign.get("category", "Other"),
            "goal_amount": float(campaign.get("goal_amount", 0)),
            "raised_amount": float(campaign.get("raised_amount", 0)),
            "status": campaign.get("status", "pending"),
            "image_url": campaign.get("image_url", ""),
            "created_at": campaign.get("created_at")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in get_campaign: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/", response_model=CampaignResponse)
async def create_campaign(campaign: CampaignCreate, user=Depends(get_current_user)):
    """Create a new campaign (NGO only)"""
    try:
        if user["role"] != "ngo":
            raise HTTPException(status_code=403, detail="Only NGOs can create campaigns")
        
        print(f"Creating campaign for NGO: {user['id']}")
        
        result = supabase.table("campaigns").insert({
            "ngo_id": user["id"],
            "title": campaign.title,
            "description": campaign.description,
            "category": campaign.category,
            "goal_amount": campaign.goal_amount,
            "end_date": str(campaign.end_date) if campaign.end_date else None,
            "image_url": campaign.image_url,
            "status": "pending"
        }).execute()
        
        if not result.data:
            raise HTTPException(status_code=400, detail="Campaign creation failed")
        
        new_campaign = result.data[0]
        
        return {
            "id": new_campaign.get("id"),
            "ngo_id": new_campaign.get("ngo_id"),
            "ngo_name": user.get("full_name"),
            "title": new_campaign.get("title"),
            "description": new_campaign.get("description"),
            "category": new_campaign.get("category"),
            "goal_amount": float(new_campaign.get("goal_amount", 0)),
            "raised_amount": float(new_campaign.get("raised_amount", 0)),
            "status": new_campaign.get("status"),
            "image_url": new_campaign.get("image_url"),
            "created_at": new_campaign.get("created_at")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in create_campaign: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.put("/{campaign_id}/approve")
async def approve_campaign(campaign_id: str, user=Depends(get_current_user)):
    """Approve a campaign (Admin only)"""
    try:
        if user["role"] != "admin":
            raise HTTPException(status_code=403, detail="Only admins can approve campaigns")
        
        print(f"Approving campaign: {campaign_id}")
        
        result = supabase.table("campaigns").update({"status": "active"}).eq("id", campaign_id).execute()
        
        # Create notification for NGO
        campaign = supabase.table("campaigns").select("*").eq("id", campaign_id).execute()
        if campaign.data:
            supabase.table("notifications").insert({
                "user_id": campaign.data[0]["ngo_id"],
                "title": "Campaign Approved",
                "message": f"Your campaign '{campaign.data[0]['title']}' has been approved!",
                "type": "approval"
            }).execute()
        
        return {"message": "Campaign approved successfully"}
        
    except Exception as e:
        print(f"❌ Error in approve_campaign: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
