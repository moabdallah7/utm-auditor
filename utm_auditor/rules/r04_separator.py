from utm_auditor.models import UTM_PARAMS, Config, Finding, RowData
from utm_auditor.rules.registry import effective_severity, register

_RULE_ID = "separator_violation"


@register(_RULE_ID, "warning")
def check(rows: list[RowData], config: Config) -> list[Finding]:
    severity = effective_severity(_RULE_ID, "warning", config)
    findings: list[Finding] = []
    for row in rows:
        if row.parsed is None:
            continue
        for param in UTM_PARAMS:
            value = row.parsed.query_params.get(param)
            if value is None:
                continue
            reason = _issue(value, config.separator)
            if reason:
                findings.append(
                    Finding(
                        row_index=row.index,
                        url=row.url,
                        rule_id=_RULE_ID,
                        severity=severity,
                        message=f"{param}={value!r}: {reason}",
                        suggested_fix=_fix(param, value, config.separator),
                    )
                )
    return findings


def _issue(value: str, separator: str) -> str | None:
    if value != value.strip():
        return "has leading or trailing whitespace"
    if " " in value:
        return "contains embedded spaces"
    # Whitespace checks are independent of separator config.
    # _ vs - checks respect separator; "any" disables them.
    if separator == "underscore":
        if "_" in value and "-" in value:
            return "mixes underscores and hyphens (configured separator: underscore)"
        if "-" in value:
            return "uses hyphens; configured separator is underscore"
    elif separator == "hyphen":
        if "_" in value and "-" in value:
            return "mixes underscores and hyphens (configured separator: hyphen)"
        if "_" in value:
            return "uses underscores; configured separator is hyphen"
    return None


def _fix(param: str, value: str, separator: str) -> str:
    fixed = value.strip()
    # Replace spaces with the configured separator character.
    sep_char = "-" if separator == "hyphen" else "_"
    fixed = fixed.replace(" ", sep_char)
    if separator == "underscore":
        fixed = fixed.replace("-", "_")
    elif separator == "hyphen":
        fixed = fixed.replace("_", "-")
    return f"Change to {param}={fixed!r}"
