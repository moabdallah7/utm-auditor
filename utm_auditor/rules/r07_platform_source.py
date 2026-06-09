from utm_auditor.models import Config, Finding, RowData
from utm_auditor.rules.registry import effective_severity, register

_ID_MISMATCH = "source_platform_mismatch"
_ID_UNKNOWN = "unknown_platform"


@register(_ID_MISMATCH, "warning")
def check_source_platform_mismatch(rows: list[RowData], config: Config) -> list[Finding]:
    """Flag rows where utm_source is not in the allow-list for the row's platform.

    No-op when platform_source_map is empty or the row has no platform column value.
    Rows with an unknown platform are flagged by unknown_platform instead; this rule
    skips them to avoid double-flagging.
    """
    if not config.platform_source_map:
        return []

    severity = effective_severity(_ID_MISMATCH, "warning", config)
    map_lower: dict[str, list[str]] = {
        k.lower(): [v.lower() for v in vs] for k, vs in config.platform_source_map.items()
    }

    findings: list[Finding] = []
    for row in rows:
        if row.parsed is None:
            continue
        platform_raw = row.raw.get("platform", "").strip()
        if not platform_raw:
            continue
        platform_key = platform_raw.lower()
        if platform_key not in map_lower:
            continue  # unknown_platform rule handles this

        allowed_sources = map_lower[platform_key]
        source_raw = row.parsed.query_params.get("utm_source", "")
        if not source_raw:
            continue  # missing utm_source is caught by missing_required_utm

        if source_raw.lower() not in allowed_sources:
            friendly = sorted(config.platform_source_map.get(platform_raw, allowed_sources))
            findings.append(
                Finding(
                    row_index=row.index,
                    url=row.url,
                    rule_id=_ID_MISMATCH,
                    severity=severity,
                    message=(
                        f"utm_source={source_raw!r} is not an expected source "
                        f"for platform={platform_raw!r} "
                        f"(allowed: {sorted(allowed_sources)})"
                    ),
                    suggested_fix=f"Change utm_source to one of: {friendly}",
                )
            )
    return findings


@register(_ID_UNKNOWN, "info")
def check_unknown_platform(rows: list[RowData], config: Config) -> list[Finding]:
    """Flag platform column values that have no entry in platform_source_map.

    Severity is info by default: it indicates a coverage gap in the config rather
    than a definite tracking error.  The source-mismatch check is skipped for these
    rows because there is nothing to compare against.
    """
    if not config.platform_source_map:
        return []

    severity = effective_severity(_ID_UNKNOWN, "info", config)
    map_keys_lower = {k.lower() for k in config.platform_source_map}
    known = sorted(config.platform_source_map.keys())

    findings: list[Finding] = []
    for row in rows:
        if row.parsed is None:
            continue
        platform_raw = row.raw.get("platform", "").strip()
        if not platform_raw:
            continue
        if platform_raw.lower() not in map_keys_lower:
            findings.append(
                Finding(
                    row_index=row.index,
                    url=row.url,
                    rule_id=_ID_UNKNOWN,
                    severity=severity,
                    message=(
                        f"Platform {platform_raw!r} is not in platform_source_map (known: {known})"
                    ),
                    suggested_fix=(
                        f"Add {platform_raw!r} to platform_source_map in conventions.json"
                    ),
                )
            )
    return findings
