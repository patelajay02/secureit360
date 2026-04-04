# backend/middleware/auth_middleware.py
# SecureIT360 — Auth middleware
# Verifies JWT and extracts tenant info

import os
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client

security = HTTPBearer()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY"),
)

async def get_current_tenant(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials

    try:
        # Verify token with Supabase
        user = supabase.auth.get_user(token)
        if not user or not user.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )

        user_id = user.user.id

        # Get tenant info
        result = supabase.table("tenant_users")\
            .select("tenant_id, role")\
            .eq("user_id", user_id)\
            .eq("status", "active")\
            .limit(1)\
            .execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tenant found for this user",
            )

        return {
            "user_id": user_id,
            "tenant_id": result.data[0]["tenant_id"],
            "role": result.data[0]["role"],
            "token": token,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )