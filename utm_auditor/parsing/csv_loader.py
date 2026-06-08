from __future__ import annotations

import csv
import io
from pathlib import Path
from urllib.parse import urlparse

from utm_auditor.models import RowData
from utm_auditor.parsing.url_parser import parse_url


def load_csv(path: Path, url_column: str | None = None) -> tuple[list[RowData], str]:
    """Load a CSV file and return (rows, resolved_url_column_name).

    Raises ValueError with a clear message for:
    - unreadable file
    - empty file / no headers
    - duplicate column headers
    - missing or ambiguous URL column
    """
    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"Cannot read input file {path}: {exc}") from exc

    reader = csv.DictReader(io.StringIO(content))

    # Accessing fieldnames triggers reading the header row.
    if reader.fieldnames is None:
        raise ValueError(f"{path} is empty (no headers found)")

    headers: list[str] = list(reader.fieldnames)

    seen: set[str] = set()
    dupes: list[str] = []
    for h in headers:
        if h in seen:
            dupes.append(h)
        else:
            seen.add(h)
    if dupes:
        raise ValueError(f"Duplicate column headers in {path}: {dupes}")

    rows_raw: list[dict[str, str]] = [
        {k: (v or "") for k, v in row.items()} for row in reader
    ]

    if url_column is not None:
        if url_column not in headers:
            raise ValueError(
                f"--url-column {url_column!r} not found. "
                f"Available columns: {headers}"
            )
        resolved_col = url_column
    else:
        resolved_col = _resolve_url_column(headers, rows_raw, path)

    rows: list[RowData] = []
    for i, raw in enumerate(rows_raw):
        url_val = raw.get(resolved_col, "") or ""
        parsed = parse_url(url_val)
        rows.append(RowData(index=i, raw=raw, url=url_val, parsed=parsed))

    return rows, resolved_col


def _resolve_url_column(
    headers: list[str], rows: list[dict[str, str]], path: Path
) -> str:
    # Prefer the literal column named "url" to avoid false-positive detection.
    if "url" in headers:
        return "url"

    candidates: list[str] = []
    for col in headers:
        non_empty = [r[col] for r in rows if r.get(col, "").strip()]
        if not non_empty:
            continue
        url_like = sum(1 for v in non_empty if _looks_like_url(v))
        if url_like / len(non_empty) >= 0.8:
            candidates.append(col)

    if not candidates:
        raise ValueError(
            f"No URL column found in {path}. "
            "Use --url-column to specify the column name. "
            "URL columns must contain absolute URLs with a scheme (http/https) and hostname."
        )
    if len(candidates) > 1:
        raise ValueError(
            f"Multiple URL-like columns found in {path}: {candidates}. "
            "Use --url-column to specify which one to audit."
        )
    return candidates[0]


def _looks_like_url(value: str) -> bool:
    try:
        r = urlparse(value.strip())
        return bool(r.scheme in ("http", "https") and r.netloc)
    except Exception:
        return False
