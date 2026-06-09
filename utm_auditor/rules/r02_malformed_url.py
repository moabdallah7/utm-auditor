from utm_auditor.models import Config, Finding, RowData
from utm_auditor.parsing.url_parser import malformed_reason
from utm_auditor.rules.registry import effective_severity, register

_RULE_ID = "malformed_url"


@register(_RULE_ID, "error")
def check(rows: list[RowData], config: Config) -> list[Finding]:
    severity = effective_severity(_RULE_ID, "error", config)
    findings: list[Finding] = []
    for row in rows:
        reason = malformed_reason(row.url)
        if reason:
            findings.append(
                Finding(
                    row_index=row.index,
                    url=row.url,
                    rule_id=_RULE_ID,
                    severity=severity,
                    message=f"Malformed URL: {reason}",
                    suggested_fix=("Ensure the URL starts with https:// and has a valid hostname"),
                )
            )
    return findings
