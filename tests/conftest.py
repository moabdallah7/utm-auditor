"""Shared pytest fixtures and helpers."""
from __future__ import annotations

from pathlib import Path

from utm_auditor.models import Config, RowData

FIXTURES = Path(__file__).parent / "fixtures"


def make_row(
    index: int,
    url: str,
    extra: dict[str, str] | None = None,
) -> RowData:
    from utm_auditor.parsing.url_parser import parse_url

    raw: dict[str, str] = {"url": url}
    if extra:
        raw.update(extra)
    return RowData(index=index, raw=raw, url=url, parsed=parse_url(url))


def default_config(**kwargs: object) -> Config:
    cfg = Config.defaults()
    for k, v in kwargs.items():
        setattr(cfg, k, v)
    return cfg
