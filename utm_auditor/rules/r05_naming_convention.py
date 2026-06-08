from __future__ import annotations

import re

from utm_auditor.models import Config, Finding, RowData
from utm_auditor.rules.registry import effective_severity, register

_RULE_ID = "naming_convention_violation"


@register(_RULE_ID, "warning")
def check(rows: list[RowData], config: Config) -> list[Finding]:
    severity = effective_severity(_RULE_ID, "warning", config)
    compiled = re.compile(config.campaign_pattern) if config.campaign_pattern else None
    findings: list[Finding] = []

    for row in rows:
        if row.parsed is None:
            continue

        # Allow-list checks: membership is case-insensitive.
        for param, allowed in config.allowed_values.items():
            value = row.parsed.query_params.get(param)
            if value is None:
                continue
            allowed_lower = [a.lower() for a in allowed]
            if value.lower() not in allowed_lower:
                findings.append(
                    Finding(
                        row_index=row.index,
                        url=row.url,
                        rule_id=_RULE_ID,
                        severity=severity,
                        message=(
                            f"{param}={value!r} is not in the allowed-values list "
                            f"(allowed: {sorted(allowed_lower)})"
                        ),
                        suggested_fix=f"Use one of: {sorted(allowed_lower)}",
                    )
                )

        # Campaign pattern check (full match).
        if compiled is not None:
            campaign = row.parsed.query_params.get("utm_campaign")
            if campaign is not None and not compiled.fullmatch(campaign):
                findings.append(
                    Finding(
                        row_index=row.index,
                        url=row.url,
                        rule_id=_RULE_ID,
                        severity=severity,
                        message=(
                            f"utm_campaign={campaign!r} does not match "
                            f"required pattern {config.campaign_pattern!r}"
                        ),
                        suggested_fix=f"Rename to match: {config.campaign_pattern}",
                    )
                )

    return findings
