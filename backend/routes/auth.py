# SecureIT360 - Authentication Routes
# Handles: Register a new company, Login, and Get current user details

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
from services.database import supabase, supabase_admin
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from fastapi import Header

router = APIRouter()

# This defines what information we expect when a new company registers
class RegisterRequest(BaseModel):
    email: str
    password: str
    company_name: str
    domain: str
    country: str
    mobile: str

# This defines what information we expect when a user logs in
class LoginRequest(BaseModel):
    email: str
    password: str


# REGISTER - A new company signs up
@router.post("/register")
def register(data: RegisterRequest):
    try:
        # Step 1: Create the user in Supabase Auth
        auth_response = supabase_admin.auth.admin.create_user({
            "email": data.email,
            "password": data.password,
            "email_confirm": True
        })
        user_id = auth_response.user.id

        # Step 2: Create a slug (short url-friendly version of company name)
        slug = data.company_name.lower().replace(" ", "-")

        # Step 3: Create the tenant row for this company
        # Step 3: Create the tenant row for this company
        tenant = supabase_admin.table("tenants").insert({
            "name": data.company_name,
            "slug": slug,
            "status": "trial",
            "trial_ends_at": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "country": data.country,
            "mobile": data.mobile
        }).execute()

        tenant_id = tenant.data[0]["id"]

        # Step 4: Link the user to the tenant as the owner
        supabase_admin.table("tenant_users").insert({
            "tenant_id": tenant_id,
            "user_id": user_id,
            "role": "owner",
            "status": "active"
        }).execute()

        # Step 5: Add their domain
        supabase_admin.table("domains").insert({
            "tenant_id": tenant_id,
            "domain": data.domain,
            "is_primary": True,
            "verified": False
        }).execute()

        return {
            "message": "Account created successfully",
            "tenant_id": tenant_id,
            "email": data.email
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# LOGIN - An existing user logs in
@router.post("/login")
def login(data: LoginRequest):
    try:
        # Sign in with Supabase Auth
        auth_response = supabase.auth.sign_in_with_password({
            "email": data.email,
            "password": data.password
        })

        user_id = auth_response.user.id
        token = auth_response.session.access_token

        # Get the tenant details for this user
        tenant_user = supabase_admin.table("tenant_users")\
            .select("*, tenants(*)")\
            .eq("user_id", user_id)\
            .eq("status", "active")\
            .single()\
            .execute()

        return {
            "token": token,
            "user_id": user_id,
            "email": data.email,
            "tenant_id": tenant_user.data["tenant_id"],
            "role": tenant_user.data["role"],
            "company_name": tenant_user.data["tenants"]["name"],
            "plan": tenant_user.data["tenants"]["plan"],
            "country": tenant_user.data["tenants"].get("country", "NZ"),
            "mobile": tenant_user.data["tenants"].get("mobile", "")
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
        # INVITE A TEAM MEMBER
@router.post("/invite")
def invite_user(data: dict, authorization: str = Header(...)):
    try:
        token = authorization.replace("Bearer ", "")
        user = supabase.auth.get_user(token)
        user_id = user.user.id

        # Get tenant and role for the person sending the invite
        tenant_user = supabase_admin.table("tenant_users")\
            .select("tenant_id, role, tenants(name)")\
            .eq("user_id", user_id)\
            .eq("status", "active")\
            .single()\
            .execute()

        role = tenant_user.data["role"]
        tenant_id = tenant_user.data["tenant_id"]
        company_name = tenant_user.data["tenants"]["name"]

        # Only owners and admins can invite
        if role not in ["owner", "admin"]:
            raise HTTPException(status_code=403, detail="Only owners and admins can invite team members.")

        invited_email = data.get("email")
        invited_role = data.get("role", "member")

        # Send invitation email via SendGrid
        message = Mail(
            from_email=os.getenv("SENDGRID_FROM_EMAIL"),
            to_emails=invited_email,
            subject=f"You have been invited to join {company_name} on SecureIT360",
            html_content=f"""
                <p>Hello,</p>
                <p>You have been invited to join <strong>{company_name}</strong> on SecureIT360.</p>
                <p>Your role will be: <strong>{invited_role}</strong></p>
                <p>The SecureIT360 Team<br>hello@secureit360.co</p>
            """
        )

        sg = SendGridAPIClient(os.getenv("SENDGRID_API_KEY"))
        sg.send(message)

        return {"message": f"Invitation sent to {invited_email}"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# GET ALL USERS FOR THIS COMPANY
@router.get("/users")
def get_users(authorization: str = Header(...)):
    try:
        token = authorization.replace("Bearer ", "")
        user = supabase.auth.get_user(token)
        user_id = user.user.id

        # Get tenant_id for this user
        tenant_user = supabase_admin.table("tenant_users")\
            .select("tenant_id")\
            .eq("user_id", user_id)\
            .eq("status", "active")\
            .single()\
            .execute()

        tenant_id = tenant_user.data["tenant_id"]

        # Get all users for this tenant only
        users = supabase_admin.table("tenant_users")\
            .select("*")\
            .eq("tenant_id", tenant_id)\
            .execute()

        return {"users": users.data}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))