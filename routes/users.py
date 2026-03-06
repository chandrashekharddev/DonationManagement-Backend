from fastapi import APIRouter, Depends, HTTPException
from typing import List, Any
from schemas import UserResponse, DonationResponse, CampaignResponse, NotificationResponse
from auth import get_current_user
from database import supabase
from datetime import datetime
import traceback

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(user: dict = Depends(get_current_user)):
    """Get current user information"""
    return user

@router.get("/dashboard")
async def get_dashboard_stats(user: dict = Depends(get_current_user)):
    """Get dashboard statistics based on user role"""
    try:
        print(f"Fetching dashboard for user: {user['username']} with role: {user['role']}")
        
        stats = {}
        
        if user["role"] == "admin":
            # Admin stats
            users_result = supabase.table("users").select("*", count="exact").execute()
            ngos_result = supabase.table("users").select("*", count="exact").eq("role", "ngo").execute()
            campaigns_result = supabase.table("campaigns").select("*", count="exact").execute()
            donations_result = supabase.table("donations").select("amount").execute()
            
            total_donations = sum(float(d["amount"]) for d in donations_result.data) if donations_result.data else 0
            active_campaigns = len([c for c in campaigns_result.data if c.get("status") == "active"]) if campaigns_result.data else 0
            pending_campaigns = len([c for c in campaigns_result.data if c.get("status") == "pending"]) if campaigns_result.data else 0
            
            stats = {
                "total_users": users_result.count if hasattr(users_result, 'count') else len(users_result.data),
                "total_ngos": ngos_result.count if hasattr(ngos_result, 'count') else len(ngos_result.data),
                "total_campaigns": campaigns_result.count if hasattr(campaigns_result, 'count') else len(campaigns_result.data),
                "total_donations": float(total_donations),
                "active_campaigns": active_campaigns,
                "pending_campaigns": pending_campaigns
            }
        
        elif user["role"] == "ngo":
            # NGO stats
            campaigns_result = supabase.table("campaigns").select("*").eq("ngo_id", user["id"]).execute()
            campaigns = campaigns_result.data if campaigns_result.data else []
            
            # Get donations for NGO's campaigns
            campaign_ids = [c["id"] for c in campaigns]
            total_donations = 0
            supporters = set()
            
            if campaign_ids:
                donations_result = supabase.table("donations").select("amount, user_id").in_("campaign_id", campaign_ids).execute()
                if donations_result.data:
                    total_donations = sum(float(d["amount"]) for d in donations_result.data)
                    supporters = set(d["user_id"] for d in donations_result.data if d.get("user_id"))
            
            stats = {
                "total_campaigns": len(campaigns),
                "active_campaigns": len([c for c in campaigns if c.get("status") == "active"]),
                "total_donations": float(total_donations),
                "total_supporters": len(supporters)
            }
        
        else:  # user
            # User stats
            donations_result = supabase.table("donations").select("*").eq("user_id", user["id"]).execute()
            donations = donations_result.data if donations_result.data else []
            
            total_amount = sum(float(d["amount"]) for d in donations) if donations else 0
            
            # Get unique NGOs supported
            supported_ngos = set()
            for d in donations:
                if d.get("campaign_id"):
                    campaign_result = supabase.table("campaigns").select("ngo_id").eq("id", d["campaign_id"]).execute()
                    if campaign_result.data and campaign_result.data[0].get("ngo_id"):
                        supported_ngos.add(campaign_result.data[0]["ngo_id"])
            
            stats = {
                "total_donations": len(donations),
                "total_amount": float(total_amount),
                "supported_ngos": len(supported_ngos)
            }
        
        # Get recent donations (last 5)
        recent_donations = []
        try:
            donations_query = supabase.table("donations").select("*, users!donations_user_id(full_name), campaigns!donations_campaign_id(title)").order("donated_at", desc=True).limit(5).execute()
            if donations_query.data:
                recent_donations = [
                    {
                        "id": d.get("id"),
                        "user_id": d.get("user_id"),
                        "user_name": d.get("users", {}).get("full_name") if d.get("users") else None,
                        "campaign_id": d.get("campaign_id"),
                        "campaign_title": d.get("campaigns", {}).get("title") if d.get("campaigns") else None,
                        "amount": float(d.get("amount", 0)),
                        "status": d.get("status", "completed"),
                        "donated_at": d.get("donated_at")
                    }
                    for d in donations_query.data
                ]
        except Exception as e:
            print(f"Error fetching recent donations: {e}")
        
        # Get recent campaigns (last 5)
        recent_campaigns = []
        try:
            campaigns_query = supabase.table("campaigns").select("*, users!campaigns_ngo_id(full_name)").order("created_at", desc=True).limit(5).execute()
            if campaigns_query.data:
                recent_campaigns = [
                    {
                        "id": c.get("id"),
                        "ngo_id": c.get("ngo_id"),
                        "ngo_name": c.get("users", {}).get("full_name") if c.get("users") else None,
                        "title": c.get("title"),
                        "description": c.get("description"),
                        "category": c.get("category"),
                        "goal_amount": float(c.get("goal_amount", 0)),
                        "raised_amount": float(c.get("raised_amount", 0)),
                        "status": c.get("status"),
                        "image_url": c.get("image_url"),
                        "created_at": c.get("created_at")
                    }
                    for c in campaigns_query.data
                ]
        except Exception as e:
            print(f"Error fetching recent campaigns: {e}")
        
        return {
            **stats,
            "recent_donations": recent_donations,
            "recent_campaigns": recent_campaigns
        }
        
    except Exception as e:
        print(f"❌ Error in get_dashboard_stats: {str(e)}")
        print(traceback.format_exc())
        # Return default stats instead of crashing
        return {
            "total_donations": 0,
            "total_campaigns": 0,
            "total_ngos": 0,
            "total_users": 0,
            "active_campaigns": 0,
            "recent_donations": [],
            "recent_campaigns": []
        }

@router.get("/notifications", response_model=List[NotificationResponse])
async def get_notifications(user: dict = Depends(get_current_user)):
    """Get user notifications"""
    try:
        print(f"Fetching notifications for user: {user['id']}")
        
        result = supabase.table("notifications").select("*").eq("user_id", user["id"]).order("created_at", desc=True).execute()
        
        notifications = []
        if result.data:
            notifications = [
                {
                    "id": n.get("id"),
                    "user_id": n.get("user_id"),
                    "title": n.get("title", ""),
                    "message": n.get("message", ""),
                    "type": n.get("type", "system"),
                    "read": n.get("read", False),
                    "created_at": n.get("created_at")
                }
                for n in result.data
            ]
        
        return notifications
        
    except Exception as e:
        print(f"❌ Error in get_notifications: {str(e)}")
        return []

@router.put("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str, user: dict = Depends(get_current_user)):
    """Mark notification as read"""
    try:
        supabase.table("notifications").update({"read": True}).eq("id", notification_id).eq("user_id", user["id"]).execute()
        return {"message": "Notification marked as read"}
    except Exception as e:
        print(f"❌ Error marking notification as read: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to mark notification as read")
