from __future__ import annotations

from tests.conftest import make_row
from utm_auditor.models import Config
from utm_auditor.rules.r04_separator import check


def test_clean_no_findings():
    row = make_row(0, "https://e.com?utm_source=google&utm_medium=cpc&utm_campaign=spring_sale")
    assert check([row], Config.defaults()) == []


def test_hyphen_in_campaign_flagged():
    row = make_row(0, "https://e.com?utm_source=google&utm_medium=cpc&utm_campaign=spring-sale")
    findings = check([row], Config.defaults())
    assert len(findings) == 1
    assert "utm_campaign" in findings[0].message
    assert findings[0].suggested_fix == "Change to utm_campaign='spring_sale'"


def test_leading_whitespace_always_flagged():
    # %20 at start decodes to a leading space.
    row = make_row(0, "https://e.com?utm_source=%20google&utm_medium=cpc&utm_campaign=x")
    findings = check([row], Config.defaults())
    assert len(findings) == 1
    assert "leading" in findings[0].message


def test_embedded_space_flagged():
    row = make_row(0, "https://e.com?utm_source=google+ads&utm_medium=cpc&utm_campaign=x")
    findings = check([row], Config.defaults())
    assert len(findings) == 1
    assert "embedded spaces" in findings[0].message


def test_separator_any_disables_check():
    config = Config(separator="any")
    row = make_row(0, "https://e.com?utm_source=google&utm_medium=cpc&utm_campaign=spring-sale")
    assert check([row], config) == []


def test_separator_any_still_flags_whitespace():
    config = Config(separator="any")
    row = make_row(0, "https://e.com?utm_source=%20google&utm_medium=cpc&utm_campaign=x")
    findings = check([row], config)
    assert len(findings) == 1


def test_hyphen_config_flags_underscores():
    config = Config(separator="hyphen")
    row = make_row(0, "https://e.com?utm_source=google&utm_medium=cpc&utm_campaign=spring_sale")
    findings = check([row], config)
    assert len(findings) == 1
    assert findings[0].suggested_fix == "Change to utm_campaign='spring-sale'"


def test_mixed_separators_flagged():
    row = make_row(
        0, "https://e.com?utm_source=google&utm_medium=cpc&utm_campaign=spring_sale-2024"
    )
    findings = check([row], Config.defaults())
    assert len(findings) == 1
    assert "mixes" in findings[0].message


def test_malformed_row_skipped():
    row = make_row(0, "not-a-url")
    assert check([row], Config.defaults()) == []
