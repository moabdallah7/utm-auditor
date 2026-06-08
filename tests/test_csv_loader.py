from __future__ import annotations

import pytest

from tests.conftest import FIXTURES
from utm_auditor.parsing.csv_loader import load_csv


def test_clean_file_loads():
    rows, col = load_csv(FIXTURES / "clean.csv")
    assert col == "url"
    assert len(rows) == 3
    assert rows[0].index == 0
    assert rows[0].parsed is not None


def test_header_only_returns_empty_rows():
    rows, col = load_csv(FIXTURES / "header_only.csv")
    assert rows == []
    assert col == "url"


def test_empty_file_raises():
    with pytest.raises(ValueError, match="empty"):
        load_csv(FIXTURES / "empty.csv")


def test_explicit_url_column():
    rows, col = load_csv(FIXTURES / "clean.csv", url_column="url")
    assert col == "url"
    assert len(rows) == 3


def test_explicit_url_column_missing_raises():
    with pytest.raises(ValueError, match="not found"):
        load_csv(FIXTURES / "clean.csv", url_column="landing_url")


def test_unknown_columns_passed_through():
    rows, _ = load_csv(FIXTURES / "clean.csv")
    assert "platform" in rows[0].raw
    assert "campaign_id" in rows[0].raw


def test_non_ascii_loads():
    rows, _ = load_csv(FIXTURES / "non_ascii.csv")
    assert len(rows) == 2


def test_no_query_urls_load():
    rows, _ = load_csv(FIXTURES / "no_query.csv")
    assert len(rows) == 2
    # No UTM params → parsed succeeds but query_params is empty.
    assert rows[0].parsed is not None
    assert rows[0].parsed.query_params == {}


def test_duplicate_headers_raises(tmp_path):
    csv_file = tmp_path / "dup.csv"
    csv_file.write_text("url,url\nhttps://a.com,https://b.com\n")
    with pytest.raises(ValueError, match="Duplicate column headers"):
        load_csv(csv_file)


def test_auto_detect_url_column(tmp_path):
    csv_file = tmp_path / "alt.csv"
    csv_file.write_text(
        "landing_url,name\n"
        "https://example.com?utm_source=x&utm_medium=cpc&utm_campaign=y,Campaign A\n"
    )
    rows, col = load_csv(csv_file)
    assert col == "landing_url"


def test_auto_detect_ambiguous_raises(tmp_path):
    csv_file = tmp_path / "two_urls.csv"
    csv_file.write_text(
        "url_a,url_b\n"
        "https://a.com?utm_source=x&utm_medium=cpc&utm_campaign=y,"
        "https://b.com?utm_source=x&utm_medium=cpc&utm_campaign=z\n"
    )
    with pytest.raises(ValueError, match="Multiple URL-like columns"):
        load_csv(csv_file)
