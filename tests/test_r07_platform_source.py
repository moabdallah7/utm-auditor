from __future__ import annotations

from tests.conftest import make_row
from utm_auditor.models import Config
from utm_auditor.rules.r07_platform_source import (
    check_source_platform_mismatch,
    check_unknown_platform,
)

_MAP = {"google": ["google", "google_ads"], "facebook": ["facebook", "meta"]}
_CONFIG = Config(platform_source_map=_MAP)

_BASE = "https://e.com?utm_source={src}&utm_medium=cpc&utm_campaign=x"


# --- source_platform_mismatch ---


def test_empty_map_no_op():
    r = make_row(0, _BASE.format(src="fb"), {"platform": "google"})
    assert check_source_platform_mismatch([r], Config.defaults()) == []


def test_matching_source_passes():
    r = make_row(0, _BASE.format(src="google_ads"), {"platform": "google"})
    assert check_source_platform_mismatch([r], _CONFIG) == []


def test_mismatch_flagged():
    r = make_row(0, _BASE.format(src="facebook"), {"platform": "google"})
    findings = check_source_platform_mismatch([r], _CONFIG)
    assert len(findings) == 1
    assert findings[0].rule_id == "source_platform_mismatch"
    assert "facebook" in findings[0].message


def test_platform_case_insensitive():
    r = make_row(0, _BASE.format(src="google"), {"platform": "Google"})
    assert check_source_platform_mismatch([r], _CONFIG) == []


def test_source_case_insensitive():
    r = make_row(0, _BASE.format(src="GOOGLE"), {"platform": "google"})
    assert check_source_platform_mismatch([r], _CONFIG) == []


def test_no_platform_column_no_op():
    r = make_row(0, _BASE.format(src="facebook"))
    assert check_source_platform_mismatch([r], _CONFIG) == []


def test_missing_utm_source_skipped():
    url = "https://e.com?utm_medium=cpc&utm_campaign=x"
    r = make_row(0, url, {"platform": "google"})
    assert check_source_platform_mismatch([r], _CONFIG) == []


def test_unknown_platform_skipped_by_mismatch_rule():
    r = make_row(0, _BASE.format(src="tiktok"), {"platform": "tiktok"})
    assert check_source_platform_mismatch([r], _CONFIG) == []


# --- unknown_platform ---


def test_empty_map_no_op_unknown():
    url = "https://e.com?utm_source=x&utm_medium=cpc&utm_campaign=y"
    r = make_row(0, url, {"platform": "tiktok"})
    assert check_unknown_platform([r], Config.defaults()) == []


def test_known_platform_not_flagged():
    r = make_row(0, _BASE.format(src="google"), {"platform": "google"})
    assert check_unknown_platform([r], _CONFIG) == []


def test_unknown_platform_flagged():
    r = make_row(0, _BASE.format(src="tiktok"), {"platform": "tiktok"})
    findings = check_unknown_platform([r], _CONFIG)
    assert len(findings) == 1
    assert findings[0].rule_id == "unknown_platform"
    assert findings[0].severity == "info"


def test_unknown_platform_case_insensitive():
    r = make_row(0, _BASE.format(src="tiktok"), {"platform": "TikTok"})
    findings = check_unknown_platform([r], _CONFIG)
    assert len(findings) == 1


def test_severity_override_unknown():
    config = Config(
        platform_source_map=_MAP,
        severity_overrides={"unknown_platform": "warning"},
    )
    url = "https://e.com?utm_source=x&utm_medium=cpc&utm_campaign=y"
    r = make_row(0, url, {"platform": "tiktok"})
    findings = check_unknown_platform([r], config)
    assert findings[0].severity == "warning"
