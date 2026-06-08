from utm_auditor.models import Config, Finding, RowData
from utm_auditor.rules.registry import effective_severity, register

_RULE_ID = "casing_violation"


@register(_RULE_ID, "warning")
def check(rows: list[RowData], config: Config) -> list[Finding]:
    severity = effective_severity(_RULE_ID, "warning", config)
    findings: list[Finding] = []
    for row in rows:
        if row.parsed is None:
            continue
        for param, rule in config.casing.items():
            if rule == "any":
                continue
            value = row.parsed.query_params.get(param)
            if value is None:
                continue  # absence handled by missing_required_utm
            if rule == "lower" and value != value.lower():
                findings.append(
                    Finding(
                        row_index=row.index,
                        url=row.url,
                        rule_id=_RULE_ID,
                        severity=severity,
                        message=f"{param}={value!r} must be lowercase",
                        suggested_fix=f"Change to {param}={value.lower()!r}",
                    )
                )
            elif rule == "upper" and value != value.upper():
                findings.append(
                    Finding(
                        row_index=row.index,
                        url=row.url,
                        rule_id=_RULE_ID,
                        severity=severity,
                        message=f"{param}={value!r} must be uppercase",
                        suggested_fix=f"Change to {param}={value.upper()!r}",
                    )
                )
    return findings
