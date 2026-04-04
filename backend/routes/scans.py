# SecureIT360 - Scan Routes
# Handles: Triggering scans and retrieving scan results
# Every query filters by tenant_id so companies only see their own scans

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from services.database import supabase, supabase_admin
from services.darkweb_scan import run_darkweb_scan
from services.email_scan import run_email_scan
from services.network_scan import run_network_scan
from services.website_scan import run_website_scan
from services.device_scan import run_device_scan
from services.cloud_scan import run_cloud_scan
import asyncio
from services.full_scan import run_full_scan

router = APIRouter()

# What we expect when triggering a scan
class ScanRequest(BaseModel):
    domain_id: str

# TRIGGER DARK WEB SCAN
@router.post("/darkweb")
async def darkweb_scan(data: ScanRequest, authorization: str = Header(...)):
    try:
        token = authorization.replace("Bearer ", "")
        user = supabase.auth.get_user(token)
        user_id = user.user.id

        # Get tenant for this user
        tenant_user = supabase_admin.table("tenant_users")\
            .select("tenant_id")\
            .eq("user_id", user_id)\
            .eq("status", "active")\
            .single()\
            .execute()

        tenant_id = tenant_user.data["tenant_id"]

        # Get the domain - confirm it belongs to this tenant
        domain_row = supabase_admin.table("domains")\
            .select("*")\
            .eq("id", data.domain_id)\
            .eq("tenant_id", tenant_id)\
            .single()\
            .execute()

        if not domain_row.data:
            raise HTTPException(status_code=404, detail="Domain not found.")

        domain = domain_row.data["domain"]

        # Create a scan record
        scan = supabase_admin.table("scans").insert({
            "tenant_id": tenant_id,
            "domain_id": data.domain_id,
            "triggered_by": user_id,
            "trigger_type": "manual",
            "status": "running"
        }).execute()

        scan_id = scan.data[0]["id"]

        # Run the dark web scan
        result = await run_darkweb_scan(tenant_id, scan_id, domain)

        # Update scan status
        supabase_admin.table("scans")\
            .update({"status": "complete"})\
            .eq("id", scan_id)\
            .execute()

        return {
            "message": "Dark web scan complete",
            "scan_id": scan_id,
            "findings_count": result["findings_count"]
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# TRIGGER EMAIL SECURITY SCAN
@router.post("/email")
async def email_scan(data: ScanRequest, authorization: str = Header(...)):
    try:
        token = authorization.replace("Bearer ", "")
        user = supabase.auth.get_user(token)
        user_id = user.user.id

        # Get tenant for this user
        tenant_user = supabase_admin.table("tenant_users")\
            .select("tenant_id")\
            .eq("user_id", user_id)\
            .eq("status", "active")\
            .single()\
            .execute()

        tenant_id = tenant_user.data["tenant_id"]

        # Get the domain - confirm it belongs to this tenant
        domain_row = supabase_admin.table("domains")\
            .select("*")\
            .eq("id", data.domain_id)\
            .eq("tenant_id", tenant_id)\
            .single()\
            .execute()

        if not domain_row.data:
            raise HTTPException(status_code=404, detail="Domain not found.")

        domain = domain_row.data["domain"]

        # Create a scan record
        scan = supabase_admin.table("scans").insert({
            "tenant_id": tenant_id,
            "domain_id": data.domain_id,
            "triggered_by": user_id,
            "trigger_type": "manual",
            "status": "running"
        }).execute()

        scan_id = scan.data[0]["id"]

        # Run the email scan
        result = await run_email_scan(tenant_id, scan_id, domain)

        # Update scan status
        supabase_admin.table("scans")\
            .update({"status": "complete"})\
            .eq("id", scan_id)\
            .execute()

        return {
            "message": "Email security scan complete",
            "scan_id": scan_id,
            "findings_count": result["findings_count"]
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# GET ALL SCANS FOR THIS COMPANY
@router.get("/")
def get_scans(authorization: str = Header(...)):
    try:
        token = authorization.replace("Bearer ", "")
        user = supabase.auth.get_user(token)
        user_id = user.user.id

        # Get tenant for this user
        tenant_user = supabase_admin.table("tenant_users")\
            .select("tenant_id")\
            .eq("user_id", user_id)\
            .eq("status", "active")\
            .single()\
            .execute()

        tenant_id = tenant_user.data["tenant_id"]

        # Get all scans for this tenant only
        scans = supabase_admin.table("scans")\
            .select("*")\
            .eq("tenant_id", tenant_id)\
            .order("created_at", desc=True)\
            .execute()

        return {"scans": scans.data}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# GET ALL FINDINGS FOR THIS COMPANY
@router.get("/findings")
def get_findings(authorization: str = Header(...)):
    try:
        token = authorization.replace("Bearer ", "")
        user = supabase.auth.get_user(token)
        user_id = user.user.id

        # Get tenant for this user
        tenant_user = supabase_admin.table("tenant_users")\
            .select("tenant_id")\
            .eq("user_id", user_id)\
            .eq("status", "active")\
            .single()\
            .execute()

        tenant_id = tenant_user.data["tenant_id"]

        # Get all findings for this tenant only
        findings = supabase_admin.table("findings")\
            .select("*")\
            .eq("tenant_id", tenant_id)\
            .order("created_at", desc=True)\
            .execute()

        return {"findings": findings.data}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

        # TRIGGER NETWORK SCAN
@router.post("/network")
async def network_scan(data: ScanRequest, authorization: str = Header(...)):
    try:
        token = authorization.replace("Bearer ", "")
        user = supabase.auth.get_user(token)
        user_id = user.user.id

        tenant_user = supabase_admin.table("tenant_users")\
            .select("tenant_id")\
            .eq("user_id", user_id)\
            .eq("status", "active")\
            .single()\
            .execute()

        tenant_id = tenant_user.data["tenant_id"]

        domain_row = supabase_admin.table("domains")\
            .select("*")\
            .eq("id", data.domain_id)\
            .eq("tenant_id", tenant_id)\
            .single()\
            .execute()

        if not domain_row.data:
            raise HTTPException(status_code=404, detail="Domain not found.")

        domain = domain_row.data["domain"]

        scan = supabase_admin.table("scans").insert({
            "tenant_id": tenant_id,
            "domain_id": data.domain_id,
            "triggered_by": user_id,
            "trigger_type": "manual",
            "status": "running"
        }).execute()

        scan_id = scan.data[0]["id"]
        result = await run_network_scan(tenant_id, scan_id, domain)

        supabase_admin.table("scans")\
            .update({"status": "complete"})\
            .eq("id", scan_id)\
            .execute()

        return {
            "message": "Network scan complete",
            "scan_id": scan_id,
            "findings_count": result["findings_count"]
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# TRIGGER WEBSITE AND SSL SCAN
@router.post("/website")
async def website_scan(data: ScanRequest, authorization: str = Header(...)):
    try:
        token = authorization.replace("Bearer ", "")
        user = supabase.auth.get_user(token)
        user_id = user.user.id

        tenant_user = supabase_admin.table("tenant_users")\
            .select("tenant_id")\
            .eq("user_id", user_id)\
            .eq("status", "active")\
            .single()\
            .execute()

        tenant_id = tenant_user.data["tenant_id"]

        domain_row = supabase_admin.table("domains")\
            .select("*")\
            .eq("id", data.domain_id)\
            .eq("tenant_id", tenant_id)\
            .single()\
            .execute()

        if not domain_row.data:
            raise HTTPException(status_code=404, detail="Domain not found.")

        domain = domain_row.data["domain"]

        scan = supabase_admin.table("scans").insert({
            "tenant_id": tenant_id,
            "domain_id": data.domain_id,
            "triggered_by": user_id,
            "trigger_type": "manual",
            "status": "running"
        }).execute()

        scan_id = scan.data[0]["id"]
        result = await run_website_scan(tenant_id, scan_id, domain)

        supabase_admin.table("scans")\
            .update({"status": "complete"})\
            .eq("id", scan_id)\
            .execute()

        return {
            "message": "Website and SSL scan complete",
            "scan_id": scan_id,
            "findings_count": result["findings_count"]
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

        # TRIGGER DEVICE SCAN
@router.post("/devices")
async def device_scan(data: ScanRequest, authorization: str = Header(...)):
    try:
        token = authorization.replace("Bearer ", "")
        user = supabase.auth.get_user(token)
        user_id = user.user.id

        tenant_user = supabase_admin.table("tenant_users")\
            .select("tenant_id")\
            .eq("user_id", user_id)\
            .eq("status", "active")\
            .single()\
            .execute()

        tenant_id = tenant_user.data["tenant_id"]

        domain_row = supabase_admin.table("domains")\
            .select("*")\
            .eq("id", data.domain_id)\
            .eq("tenant_id", tenant_id)\
            .single()\
            .execute()

        if not domain_row.data:
            raise HTTPException(status_code=404, detail="Domain not found.")

        domain = domain_row.data["domain"]

        scan = supabase_admin.table("scans").insert({
            "tenant_id": tenant_id,
            "domain_id": data.domain_id,
            "triggered_by": user_id,
            "trigger_type": "manual",
            "status": "running"
        }).execute()

        scan_id = scan.data[0]["id"]
        result = await run_device_scan(tenant_id, scan_id, domain)

        supabase_admin.table("scans")\
            .update({"status": "complete"})\
            .eq("id", scan_id)\
            .execute()

        return {
            "message": "Device scan complete",
            "scan_id": scan_id,
            "findings_count": result["findings_count"]
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# TRIGGER CLOUD SCAN
@router.post("/cloud")
async def cloud_scan(data: ScanRequest, authorization: str = Header(...)):
    try:
        token = authorization.replace("Bearer ", "")
        user = supabase.auth.get_user(token)
        user_id = user.user.id

        tenant_user = supabase_admin.table("tenant_users")\
            .select("tenant_id")\
            .eq("user_id", user_id)\
            .eq("status", "active")\
            .single()\
            .execute()

        tenant_id = tenant_user.data["tenant_id"]

        domain_row = supabase_admin.table("domains")\
            .select("*")\
            .eq("id", data.domain_id)\
            .eq("tenant_id", tenant_id)\
            .single()\
            .execute()

        if not domain_row.data:
            raise HTTPException(status_code=404, detail="Domain not found.")

        domain = domain_row.data["domain"]

        scan = supabase_admin.table("scans").insert({
            "tenant_id": tenant_id,
            "domain_id": data.domain_id,
            "triggered_by": user_id,
            "trigger_type": "manual",
            "status": "running"
        }).execute()

        scan_id = scan.data[0]["id"]
        result = await run_cloud_scan(tenant_id, scan_id, domain)

        supabase_admin.table("scans")\
            .update({"status": "complete"})\
            .eq("id", scan_id)\
            .execute()

        return {
            "message": "Cloud scan complete",
            "scan_id": scan_id,
            "findings_count": result["findings_count"]
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

        # TRIGGER FULL SCAN - Runs all 6 engines in one click
@router.post("/full")
async def full_scan(data: ScanRequest, authorization: str = Header(...)):
    try:
        token = authorization.replace("Bearer ", "")
        user = supabase.auth.get_user(token)
        user_id = user.user.id

        tenant_user = supabase_admin.table("tenant_users")\
            .select("tenant_id")\
            .eq("user_id", user_id)\
            .eq("status", "active")\
            .single()\
            .execute()

        tenant_id = tenant_user.data["tenant_id"]

        domain_row = supabase_admin.table("domains")\
            .select("*")\
            .eq("id", data.domain_id)\
            .eq("tenant_id", tenant_id)\
            .single()\
            .execute()

        if not domain_row.data:
            raise HTTPException(status_code=404, detail="Domain not found.")

        domain = domain_row.data["domain"]

        result = await run_full_scan(
            tenant_id, data.domain_id, domain, user_id
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))