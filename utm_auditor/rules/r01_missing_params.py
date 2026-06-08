from utm_auditor.models import Config, Finding, RowData
from utm_auditor.rules.registry import effective_severity, register

_RULE_ID = "missing_required_utm"
_DEFAULT: str = "error"


@register(_RULE_ID, "error")
def check(rows: list[RowData], config: Config) -> list[Finding]:
    severity = effective_severity(_RULE_ID, "error", config)
    findings: list[Finding] = []
    for row in rows:
        if row.parsed is None:
            continue  # malformed_url rule handles unparseable rows
        for param in config.required_params:
            if param not in row.parsed.query_params:
                findings.append(
                    Finding(
                        row_index=row.index,
                        url=row.url,
                        rule_id=_RULE_ID,
                        severity=severity,
                        message=f"Missing required UTM parameter: {param!r}",
                        suggested_fix=f"Add {param}=<value> to the URL query string",
                    )
                )
    return findings
