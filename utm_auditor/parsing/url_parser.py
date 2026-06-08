from __future__ import annotations

from urllib.parse import parse_qs, unquote, urlparse

from utm_auditor.models import ParsedURL


def parse_url(raw: str) -> ParsedURL | None:
    """Parse a URL string into a ParsedURL.

    Returns None for URLs that are empty, unparseable, missing scheme/host,
    or have undecodable query strings.  The malformed_url rule independently
    computes a human-readable reason for the same set of conditions.
    """
    if not raw or not raw.strip():
        return None

    stripped = raw.strip()

    try:
        result = urlparse(stripped)
    except Exception:
        return None

    if not result.scheme or not result.netloc:
        return None

    try:
        qs = parse_qs(result.query, keep_blank_values=True, strict_parsing=False)
        # Take first value for each key; preserve parse order (3.7+ dict is ordered).
        params: dict[str, str] = {k: v[0] for k, v in qs.items()}
    except Exception:
        return None

    # Validate percent-encoding in the query string.
    try:
        unquote(result.query, errors="strict")
    except (UnicodeDecodeError, ValueError):
        return None

    return ParsedURL(scheme=result.scheme, netloc=result.netloc, query_params=params)


def malformed_reason(raw: str) -> str | None:
    """Return a human-readable reason if the URL is malformed, else None.

    Mirrors the exact conditions under which parse_url returns None, plus
    produces messages for the terminal report.
    """
    if not raw or not raw.strip():
        return "URL is empty"

    stripped = raw.strip()

    try:
        result = urlparse(stripped)
    except Exception as exc:
        return f"unparseable: {exc}"

    if not result.scheme:
        return "missing URL scheme (expected https://)"
    if not result.netloc:
        return "missing host"

    try:
        parse_qs(result.query, keep_blank_values=True, strict_parsing=False)
    except Exception as exc:
        return f"undecodable query string: {exc}"

    try:
        unquote(result.query, errors="strict")
    except (UnicodeDecodeError, ValueError):
        return "query string contains invalid percent-encoding"

    return None
