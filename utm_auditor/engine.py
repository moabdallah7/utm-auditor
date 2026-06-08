from __future__ import annotations

import utm_auditor.rules  # noqa: F401 — side-effect: registers all rule modules
from utm_auditor.models import Config, Finding, RowData
from utm_auditor.rules.registry import all_rules


def run_audit(
    rows: list[RowData],
    config: Config,
    disabled_rules: set[str] | None = None,
) -> list[Finding]:
    """Run all registered rules against rows and return a sorted finding list.

    Findings are sorted by (row_index, rule_id) for deterministic output
    regardless of rule registration order or Python dict ordering.
    """
    disabled = disabled_rules or set()
    findings: list[Finding] = []

    for rule_id, (rule_fn, _default) in all_rules().items():
        if rule_id in disabled:
            continue
        findings.extend(rule_fn(rows, config))

    findings.sort(key=lambda f: (f.row_index, f.rule_id))
    return findings
