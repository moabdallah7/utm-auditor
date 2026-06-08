from __future__ import annotations

from tests.conftest import make_row
from utm_auditor.models import Config
from utm_auditor.rules.r06_duplicates import check_duplicate_campaign, check_duplicate_url

_URL_A = "https://e.com?utm_source=google&utm_medium=cpc&utm_campaign=spring"
_URL_B = "https://e.com?utm_source=facebook&utm_medium=social&utm_campaign=spring"


# --- duplicate_campaign ---


def test_no_duplicates_no_findings():
    rows = [make_row(0, _URL_A), make_row(1, _URL_B.replace("spring", "summer"))]
    assert check_duplicate_campaign(rows, Config.defaults()) == []


def test_same_campaign_different_urls_flagged():
    rows = [make_row(0, _URL_A), make_row(1, _URL_B)]
    findings = check_duplicate_campaign(rows, Config.defaults())
    assert len(findings) == 2
    assert all(f.rule_id == "duplicate_campaign" for f in findings)
    assert "spring" in findings[0].message


def test_same_campaign_same_url_not_flagged():
    rows = [make_row(0, _URL_A), make_row(1, _URL_A)]
    assert check_duplicate_campaign(rows, Config.defaults()) == []


def test_missing_campaign_param_skipped():
    row = make_row(0, "https://e.com?utm_source=g&utm_medium=cpc")
    assert check_duplicate_campaign([row], Config.defaults()) == []


def test_malformed_row_skipped():
    rows = [make_row(0, "not-a-url"), make_row(1, _URL_A)]
    assert check_duplicate_campaign(rows, Config.defaults()) == []


# --- duplicate_url ---


def test_unique_urls_no_findings():
    rows = [make_row(0, _URL_A), make_row(1, _URL_B)]
    assert check_duplicate_url(rows, Config.defaults()) == []


def test_duplicate_url_flagged():
    rows = [make_row(0, _URL_A), make_row(1, _URL_A)]
    findings = check_duplicate_url(rows, Config.defaults())
    assert len(findings) == 2
    assert all(f.rule_id == "duplicate_url" for f in findings)
    assert all(str([0, 1]) in f.message for f in findings)


def test_empty_url_skipped():
    rows = [make_row(0, ""), make_row(1, "")]
    assert check_duplicate_url(rows, Config.defaults()) == []


def test_severity_override_campaign():
    config = Config(severity_overrides={"duplicate_campaign": "error"})
    rows = [make_row(0, _URL_A), make_row(1, _URL_B)]
    findings = check_duplicate_campaign(rows, config)
    assert all(f.severity == "error" for f in findings)
