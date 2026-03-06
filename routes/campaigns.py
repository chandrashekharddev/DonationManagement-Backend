from fastapi import APIRouter, HTTPException, Depends
from typing import List
from schemas import CampaignCreate, CampaignResponse
from auth import get_current_user
from database import supabase

router = APIRouter(prefix="/campaigns", tags=["campaigns"])

@router.get("/", response_model=List[CampaignResponse])
async def get_campaigns(status: str = None):
    query = supabase.table("campaigns").select("*, users!campaigns_ngo_id(full_name)")
    if status:
        query = query.eq("status", status)
    
    result = query.execute()
    
    campaigns = []
    for item in result.data:
        campaigns.append({
            **item,
            "ngo_name": item["users"]["full_name"] if item.get("users") else None
        })
    
    return campaigns

@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(campaign_id: str):
    result = supabase.table("campaigns").select("*, users!campaigns_ngo_id(full_name)").eq("id", campaign_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    campaign = result.data[0]
    campaign["ngo_name"] = campaign["users"]["full_name"] if campaign.get("users") else None
    return campaign

@router.post("/", response_model=CampaignResponse)
async def create_campaign(campaign: CampaignCreate, user=Depends(get_current_user)):
    if user["role"] != "ngo":
        raise HTTPException(status_code=403, detail="Only NGOs can create campaigns")
    
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
    
    return result.data[0]

@router.put("/{campaign_id}/approve")
async def approve_campaign(campaign_id: str, user=Depends(get_current_user)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can approve campaigns")
    
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
    
    return {"message": "Campaign approved"}