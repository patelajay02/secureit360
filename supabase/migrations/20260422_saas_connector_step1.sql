-- SecureIT360 Universal SaaS Connector — Step 1
-- Creates saas_connections, saas_app_registry, saas_findings
-- Extends delete_user_completely to clean up SaaS connections

-- ── Extensions ─────────────────────────────────────────────────────────────

create extension if not exists pgcrypto;

-- ── saas_connections ───────────────────────────────────────────────────────

create table if not exists public.saas_connections (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users(id) on delete cascade,
    app_slug text not null,
    app_name text not null,
    connection_type text not null check (connection_type in ('oauth', 'api_key')),
    encrypted_credentials bytea not null,
    status text not null default 'active' check (status in ('active', 'expired', 'failed')),
    last_scan_at timestamptz,
    created_at timestamptz not null default now()
);

create index if not exists saas_connections_user_id_idx
    on public.saas_connections (user_id);

-- ── saas_app_registry ──────────────────────────────────────────────────────

create table if not exists public.saas_app_registry (
    slug text primary key,
    name text not null,
    logo_url text,
    tier text not null check (tier in ('1_oauth', '2_manual')),
    oauth_config jsonb,
    wizard_recipe jsonb,
    generic_check_capabilities jsonb not null default '[]'::jsonb,
    verified boolean not null default false,
    created_at timestamptz not null default now()
);

-- ── saas_findings ──────────────────────────────────────────────────────────

create table if not exists public.saas_findings (
    id uuid primary key default gen_random_uuid(),
    connection_id uuid not null references public.saas_connections(id) on delete cascade,
    check_id text not null,
    severity text not null check (severity in ('critical', 'high', 'medium', 'low', 'info')),
    governance_statement text not null,
    technical_detail text,
    recommended_action text not null,
    regulation_refs jsonb not null default '[]'::jsonb,
    created_at timestamptz not null default now()
);

create index if not exists saas_findings_connection_id_idx
    on public.saas_findings (connection_id);

-- ── delete_user_completely RPC ─────────────────────────────────────────────
-- Full replacement. Cascades through every tenant-scoped table this app
-- writes to, then removes the owner's tenant, the user's tenant_user rows,
-- and any SaaS connections the user owns (saas_findings cascade via FK).

create or replace function public.delete_user_completely(p_user_id uuid)
returns void
language plpgsql
security definer
set search_path = public
as $$
declare
    v_tenant_id uuid;
    v_domain_ids uuid[];
    v_scan_ids uuid[];
begin
    -- Find the tenant this user owns (if any) and cascade its data
    select tenant_id into v_tenant_id
    from public.tenant_users
    where user_id = p_user_id and role = 'owner'
    limit 1;

    if v_tenant_id is not null then
        select coalesce(array_agg(id), '{}') into v_domain_ids
        from public.domains
        where tenant_id = v_tenant_id;

        select coalesce(array_agg(id), '{}') into v_scan_ids
        from public.scans
        where tenant_id = v_tenant_id;

        -- Per-scan children
        if array_length(v_scan_ids, 1) is not null then
            delete from public.findings where scan_id = any(v_scan_ids);
            delete from public.scan_engine_results where scan_id = any(v_scan_ids);
        end if;

        -- Any tenant-level findings not tied to a scan
        delete from public.findings where tenant_id = v_tenant_id;
        delete from public.scan_engine_results where tenant_id = v_tenant_id;

        delete from public.scans where tenant_id = v_tenant_id;
        delete from public.domains where tenant_id = v_tenant_id;
        delete from public.integrations where tenant_id = v_tenant_id;
        delete from public.tenant_users where tenant_id = v_tenant_id;
        delete from public.tenants where id = v_tenant_id;
    end if;

    -- Any tenant_user rows where the user isn't the owner (secondary memberships)
    delete from public.tenant_users where user_id = p_user_id;

    -- SaaS connector data for this user (saas_findings cascade via FK)
    delete from public.saas_connections where user_id = p_user_id;

    -- Finally, the auth user
    delete from auth.users where id = p_user_id;
end;
$$;

-- ── Row-Level Security ─────────────────────────────────────────────────────

alter table public.saas_connections enable row level security;
alter table public.saas_app_registry enable row level security;
alter table public.saas_findings enable row level security;

-- saas_connections: users can only see/manage their own rows

drop policy if exists "saas_connections_select_own" on public.saas_connections;
create policy "saas_connections_select_own"
    on public.saas_connections
    for select
    using (auth.uid() = user_id);

drop policy if exists "saas_connections_insert_own" on public.saas_connections;
create policy "saas_connections_insert_own"
    on public.saas_connections
    for insert
    with check (auth.uid() = user_id);

drop policy if exists "saas_connections_update_own" on public.saas_connections;
create policy "saas_connections_update_own"
    on public.saas_connections
    for update
    using (auth.uid() = user_id)
    with check (auth.uid() = user_id);

drop policy if exists "saas_connections_delete_own" on public.saas_connections;
create policy "saas_connections_delete_own"
    on public.saas_connections
    for delete
    using (auth.uid() = user_id);

-- saas_findings: users can only see findings belonging to their own connections

drop policy if exists "saas_findings_select_own" on public.saas_findings;
create policy "saas_findings_select_own"
    on public.saas_findings
    for select
    using (
        exists (
            select 1
            from public.saas_connections c
            where c.id = saas_findings.connection_id
              and c.user_id = auth.uid()
        )
    );

drop policy if exists "saas_findings_insert_own" on public.saas_findings;
create policy "saas_findings_insert_own"
    on public.saas_findings
    for insert
    with check (
        exists (
            select 1
            from public.saas_connections c
            where c.id = saas_findings.connection_id
              and c.user_id = auth.uid()
        )
    );

drop policy if exists "saas_findings_update_own" on public.saas_findings;
create policy "saas_findings_update_own"
    on public.saas_findings
    for update
    using (
        exists (
            select 1
            from public.saas_connections c
            where c.id = saas_findings.connection_id
              and c.user_id = auth.uid()
        )
    )
    with check (
        exists (
            select 1
            from public.saas_connections c
            where c.id = saas_findings.connection_id
              and c.user_id = auth.uid()
        )
    );

drop policy if exists "saas_findings_delete_own" on public.saas_findings;
create policy "saas_findings_delete_own"
    on public.saas_findings
    for delete
    using (
        exists (
            select 1
            from public.saas_connections c
            where c.id = saas_findings.connection_id
              and c.user_id = auth.uid()
        )
    );

-- saas_app_registry: public read (every authenticated user sees the catalog);
-- writes are admin-only via service role (which bypasses RLS)

drop policy if exists "saas_app_registry_public_read" on public.saas_app_registry;
create policy "saas_app_registry_public_read"
    on public.saas_app_registry
    for select
    using (true);
