"""Credential vault for the Universal SaaS Connector.

Uses Supabase-side pgcrypto (pgp_sym_encrypt/pgp_sym_decrypt) via two
SECURITY DEFINER RPCs so plaintext secrets never transit any path where
they could be logged:

    saas_store_connection(user_id, app_slug, app_name, connection_type,
                          plaintext_json, vault_key) -> uuid
    saas_load_credentials(connection_id, user_id, vault_key) -> jsonb

The vault_key comes from the SAAS_VAULT_KEY env var and is passed straight
to Postgres. Nothing in this module prints or returns raw plaintext outside
the two public helpers below.
"""

import json
import os
from typing import Any

from services.database import supabase_admin


def _vault_key() -> str:
    key = os.getenv("SAAS_VAULT_KEY")
    if not key:
        raise RuntimeError("SAAS_VAULT_KEY environment variable is not set")
    return key


def encrypt_credentials(plaintext_json: dict) -> bytes:
    """Encrypt a credential dict. Returns the raw ciphertext bytes.

    This helper is mostly used for unit testing the round-trip. In
    production paths prefer store_credentials() which performs the insert
    atomically on the database side.
    """
    resp = supabase_admin.rpc(
        "saas_encrypt",
        {"p_plaintext": json.dumps(plaintext_json), "p_key": _vault_key()},
    ).execute()
    value = resp.data
    if value is None:
        raise RuntimeError("saas_encrypt returned no data")
    if isinstance(value, str):
        return value.encode("utf-8")
    return value


def decrypt_credentials(encrypted: bytes) -> dict:
    """Decrypt ciphertext produced by encrypt_credentials back into a dict.

    Mirror of encrypt_credentials for tests; production code paths should
    use load_credentials() which performs the select atomically.
    """
    payload = encrypted.decode("utf-8") if isinstance(encrypted, (bytes, bytearray)) else encrypted
    resp = supabase_admin.rpc(
        "saas_decrypt",
        {"p_ciphertext": payload, "p_key": _vault_key()},
    ).execute()
    value = resp.data
    if value is None:
        raise RuntimeError("saas_decrypt returned no data")
    return json.loads(value)


def store_credentials(
    user_id: str,
    app_slug: str,
    app_name: str,
    connection_type: str,
    plaintext_credentials: dict,
) -> str:
    """Insert a saas_connections row with credentials encrypted at rest.

    Returns the new connection id. Plaintext never leaves this function —
    the RPC performs pgp_sym_encrypt inline inside the INSERT.
    """
    if connection_type not in ("oauth", "api_key"):
        raise ValueError("connection_type must be 'oauth' or 'api_key'")

    resp = supabase_admin.rpc(
        "saas_store_connection",
        {
            "p_user_id": user_id,
            "p_app_slug": app_slug,
            "p_app_name": app_name,
            "p_connection_type": connection_type,
            "p_plaintext_json": json.dumps(plaintext_credentials),
            "p_key": _vault_key(),
        },
    ).execute()
    new_id = resp.data
    if not new_id:
        raise RuntimeError("saas_store_connection returned no connection id")
    return new_id


def load_credentials(connection_id: str, user_id: str) -> dict:
    """Return the decrypted credentials dict for a connection owned by user_id.

    Raises PermissionError if the connection does not belong to user_id.
    Raises RuntimeError if decryption fails.
    """
    resp = supabase_admin.rpc(
        "saas_load_credentials",
        {
            "p_connection_id": connection_id,
            "p_user_id": user_id,
            "p_key": _vault_key(),
        },
    ).execute()
    data: Any = resp.data
    if data is None:
        raise PermissionError("Connection not found or not owned by this user")
    if isinstance(data, str):
        return json.loads(data)
    return data
