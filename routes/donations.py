from fastapi import APIRouter, HTTPException, Depends
from typing import List
from schemas import DonationCreate, DonationResponse
from auth import get_current_user
from database import supabase

router = APIRouter(prefix="/donations", tags=["donations"])

@router.post("/", response_model=DonationResponse)
async def create_donation(donation: DonationCreate, user=Depends(get_current_user)):
    if user["role"] != "user":
        raise HTTPException(status_code=403, detail="Only users can donate")
    
    # Create donation
    result = supabase.table("donations").insert({
        "user_id": user["id"],
        "campaign_id": donation.campaign_id,
        "amount": donation.amount,
        "payment_method": donation.payment_method,
        "status": "completed"
    }).execute()
    
    if not result.data:
        raise HTTPException(status_code=400, detail="Donation failed")
    
    # Update campaign raised amount
    campaign = supabase.table("campaigns").select("raised_amount").eq("id", donation.campaign_id).execute()
    if campaign.data:
        new_amount = campaign.data[0]["raised_amount"] + donation.amount
        supabase.table("campaigns").update({"raised_amount": new_amount}).eq("id", donation.campaign_id).execute()
    
    # Create notification for user
    supabase.table("notifications").insert({
        "user_id": user["id"],
        "title": "Donation Successful",
        "message": f"Thank you for donating ₹{donation.amount}!",
        "type": "donation"
    }).execute()
    
    # Get campaign details for NGO notification
    campaign_details = supabase.table("campaigns").select("ngo_id, title").eq("id", donation.campaign_id).execute()
    if campaign_details.data:
        # Notify NGO
        supabase.table("notifications").insert({
            "user_id": campaign_details.data[0]["ngo_id"],
            "title": "New Donation Received",
            "message": f"Received ₹{donation.amount} for {campaign_details.data[0]['title']}",
            "type": "donation"
        }).execute()
    
    return result.data[0]

@router.get("/user", response_model=List[DonationResponse])
async def get_user_donations(user=Depends(get_current_user)):
    result = supabase.table("donations").select("*, campaigns!donations_campaign_id(title)").eq("user_id", user["id"]).execute()
    
    donations = []
    for item in result.data:
        donations.append({
            **item,
            "campaign_title": item["campaigns"]["title"] if item.get("campaigns") else None
        })
    
    return donations