from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path
from urllib.parse import parse_qsl, quote, urlencode, urlparse, urlunparse

from utm_auditor.models import UTM_PARAMS, Config, Finding, RowData

_SEVERITY_RANK: dict[str, int] = {"error": 0, "warning": 1, "info": 2}


def render_cleaned_csv(
    rows: list[RowData],
    findings: list[Finding],
    config: Config,
    path: Path,
    url_column: str,
) -> None:
    """Write a cleaned CSV to path.

    Each output row contains the original columns (with the URL column replaced
    by the normalized URL), plus three appended audit columns:
      audit_status   — worst severity across findings for this row, or "clean"
      audit_findings — semicolon-separated rule_ids that fired
      audit_changes  — semicolon-separated description of normalizations applied
    """
    by_row: dict[int, list[Finding]] = defaultdict(list)
    for f in findings:
        by_row[f.row_index].append(f)

    original_headers = list(rows[0].raw.keys()) if rows else []
    fieldnames = original_headers + ["audit_status", "audit_findings", "audit_changes"]

    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            row_findings = by_row[row.index]

            if row.parsed is not None:
                normalized_url, changes = _normalize_url(row.url, config)
            else:
                normalized_url = row.url
                changes = []

            if not row_findings:
                status = "clean"
            else:
                worst = min(row_findings, key=lambda f: _SEVERITY_RANK[f.severity])
                status = worst.severity

            out: dict[str, str] = dict(row.raw)
            out[url_column] = normalized_url
            out["audit_status"] = status
            out["audit_findings"] = "; ".join(sorted({f.rule_id for f in row_findings}))
            out["audit_changes"] = "; ".join(changes)
            writer.writerow(out)


def _normalize_url(url: str, config: Config) -> tuple[str, list[str]]:
    """Return (normalized_url, list_of_human_readable_changes)."""
    changes: list[str] = []
    try:
        parsed = urlparse(url)
    except Exception:
        return url, []

    pairs = parse_qsl(parsed.query, keep_blank_values=True)
    new_pairs: list[tuple[str, str]] = []

    for key, value in pairs:
        if key not in UTM_PARAMS:
            new_pairs.append((key, value))
            continue

        new_value = value

        stripped = new_value.strip()
        if stripped != new_value:
            changes.append(f"{key}: stripped whitespace")
            new_value = stripped

        casing_rule = config.casing.get(key, "any")
        if casing_rule == "lower" and new_value != new_value.lower():
            changes.append(f"{key}: lowercased")
            new_value = new_value.lower()
        elif casing_rule == "upper" and new_value != new_value.upper():
            changes.append(f"{key}: uppercased")
            new_value = new_value.upper()

        if config.separator == "underscore" and "-" in new_value:
            changes.append(f"{key}: replaced hyphens with underscores")
            new_value = new_value.replace("-", "_")
        elif config.separator == "hyphen" and "_" in new_value:
            changes.append(f"{key}: replaced underscores with hyphens")
            new_value = new_value.replace("_", "-")

        new_pairs.append((key, new_value))

    new_query = urlencode(new_pairs, quote_via=quote)
    return urlunparse(parsed._replace(query=new_query)), changes
