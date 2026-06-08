from __future__ import annotations

from tests.conftest import make_row
from utm_auditor.models import Config
from utm_auditor.rules.r03_casing import check


def test_clean_no_findings():
    row = make_row(0, "https://e.com?utm_source=google&utm_medium=cpc&utm_campaign=x")
    assert check([row], Config.defaults()) == []


def test_uppercase_source_flagged():
    row = make_row(0, "https://e.com?utm_source=Google&utm_medium=cpc&utm_campaign=x")
    findings = check([row], Config.defaults())
    assert len(findings) == 1
    assert "utm_source" in findings[0].message
    assert findings[0].suggested_fix == "Change to utm_source='google'"


def test_uppercase_medium_flagged():
    row = make_row(0, "https://e.com?utm_source=google&utm_medium=CPC&utm_campaign=x")
    findings = check([row], Config.defaults())
    assert len(findings) == 1
    assert "utm_medium" in findings[0].message


def test_campaign_not_checked_by_default():
    # Default config has no casing rule for utm_campaign.
    row = make_row(0, "https://e.com?utm_source=google&utm_medium=cpc&utm_campaign=SPRING")
    assert check([row], Config.defaults()) == []


def test_upper_rule():
    config = Config(casing={"utm_source": "upper"})
    row = make_row(0, "https://e.com?utm_source=google&utm_medium=cpc&utm_campaign=x")
    findings = check([row], config)
    assert len(findings) == 1
    assert findings[0].suggested_fix == "Change to utm_source='GOOGLE'"


def test_any_rule_skipped():
    config = Config(casing={"utm_source": "any"})
    row = make_row(0, "https://e.com?utm_source=Google&utm_medium=cpc&utm_campaign=x")
    assert check([row], config) == []


def test_missing_param_not_flagged():
    # utm_source absent — missing_required_utm handles it; casing must not fire.
    row = make_row(0, "https://e.com?utm_medium=cpc&utm_campaign=x")
    assert check([row], Config.defaults()) == []


def test_malformed_row_skipped():
    row = make_row(0, "not-a-url")
    assert check([row], Config.defaults()) == []


def test_severity_override():
    config = Config(severity_overrides={"casing_violation": "error"})
    row = make_row(0, "https://e.com?utm_source=Google&utm_medium=cpc&utm_campaign=x")
    findings = check([row], config)
    assert findings[0].severity == "error"
