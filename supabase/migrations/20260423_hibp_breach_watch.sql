-- SecureIT360 — Real-time HIBP breach watch
-- Two tables that back the 5-minute scheduler in
-- backend/services/hibp_watch.py:
--   * hibp_breach_watch  : per-domain marker of the most recent HIBP
--                          breach we've already alerted on, so the
--                          scheduler can detect "anything newer" cheaply
--   * hibp_breach_alerts : history log of every critical alert email
--                          fired, used by the dashboard tile
--
-- Both tables are written by the Railway backend via the service role
-- (which bypasses RLS). The RLS policies below only need to grant
-- tenant-scoped READ access so the dashboard tile can render.

-- ── hibp_breach_watch ──────────────────────────────────────────────────────

create table if not exists public.hibp_breach_watch (
    id uuid primary key default gen_random_uuid(),
    tenant_id uuid not null references public.tenants(id) on delete cascade,
    domain text not null,
    last_checked_breach_name text,
    last_checked_at timestamptz default now(),
    created_at timestamptz default now(),
    unique (tenant_id, domain)
);

create index if not exists hibp_breach_watch_tenant_id_idx
    on public.hibp_breach_watch (tenant_id);

-- ── hibp_breach_alerts ─────────────────────────────────────────────────────

create table if not exists public.hibp_breach_alerts (
    id uuid primary key default gen_random_uuid(),
    tenant_id uuid not null references public.tenants(id) on delete cascade,
    breach_name text not null,
    breach_date date,
    pwn_count bigint,
    affected_emails int default 0,
    alert_sent_at timestamptz default now(),
    email_recipient text,
    created_at timestamptz default now()
);

create index if not exists hibp_breach_alerts_tenant_id_idx
    on public.hibp_breach_alerts (tenant_id);

create index if not exists hibp_breach_alerts_alert_sent_at_idx
    on public.hibp_breach_alerts (alert_sent_at desc);

-- ── Row-Level Security ─────────────────────────────────────────────────────
-- A user can read rows belonging to any tenant they're an active member of.
-- All writes happen via the service role on the Railway backend, which
-- bypasses RLS, so we deliberately do not expose insert/update/delete
-- policies — the frontend has no business writing these rows directly.

alter table public.hibp_breach_watch enable row level security;
alter table public.hibp_breach_alerts enable row level security;

drop policy if exists "hibp_breach_watch_select_own_tenant"
    on public.hibp_breach_watch;
create policy "hibp_breach_watch_select_own_tenant"
    on public.hibp_breach_watch
    for select
    using (
        tenant_id in (
            select tenant_id
            from public.tenant_users
            where user_id = auth.uid() and status = 'active'
        )
    );

drop policy if exists "hibp_breach_alerts_select_own_tenant"
    on public.hibp_breach_alerts;
create policy "hibp_breach_alerts_select_own_tenant"
    on public.hibp_breach_alerts
    for select
    using (
        tenant_id in (
            select tenant_id
            from public.tenant_users
            where user_id = auth.uid() and status = 'active'
        )
    );

-- ── Backfill: existing verified domains ────────────────────────────────────
-- Tenants that verified domains before this migration ran would otherwise
-- be invisible to the 5-minute scheduler until they re-verified. Seed one
-- row per (tenant_id, domain) for everything currently verified.
-- last_checked_breach_name stays NULL on these rows, which trips the
-- first-run protection inside hibp_watch.py — the next scheduler tick
-- silently primes each row to the current state instead of replaying
-- every historical breach as a fresh critical alert.

insert into public.hibp_breach_watch (tenant_id, domain)
select tenant_id, domain
from public.domains
where verified = true
on conflict (tenant_id, domain) do nothing;
