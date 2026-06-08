from __future__ import annotations

from tests.conftest import make_row
from utm_auditor.models import Config
from utm_auditor.rules.r05_naming_convention import check

_ALLOWED_CONFIG = Config(
    allowed_values={"utm_medium": ["cpc", "email", "social", "organic", "referral"]}
)
_PATTERN_CONFIG = Config(campaign_pattern=r"^[a-z0-9_]+$")


def test_no_config_no_findings():
    row = make_row(0, "https://e.com?utm_source=g&utm_medium=banner&utm_campaign=x")
    assert check([row], Config.defaults()) == []


def test_allowed_value_passes():
    row = make_row(0, "https://e.com?utm_source=g&utm_medium=cpc&utm_campaign=x")
    assert check([row], _ALLOWED_CONFIG) == []


def test_disallowed_value_flagged():
    row = make_row(0, "https://e.com?utm_source=g&utm_medium=banner&utm_campaign=x")
    findings = check([row], _ALLOWED_CONFIG)
    assert len(findings) == 1
    assert "banner" in findings[0].message


def test_allowed_check_is_case_insensitive():
    # "CPC" should pass the allow-list because membership is case-insensitive.
    row = make_row(0, "https://e.com?utm_source=g&utm_medium=CPC&utm_campaign=x")
    assert check([row], _ALLOWED_CONFIG) == []


def test_pattern_passes():
    row = make_row(0, "https://e.com?utm_source=g&utm_medium=cpc&utm_campaign=spring_2024")
    assert check([row], _PATTERN_CONFIG) == []


def test_pattern_violation_flagged():
    row = make_row(0, "https://e.com?utm_source=g&utm_medium=cpc&utm_campaign=SPRING SALE")
    findings = check([row], _PATTERN_CONFIG)
    assert len(findings) == 1
    assert "utm_campaign" in findings[0].message


def test_missing_utm_campaign_skips_pattern():
    row = make_row(0, "https://e.com?utm_source=g&utm_medium=cpc")
    assert check([row], _PATTERN_CONFIG) == []


def test_malformed_row_skipped():
    row = make_row(0, "not-a-url")
    assert check([row], _ALLOWED_CONFIG) == []


def test_severity_override():
    config = Config(
        allowed_values={"utm_medium": ["cpc"]},
        severity_overrides={"naming_convention_violation": "error"},
    )
    row = make_row(0, "https://e.com?utm_source=g&utm_medium=banner&utm_campaign=x")
    findings = check([row], config)
    assert findings[0].severity == "error"
