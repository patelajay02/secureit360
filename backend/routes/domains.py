# SecureIT360 - Domain Management Routes
# Handles: Adding domains to scan, listing domains, deleting domains
# Every query filters by tenant_id so companies only see their own domains

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from services.database import supabase, supabase_admin

router = APIRouter()

# Plan limits - how many domains each plan allows
PLAN_LIMITS = {
    "starter": 1,
    "pro": 3,
    "enterprise": 10
}

# What we expect when adding a new domain
class DomainRequest(BaseModel):
    domain: str

# ADD A DOMAIN
@router.post("/")
def add_domain(data: DomainRequest, authorization: str = Header(...)):
    try:
        # Get the user from the token
        token = authorization.replace("Bearer ", "")
        user = supabase.auth.get_user(token)
        user_id = user.user.id

        # Get the tenant and plan for this user
        tenant_user = supabase_admin.table("tenant_users")\
            .select("tenant_id, tenants(plan)")\
            .eq("user_id", user_id)\
            .eq("status", "active")\
            .single()\
            .execute()

        tenant_id = tenant_user.data["tenant_id"]
        plan = tenant_user.data["tenants"]["plan"]

        # Check how many domains this tenant already has
        existing = supabase_admin.table("domains")\
            .select("id")\
            .eq("tenant_id", tenant_id)\
            .execute()

        max_domains = PLAN_LIMITS.get(plan, 1)

        if len(existing.data) >= max_domains:
            raise HTTPException(
                status_code=400,
                detail=f"Your {plan} plan allows {max_domains} domain(s). Please upgrade to add more."
            )

        # Add the domain
        domain = supabase_admin.table("domains").insert({
            "tenant_id": tenant_id,
            "domain": data.domain,
            "verified": False,
            "is_primary": len(existing.data) == 0
        }).execute()

        return {"message": "Domain added successfully", "domain": domain.data[0]}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# GET ALL DOMAINS FOR THIS COMPANY
@router.get("/")
def get_domains(authorization: str = Header(...)):
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

        # Get all domains for this tenant only
        domains = supabase_admin.table("domains")\
            .select("*")\
            .eq("tenant_id", tenant_id)\
            .execute()

        return {"domains": domains.data}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# DELETE A DOMAIN
@router.delete("/{domain_id}")
def delete_domain(domain_id: str, authorization: str = Header(...)):
    try:
        token = authorization.replace("Bearer ", "")
        user = supabase.auth.get_user(token)
        user_id = user.user.id

        # Get tenant_id for this user
        tenant_user = supabase_admin.table("tenant_users")\
            .select("tenant_id, role")\
            .eq("user_id", user_id)\
            .eq("status", "active")\
            .single()\
            .execute()

        tenant_id = tenant_user.data["tenant_id"]
        role = tenant_user.data["role"]

        # Only owners and admins can delete domains
        if role not in ["owner", "admin"]:
            raise HTTPException(status_code=403, detail="Only owners and admins can delete domains.")

        # Confirm this domain belongs to this tenant before deleting
        domain = supabase_admin.table("domains")\
            .select("id")\
            .eq("id", domain_id)\
            .eq("tenant_id", tenant_id)\
            .single()\
            .execute()

        if not domain.data:
            raise HTTPException(status_code=404, detail="Domain not found.")

        # Delete the domain
        supabase_admin.table("domains")\
            .delete()\
            .eq("id", domain_id)\
            .eq("tenant_id", tenant_id)\
            .execute()

        return {"message": "Domain deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))