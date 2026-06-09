from __future__ import annotations

from collections import defaultdict

from utm_auditor.models import Config, Finding, RowData
from utm_auditor.rules.registry import effective_severity, register

_ID_CAMPAIGN = "duplicate_campaign"
_ID_URL = "duplicate_url"


@register(_ID_CAMPAIGN, "warning")
def check_duplicate_campaign(rows: list[RowData], config: Config) -> list[Finding]:
    """Flag when the same utm_campaign value appears on rows with different URLs.

    Identical duplicate rows are left to duplicate_url; this rule fires only when
    there are genuinely *differing* rows sharing a campaign name, which usually
    means attribution data will be ambiguous in the analytics tool.
    """
    severity = effective_severity(_ID_CAMPAIGN, "warning", config)

    by_campaign: dict[str, list[RowData]] = defaultdict(list)
    for row in rows:
        if row.parsed is None:
            continue
        campaign = row.parsed.query_params.get("utm_campaign")
        if campaign is not None:
            by_campaign[campaign].append(row)

    findings: list[Finding] = []
    for campaign, group in by_campaign.items():
        if len(group) <= 1:
            continue
        distinct_urls = {r.url for r in group}
        if len(distinct_urls) <= 1:
            continue  # all identical — duplicate_url covers this
        count = len(group)
        url_count = len(distinct_urls)
        for row in group:
            findings.append(
                Finding(
                    row_index=row.index,
                    url=row.url,
                    rule_id=_ID_CAMPAIGN,
                    severity=severity,
                    message=(
                        f"utm_campaign={campaign!r} appears {count} time(s) "
                        f"across {url_count} different URLs"
                    ),
                    suggested_fix=(
                        "Use a unique utm_campaign per campaign, "
                        "or verify that reuse is intentional"
                    ),
                )
            )
    return findings


@register(_ID_URL, "info")
def check_duplicate_url(rows: list[RowData], config: Config) -> list[Finding]:
    """Flag when the exact same URL (including all query params) appears more than once."""
    severity = effective_severity(_ID_URL, "info", config)

    by_url: dict[str, list[int]] = defaultdict(list)
    for row in rows:
        if row.url.strip():
            by_url[row.url].append(row.index)

    findings: list[Finding] = []
    for url, indices in by_url.items():
        if len(indices) <= 1:
            continue
        for idx in indices:
            findings.append(
                Finding(
                    row_index=idx,
                    url=url,
                    rule_id=_ID_URL,
                    severity=severity,
                    message=(f"Exact URL appears {len(indices)} time(s) (row indices: {indices})"),
                    suggested_fix="Remove duplicate rows or confirm intentional reuse",
                )
            )
    return findings
