-- SecureIT360 — add auto_fixable to findings + saas_findings.
-- Dashboard and SaaS UIs expose a three-button action row per finding
-- (Auto Fix / Voice Guide / Connect to Expert). Auto Fix only lights up
-- when the platform can genuinely remediate the finding on the customer's
-- behalf. Default false so every existing row correctly disables the button.
-- See backend/services/auto_fix.py for the handler registry; populate the
-- column from the relevant scan engine when adding a fix handler.

alter table public.findings
    add column if not exists auto_fixable boolean not null default false;

alter table public.saas_findings
    add column if not exists auto_fixable boolean not null default false;
