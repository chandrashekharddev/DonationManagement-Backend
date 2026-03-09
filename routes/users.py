from fastapi import APIRouter, Depends, HTTPException
from typing import List
from schemas import UserResponse, DonationResponse, CampaignResponse, NotificationResponse, DashboardStats
from auth import get_current_user
from database import supabase
from datetime import datetime
import traceback

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information"""
    return current_user

@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(current_user: dict = Depends(get_current_user)):
    """Get dashboard statistics based on user role"""
    try:
        print(f"Fetching dashboard for user: {current_user['username']} with role: {current_user['role']}")
        
        # Get global stats - FIXED: Remove joins, fetch separately
        users_result = supabase.table("users").select("*", count="exact").execute()
        ngos_result = supabase.table("users").select("*", count="exact").eq("role", "ngo").execute()
        campaigns_result = supabase.table("campaigns").select("*", count="exact").execute()
        
        total_users = users_result.count if hasattr(users_result, 'count') else len(users_result.data)
        total_ngos = ngos_result.count if hasattr(ngos_result, 'count') else len(ngos_result.data)
        total_campaigns = campaigns_result.count if hasattr(campaigns_result, 'count') else len(campaigns_result.data)
        active_campaigns = len([c for c in campaigns_result.data if c.get("status") == "active"]) if campaigns_result.data else 0
        
        # Get role-specific donations
        total_donations = 0.0
        
        if current_user["role"] == "admin":
            donations_result = supabase.table("donations").select("amount").execute()
            total_donations = sum(float(d["amount"]) for d in donations_result.data) if donations_result.data else 0.0
            
        elif current_user["role"] == "ngo":
            campaigns = supabase.table("campaigns").select("id").eq("ngo_id", current_user["id"]).execute()
            campaign_ids = [c["id"] for c in campaigns.data] if campaigns.data else []
            
            if campaign_ids:
                donations_result = supabase.table("donations").select("amount").in_("campaign_id", campaign_ids).execute()
                total_donations = sum(float(d["amount"]) for d in donations_result.data) if donations_result.data else 0.0
                
        else:  # user
            donations_result = supabase.table("donations").select("amount").eq("user_id", current_user["id"]).execute()
            total_donations = sum(float(d["amount"]) for d in donations_result.data) if donations_result.data else 0.0
        
        # Get recent donations - FIXED: Remove joins, fetch separately
        recent_donations = []
        try:
            # Fetch recent donations
            donations_query = supabase.table("donations").select("*").order("donated_at", desc=True).limit(5).execute()
            
            if donations_query.data:
                for d in donations_query.data:
                    # Fetch user name separately
                    user_name = "Anonymous"
                    if d.get("user_id"):
                        user = supabase.table("users").select("full_name").eq("id", d["user_id"]).execute()
                        if user.data:
                            user_name = user.data[0]["full_name"]
                    
                    # Fetch campaign title separately
                    campaign_title = "Campaign"
                    if d.get("campaign_id"):
                        campaign = supabase.table("campaigns").select("title").eq("id", d["campaign_id"]).execute()
                        if campaign.data:
                            campaign_title = campaign.data[0]["title"]
                    
                    donation = {
                        "id": d.get("id", ""),
                        "user_id": d.get("user_id", ""),
                        "user_name": user_name,
                        "campaign_id": d.get("campaign_id", ""),
                        "campaign_title": campaign_title,
                        "amount": float(d.get("amount", 0)),
                        "status": d.get("status", "completed"),
                        "donated_at": d.get("donated_at")
                    }
                    recent_donations.append(donation)
        except Exception as e:
            print(f"Error fetching recent donations: {e}")
        
        # Get recent campaigns - FIXED: Remove joins, fetch separately
        recent_campaigns = []
        try:
            # Fetch recent campaigns
            campaigns_query = supabase.table("campaigns").select("*").order("created_at", desc=True).limit(5).execute()
            
            if campaigns_query.data:
                for c in campaigns_query.data:
                    # Fetch NGO name separately
                    ngo_name = "NGO"
                    if c.get("ngo_id"):
                        ngo = supabase.table("users").select("full_name").eq("id", c["ngo_id"]).execute()
                        if ngo.data:
                            ngo_name = ngo.data[0]["full_name"]
                    
                    campaign = {
                        "id": c.get("id", ""),
                        "ngo_id": c.get("ngo_id", ""),
                        "ngo_name": ngo_name,
                        "title": c.get("title", ""),
                        "description": c.get("description"),
                        "category": c.get("category", "Other"),
                        "goal_amount": float(c.get("goal_amount", 0)),
                        "raised_amount": float(c.get("raised_amount", 0)),
                        "status": c.get("status", "pending"),
                        "image_url": c.get("image_url"),
                        "created_at": c.get("created_at")
                    }
                    recent_campaigns.append(campaign)
        except Exception as e:
            print(f"Error fetching recent campaigns: {e}")
        
        # Create DashboardStats
        dashboard_stats = {
            "total_donations": float(total_donations),
            "total_campaigns": total_campaigns,
            "total_ngos": total_ngos,
            "total_users": total_users,
            "active_campaigns": active_campaigns,
            "recent_donations": recent_donations,
            "recent_campaigns": recent_campaigns
        }
        
        print(f"✅ Dashboard stats prepared for {current_user['role']}")
        return dashboard_stats
        
    except Exception as e:
        print(f"❌ Error in get_dashboard_stats: {str(e)}")
        print(traceback.format_exc())
        return {
            "total_donations": 0.0,
            "total_campaigns": 0,
            "total_ngos": 0,
            "total_users": 0,
            "active_campaigns": 0,
            "recent_donations": [],
            "recent_campaigns": []
        }

@router.get("/notifications", response_model=List[NotificationResponse])
async def get_notifications(current_user: dict = Depends(get_current_user)):
    """Get user notifications"""
    try:
        print(f"Fetching notifications for user: {current_user['id']}")
        
        result = supabase.table("notifications").select("*")\
            .eq("user_id", current_user["id"])\
            .order("created_at", desc=True).execute()
        
        notifications = []
        if result.data:
            for n in result.data:
                notification = {
                    "id": n.get("id", ""),
                    "title": n.get("title", ""),
                    "message": n.get("message"),
                    "type": n.get("type", "system"),
                    "read": n.get("read", False),
                    "created_at": n.get("created_at")
                }
                notifications.append(notification)
        
        print(f"✅ Found {len(notifications)} notifications")
        return notifications
        
    except Exception as e:
        print(f"❌ Error in get_notifications: {str(e)}")
        return []

@router.put("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str, current_user: dict = Depends(get_current_user)):
    """Mark notification as read"""
    try:
        supabase.table("notifications").update({"read": True})\
            .eq("id", notification_id)\
            .eq("user_id", current_user["id"]).execute()
        return {"message": "Notification marked as read"}
    except Exception as e:
        print(f"❌ Error marking notification as read: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to mark notification as read")
