from __future__ import annotations

import sys
from pathlib import Path

import click

from utm_auditor import __version__
from utm_auditor.engine import run_audit
from utm_auditor.models import Config
from utm_auditor.parsing.csv_loader import load_csv
from utm_auditor.report.cleaned_csv import render_cleaned_csv
from utm_auditor.report.json_report import render_json
from utm_auditor.report.terminal import render_terminal

_SEVERITY_RANK: dict[str, int] = {"error": 0, "warning": 1, "info": 2}


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("input_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--config",
    "config_file",
    type=click.Path(path_type=Path),
    default=None,
    metavar="FILE",
    help="Path to conventions.json.  Omit to run with built-in defaults.",
)
@click.option(
    "--url-column",
    default=None,
    metavar="COLUMN",
    help=(
        "Name of the URL column.  "
        "Defaults to 'url'; falls back to auto-detection if absent."
    ),
)
@click.option(
    "--out",
    "out_file",
    type=click.Path(path_type=Path),
    default=None,
    metavar="FILE",
    help="Cleaned CSV output path.  Default: campaigns.cleaned.csv",
)
@click.option(
    "--json",
    "json_file",
    type=click.Path(path_type=Path),
    default=None,
    metavar="FILE",
    help="Write full structured findings to a JSON file.",
)
@click.option(
    "--fail-on",
    default="error",
    type=click.Choice(["error", "warning", "info"], case_sensitive=False),
    show_default=True,
    help=(
        "Exit non-zero when any finding is at or above this severity.  "
        "Useful for gating CI pipelines."
    ),
)
@click.option("--no-color", is_flag=True, help="Disable color and Rich markup in terminal output.")
@click.version_option(version=__version__, prog_name="utm-auditor")
def cli(
    input_file: Path,
    config_file: Path | None,
    url_column: str | None,
    out_file: Path | None,
    json_file: Path | None,
    fail_on: str,
    no_color: bool,
) -> None:
    """Audit campaign tracking URLs for UTM hygiene issues.

    INPUT_FILE is a CSV file containing campaign URLs.  The tool emits a
    terminal report, writes a cleaned CSV, and optionally a JSON report.
    Exit code is non-zero when findings meet or exceed --fail-on severity.

    \b
    Examples:
      utm-auditor campaigns.csv
      utm-auditor campaigns.csv --config conventions.json --json report.json
      utm-auditor campaigns.csv --url-column landing_url --fail-on warning
    """
    # --- Config ---
    if config_file is not None:
        try:
            config = Config.load(config_file)
        except ValueError as exc:
            click.echo(f"Error: {exc}", err=True)
            sys.exit(2)
        config_source = str(config_file)
    else:
        config = Config.defaults()
        config_source = "built-in defaults"

    # --- Load CSV ---
    try:
        rows, resolved_col = load_csv(input_file, url_column)
    except ValueError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(2)

    # --- Audit ---
    findings = run_audit(rows, config)

    # --- Terminal report ---
    render_terminal(findings, len(rows), config_source, no_color=no_color)

    # --- JSON report ---
    if json_file is not None:
        render_json(findings, json_file)
        click.echo(f"JSON report written to {json_file}", err=True)

    # --- Cleaned CSV ---
    out_path = out_file if out_file is not None else Path("campaigns.cleaned.csv")
    if out_path.resolve() == input_file.resolve():
        click.echo(
            "Error: --out cannot point to the same file as the input.  "
            "Choose a different output path.",
            err=True,
        )
        sys.exit(2)
    render_cleaned_csv(rows, findings, config, out_path, resolved_col)
    click.echo(f"Cleaned CSV written to {out_path}", err=True)

    # --- Exit code ---
    threshold = _SEVERITY_RANK[fail_on.lower()]
    worst = min((_SEVERITY_RANK[f.severity] for f in findings), default=999)
    if worst <= threshold:
        sys.exit(1)
