"""FastAPI router for the Universal SaaS Connector.

All routes require a Bearer token. The authenticated user's id is used to
own and scope every SaaS connection. OAuth flows are placeholders in this
step — Step 3 wires the per-app auth_url builder and callback handler.
"""

from typing import Any

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from services.database import supabase_admin
from saas_connectors.credential_vault import store_credentials
from saas_connectors.scan_runner import run_scan


router = APIRouter()


# ── Auth helper ─────────────────────────────────────────────────────────────

def _get_user_id(authorization: str) -> str:
    token = authorization.removeprefix("Bearer ")
    user = supabase_admin.auth.get_user(token)
    if not user or not user.user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user.user.id


def _get_registry_entry(app_slug: str) -> dict[str, Any]:
    r = (
        supabase_admin.table("saas_app_registry")
        .select("slug, name, tier, oauth_config, wizard_recipe")
        .eq("slug", app_slug)
        .single()
        .execute()
    )
    if not r.data:
        raise HTTPException(status_code=404, detail=f"App '{app_slug}' is not in the registry")
    return r.data


# ── OAuth connect (placeholder — Step 3 finishes this) ─────────────────────

@router.post("/connect/oauth/{app_slug}")
def oauth_start(app_slug: str, authorization: str = Header(...)):
    _get_user_id(authorization)
    entry = _get_registry_entry(app_slug)
    if entry.get("tier") != "1_oauth":
        raise HTTPException(status_code=400, detail=f"App '{app_slug}' is not an OAuth integration")
    return {
        "app_slug": app_slug,
        "auth_url": None,
        "placeholder": True,
        "message": "OAuth auth URL building is wired in Step 3.",
    }


@router.get("/callback/{app_slug}")
def oauth_callback(app_slug: str, code: str | None = None, state: str | None = None):  # noqa: ARG001
    return {
        "app_slug": app_slug,
        "placeholder": True,
        "message": "OAuth callback handling is wired in Step 3.",
    }


# ── Manual credential connect ───────────────────────────────────────────────

class ManualConnectRequest(BaseModel):
    credentials: dict[str, Any]


@router.post("/connect/manual/{app_slug}")
def manual_connect(
    app_slug: str,
    data: ManualConnectRequest,
    authorization: str = Header(...),
):
    user_id = _get_user_id(authorization)
    entry = _get_registry_entry(app_slug)

    if not data.credentials:
        raise HTTPException(status_code=400, detail="credentials object is required")

    try:
        connection_id = store_credentials(
            user_id=user_id,
            app_slug=app_slug,
            app_name=entry["name"],
            connection_type="api_key",
            plaintext_credentials=data.credentials,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    return {"connection_id": connection_id, "app_slug": app_slug, "app_name": entry["name"]}


# ── Scan trigger ────────────────────────────────────────────────────────────

@router.post("/scan/{connection_id}")
def scan_connection(connection_id: str, authorization: str = Header(...)):
    user_id = _get_user_id(authorization)

    owner = (
        supabase_admin.table("saas_connections")
        .select("user_id")
        .eq("id", connection_id)
        .single()
        .execute()
    )
    if not owner.data:
        raise HTTPException(status_code=404, detail="Connection not found")
    if owner.data["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not allowed")

    try:
        return run_scan(connection_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


# ── List connections ────────────────────────────────────────────────────────

@router.get("/connections")
def list_connections(authorization: str = Header(...)):
    user_id = _get_user_id(authorization)
    r = (
        supabase_admin.table("saas_connections")
        .select("id, app_slug, app_name, connection_type, status, last_scan_at, created_at")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    return {"connections": r.data or []}


# ── Disconnect ──────────────────────────────────────────────────────────────

@router.delete("/connections/{connection_id}")
def disconnect(connection_id: str, authorization: str = Header(...)):
    user_id = _get_user_id(authorization)

    owner = (
        supabase_admin.table("saas_connections")
        .select("user_id")
        .eq("id", connection_id)
        .single()
        .execute()
    )
    if not owner.data:
        raise HTTPException(status_code=404, detail="Connection not found")
    if owner.data["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not allowed")

    supabase_admin.table("saas_connections").delete().eq("id", connection_id).execute()
    return {"message": "Disconnected", "connection_id": connection_id}
