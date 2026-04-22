-- SecureIT360 Universal SaaS Connector — Step 2
-- pgcrypto helper RPCs used by backend/saas_connectors/credential_vault.py
-- Plaintext credentials only cross the wire to these SECURITY DEFINER
-- functions; pgp_sym_encrypt/pgp_sym_decrypt run inline in Postgres.
--
-- Supabase installs pgcrypto into the "extensions" schema, so every
-- pgcrypto call is qualified as extensions.pgp_sym_* and each function
-- sets search_path = public, extensions as a belt-and-braces measure.

create extension if not exists pgcrypto with schema extensions;

-- ── Primitive encrypt / decrypt helpers ────────────────────────────────────
-- Return ciphertext as base64-encoded text so PostgREST can marshal it
-- over JSON safely. Python side base64-decodes before storing as bytea.

create or replace function public.saas_encrypt(p_plaintext text, p_key text)
returns text
language sql
security definer
set search_path = public, extensions
as $$
    select encode(extensions.pgp_sym_encrypt(p_plaintext, p_key), 'base64');
$$;

create or replace function public.saas_decrypt(p_ciphertext text, p_key text)
returns text
language sql
security definer
set search_path = public, extensions
as $$
    select extensions.pgp_sym_decrypt(decode(p_ciphertext, 'base64')::bytea, p_key);
$$;

-- ── Atomic store / load ────────────────────────────────────────────────────
-- store_connection performs the pgp_sym_encrypt inside the INSERT so the
-- plaintext is never returned to the client after insertion.

create or replace function public.saas_store_connection(
    p_user_id uuid,
    p_app_slug text,
    p_app_name text,
    p_connection_type text,
    p_plaintext_json text,
    p_key text
)
returns uuid
language plpgsql
security definer
set search_path = public, extensions
as $$
declare
    v_id uuid;
begin
    insert into public.saas_connections (
        user_id, app_slug, app_name, connection_type, encrypted_credentials
    )
    values (
        p_user_id,
        p_app_slug,
        p_app_name,
        p_connection_type,
        extensions.pgp_sym_encrypt(p_plaintext_json, p_key)
    )
    returning id into v_id;
    return v_id;
end;
$$;

-- load_credentials returns the decrypted JSON only when the connection
-- belongs to the caller's user. The check is done inside the SECURITY
-- DEFINER function so the vault key never has to leave Postgres.

create or replace function public.saas_load_credentials(
    p_connection_id uuid,
    p_user_id uuid,
    p_key text
)
returns jsonb
language plpgsql
security definer
set search_path = public, extensions
as $$
declare
    v_cipher bytea;
begin
    select encrypted_credentials into v_cipher
    from public.saas_connections
    where id = p_connection_id and user_id = p_user_id;

    if v_cipher is null then
        return null;
    end if;

    return extensions.pgp_sym_decrypt(v_cipher, p_key)::jsonb;
end;
$$;

-- ── Execute grants ─────────────────────────────────────────────────────────
-- Service role already bypasses RLS, but make sure the RPCs are reachable
-- for authenticated users so the backend can call them with a user JWT if
-- we ever move off the admin client.

grant execute on function public.saas_encrypt(text, text) to authenticated, service_role;
grant execute on function public.saas_decrypt(text, text) to authenticated, service_role;
grant execute on function public.saas_store_connection(uuid, text, text, text, text, text) to authenticated, service_role;
grant execute on function public.saas_load_credentials(uuid, uuid, text) to authenticated, service_role;
