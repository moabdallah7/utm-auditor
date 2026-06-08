from __future__ import annotations

import json

from click.testing import CliRunner

from tests.conftest import FIXTURES
from utm_auditor.cli.main import cli


def invoke(*args: str) -> object:
    runner = CliRunner()
    return runner.invoke(cli, list(args), catch_exceptions=False)


def test_help():
    result = invoke("--help")
    assert result.exit_code == 0
    assert "utm-auditor" in result.output.lower() or "audit" in result.output.lower()


def test_version():
    result = invoke("--version")
    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_clean_file_exits_zero(tmp_path):
    result = invoke(str(FIXTURES / "clean.csv"), "--out", str(tmp_path / "out.csv"))
    assert result.exit_code == 0


def test_missing_params_exits_nonzero(tmp_path):
    result = invoke(
        str(FIXTURES / "missing_params.csv"),
        "--out", str(tmp_path / "out.csv"),
    )
    assert result.exit_code == 1


def test_fail_on_warning_exits_nonzero(tmp_path):
    result = invoke(
        str(FIXTURES / "casing_violations.csv"),
        "--out", str(tmp_path / "out.csv"),
        "--fail-on", "warning",
    )
    assert result.exit_code == 1


def test_fail_on_error_passes_warnings(tmp_path):
    result = invoke(
        str(FIXTURES / "casing_violations.csv"),
        "--out", str(tmp_path / "out.csv"),
        "--fail-on", "error",
    )
    assert result.exit_code == 0


def test_json_output_written(tmp_path):
    json_path = tmp_path / "report.json"
    invoke(
        str(FIXTURES / "missing_params.csv"),
        "--out", str(tmp_path / "out.csv"),
        "--json", str(json_path),
    )
    assert json_path.exists()
    data = json.loads(json_path.read_text())
    assert isinstance(data, list)
    assert len(data) > 0
    assert "rule_id" in data[0]


def test_cleaned_csv_written(tmp_path):
    out_path = tmp_path / "clean.csv"
    invoke(
        str(FIXTURES / "casing_violations.csv"),
        "--out", str(out_path),
    )
    assert out_path.exists()
    content = out_path.read_text()
    assert "audit_status" in content
    assert "audit_findings" in content
    assert "audit_changes" in content


def test_out_cannot_equal_input(tmp_path):
    result = invoke(
        str(FIXTURES / "clean.csv"),
        "--out", str(FIXTURES / "clean.csv"),
    )
    assert result.exit_code == 2


def test_invalid_config_exits_2(tmp_path):
    bad_config = tmp_path / "bad.json"
    bad_config.write_text('{"separator": "comma"}')
    result = invoke(
        str(FIXTURES / "clean.csv"),
        "--config", str(bad_config),
        "--out", str(tmp_path / "out.csv"),
    )
    assert result.exit_code == 2


def test_no_color_flag(tmp_path):
    result = invoke(
        str(FIXTURES / "clean.csv"),
        "--no-color",
        "--out", str(tmp_path / "out.csv"),
    )
    assert result.exit_code == 0


def test_url_column_flag(tmp_path):
    result = invoke(
        str(FIXTURES / "clean.csv"),
        "--url-column", "url",
        "--out", str(tmp_path / "out.csv"),
    )
    assert result.exit_code == 0


def test_url_column_missing_exits_2(tmp_path):
    result = invoke(
        str(FIXTURES / "clean.csv"),
        "--url-column", "nonexistent",
        "--out", str(tmp_path / "out.csv"),
    )
    assert result.exit_code == 2
