from __future__ import annotations

from tests.conftest import FIXTURES, make_row
from utm_auditor.models import Config
from utm_auditor.parsing.csv_loader import load_csv
from utm_auditor.rules.r01_missing_params import check


def test_all_present_no_findings():
    row = make_row(0, "https://e.com?utm_source=g&utm_medium=cpc&utm_campaign=x")
    assert check([row], Config.defaults()) == []


def test_missing_campaign():
    row = make_row(0, "https://e.com?utm_source=g&utm_medium=cpc")
    findings = check([row], Config.defaults())
    assert len(findings) == 1
    assert findings[0].rule_id == "missing_required_utm"
    assert "utm_campaign" in findings[0].message


def test_missing_multiple_params():
    row = make_row(0, "https://e.com?utm_campaign=x")
    findings = check([row], Config.defaults())
    assert len(findings) == 2
    params_flagged = {f.message.split("'")[1] for f in findings}
    assert params_flagged == {"utm_source", "utm_medium"}


def test_malformed_row_skipped():
    row = make_row(0, "not-a-url")
    assert check([row], Config.defaults()) == []


def test_custom_required_params():
    config = Config(required_params=["utm_source"])
    row = make_row(0, "https://e.com?utm_source=google")
    assert check([row], config) == []


def test_custom_required_empty_means_nothing_required():
    config = Config(required_params=[])
    row = make_row(0, "https://e.com/no-params")
    assert check([row], config) == []


def test_severity_override():
    config = Config(severity_overrides={"missing_required_utm": "info"})
    row = make_row(0, "https://e.com?utm_source=g&utm_medium=cpc")
    findings = check([row], config)
    assert all(f.severity == "info" for f in findings)


def test_fixture_file():
    rows, _ = load_csv(FIXTURES / "missing_params.csv")
    findings = check(rows, Config.defaults())
    # Row 0: missing utm_campaign; Row 1: missing utm_source and utm_medium.
    rule_ids = {f.rule_id for f in findings}
    assert rule_ids == {"missing_required_utm"}
    assert any("utm_campaign" in f.message for f in findings)
