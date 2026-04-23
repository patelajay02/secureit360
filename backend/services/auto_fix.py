"""Auto-fix handler registry.

Every finding that carries auto_fixable=true must have a handler
registered here. When the customer clicks Auto Fix on the dashboard or
the SaaS connections page, the backend route looks up the handler by
(engine, check_key) and calls it with the finding row.

Current state: no handlers are registered. The honest audit done at
build time concluded every existing scan finding requires an action we
cannot take on the customer's behalf (DNS changes, hosting changes,
write-scoped admin API tokens we do not hold, etc.). The registry and
endpoints ship anyway so future fixes can be added without another UI
round-trip.

To add a handler:

    @register_scan_fix("website", "security_headers_missing")
    def _fix_headers(finding: dict) -> dict:
        ...  # perform the fix
        return {"message": "Added recommended headers on the edge CDN."}
"""

from __future__ import annotations

from typing import Any, Callable


ScanFixHandler = Callable[[dict[str, Any]], dict[str, Any]]
SaasFixHandler = Callable[[dict[str, Any]], dict[str, Any]]


# Keyed by (engine, check_key). check_key is engine-specific and must
# match whatever the handler logic branches on (typically a normalized
# slug derived from the finding title, or the engine name itself when
# the engine produces only one shape of finding).
SCAN_FIX_HANDLERS: dict[tuple[str, str], ScanFixHandler] = {}

# Keyed by check_id, matching saas_findings.check_id directly.
SAAS_FIX_HANDLERS: dict[str, SaasFixHandler] = {}


def register_scan_fix(engine: str, check_key: str):
    def decorator(fn: ScanFixHandler) -> ScanFixHandler:
        SCAN_FIX_HANDLERS[(engine, check_key)] = fn
        return fn

    return decorator


def register_saas_fix(check_id: str):
    def decorator(fn: SaasFixHandler) -> SaasFixHandler:
        SAAS_FIX_HANDLERS[check_id] = fn
        return fn

    return decorator


def run_scan_fix(finding: dict[str, Any]) -> dict[str, Any]:
    """Dispatch an auto-fix for a row from the `findings` table.

    Raises RuntimeError if no handler is registered for the finding.
    Returns the handler's result dict (typically contains a human-readable
    `message`). Callers should mark status='auto_resolved' on success.
    """
    engine = finding.get("engine") or ""
    check_key = _derive_scan_check_key(finding)
    handler = SCAN_FIX_HANDLERS.get((engine, check_key))
    if not handler:
        raise RuntimeError(
            f"No auto-fix handler registered for {engine}/{check_key}"
        )
    return handler(finding) or {}


def run_saas_fix(finding: dict[str, Any]) -> dict[str, Any]:
    check_id = finding.get("check_id") or ""
    handler = SAAS_FIX_HANDLERS.get(check_id)
    if not handler:
        raise RuntimeError(f"No auto-fix handler registered for SaaS/{check_id}")
    return handler(finding) or {}


def _derive_scan_check_key(finding: dict[str, Any]) -> str:
    """Best-effort slug used to look up a handler. Engines that only
    emit one finding shape can register with check_key equal to the
    engine name. Multi-finding engines should register a key that matches
    what this function returns."""
    title = (finding.get("title") or "").lower()
    if not title:
        return finding.get("engine", "")
    # First 40 chars normalized; handlers key themselves off the prefix
    # unique to their finding type.
    slug = title[:40].replace("  ", " ").strip().replace(" ", "_")
    return slug
