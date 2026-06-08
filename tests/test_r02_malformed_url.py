from __future__ import annotations

from tests.conftest import FIXTURES, make_row
from utm_auditor.models import Config
from utm_auditor.parsing.csv_loader import load_csv
from utm_auditor.rules.r02_malformed_url import check


def test_valid_url_no_findings():
    row = make_row(0, "https://example.com?utm_source=g&utm_medium=cpc&utm_campaign=x")
    assert check([row], Config.defaults()) == []


def test_empty_url_flagged():
    row = make_row(0, "")
    findings = check([row], Config.defaults())
    assert len(findings) == 1
    assert findings[0].rule_id == "malformed_url"
    assert "empty" in findings[0].message.lower()


def test_no_scheme_flagged():
    row = make_row(0, "not-a-url")
    findings = check([row], Config.defaults())
    assert len(findings) == 1
    assert "scheme" in findings[0].message.lower()


def test_missing_host_flagged():
    row = make_row(0, "http://")
    findings = check([row], Config.defaults())
    assert len(findings) == 1
    assert "host" in findings[0].message.lower()


def test_non_ascii_url_valid():
    # Non-ASCII in query params is allowed by urlparse; not a malformed-URL issue.
    row = make_row(0, "https://example.com?utm_source=café&utm_medium=cpc&utm_campaign=y")
    assert check([row], Config.defaults()) == []


def test_no_query_string_not_malformed():
    row = make_row(0, "https://example.com/landing")
    assert check([row], Config.defaults()) == []


def test_severity_override():
    config = Config(severity_overrides={"malformed_url": "warning"})
    row = make_row(0, "not-a-url")
    findings = check([row], config)
    assert findings[0].severity == "warning"


def test_fixture_file():
    rows, _ = load_csv(FIXTURES / "malformed_urls.csv")
    findings = check(rows, Config.defaults())
    flagged_urls = {f.url for f in findings}
    assert "not-a-url" in flagged_urls
    assert "http://" in flagged_urls
    # The valid https URL must NOT be flagged.
    assert not any("valid.com" in f.url for f in findings)
