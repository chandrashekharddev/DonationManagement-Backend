from fastapi import APIRouter, Depends
from typing import List
from schemas import UserResponse, DashboardStats, DonationResponse, CampaignResponse, NotificationResponse
from auth import get_current_user
from database import supabase

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(user=Depends(get_current_user)):
    return user

@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(user=Depends(get_current_user)):
    stats = {}
    
    if user["role"] == "admin":
        # Admin stats
        users = supabase.table("users").select("*", count="exact").execute()
        ngos = supabase.table("users").select("*", count="exact").eq("role", "ngo").execute()
        campaigns = supabase.table("campaigns").select("*", count="exact").execute()
        donations = supabase.table("donations").select("amount").execute()
        
        total_donations = sum(d["amount"] for d in donations.data) if donations.data else 0
        
        stats = {
            "total_users": users.count,
            "total_ngos": ngos.count,
            "total_campaigns": campaigns.count,
            "total_donations": total_donations,
            "active_campaigns": campaigns.count
        }
    
    elif user["role"] == "ngo":
        # NGO stats
        campaigns = supabase.table("campaigns").select("*", count="exact").eq("ngo_id", user["id"]).execute()
        donations = supabase.table("donations").select("amount, campaigns!donations_campaign_id(*)").eq("campaigns.ngo_id", user["id"]).execute()
        
        total_donations = sum(d["amount"] for d in donations.data) if donations.data else 0
        
        stats = {
            "total_campaigns": campaigns.count,
            "active_campaigns": len([c for c in campaigns.data if c["status"] == "active"]),
            "total_donations": total_donations,
            "total_supporters": len(set(d["user_id"] for d in donations.data)) if donations.data else 0
        }
    
    else:  # user
        # User stats
        donations = supabase.table("donations").select("*", count="exact").eq("user_id", user["id"]).execute()
        total_amount = sum(d["amount"] for d in donations.data) if donations.data else 0
        
        # Get supported NGOs count
        supported_ngos = supabase.table("donations").select("campaigns!donations_campaign_id(ngo_id)").eq("user_id", user["id"]).execute()
        unique_ngos = set()
        if supported_ngos.data:
            for d in supported_ngos.data:
                if d.get("campaigns") and d["campaigns"].get("ngo_id"):
                    unique_ngos.add(d["campaigns"]["ngo_id"])
        
        stats = {
            "total_donations": donations.count,
            "total_amount": total_amount,
            "supported_ngos": len(unique_ngos)
        }
    
    # Get recent donations
    recent_donations = supabase.table("donations").select("*, users(full_name), campaigns(title)").order("donated_at", desc=True).limit(5).execute()
    
    # Get recent campaigns
    recent_campaigns = supabase.table("campaigns").select("*, users!campaigns_ngo_id(full_name)").order("created_at", desc=True).limit(5).execute()
    
    return {
        **stats,
        "recent_donations": recent_donations.data,
        "recent_campaigns": recent_campaigns.data
    }

@router.get("/notifications", response_model=List[NotificationResponse])
async def get_notifications(user=Depends(get_current_user)):
    result = supabase.table("notifications").select("*").eq("user_id", user["id"]).order("created_at", desc=True).execute()
    return result.data

@router.put("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str, user=Depends(get_current_user)):
    supabase.table("notifications").update({"read": True}).eq("id", notification_id).eq("user_id", user["id"]).execute()
    return {"message": "Notification marked as read"}