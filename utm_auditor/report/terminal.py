from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING

from utm_auditor import __version__
from utm_auditor.models import Finding

if TYPE_CHECKING:
    from rich.console import Console

_SEVERITY_ORDER = ("error", "warning", "info")
_SEVERITY_STYLE: dict[str, str] = {
    "error": "bold red",
    "warning": "yellow",
    "info": "cyan",
}
_SEVERITY_ICON: dict[str, str] = {
    "error": "✗",
    "warning": "⚠",
    "info": "ℹ",
}
_URL_TRUNCATE = 70


def render_terminal(
    findings: list[Finding],
    row_count: int,
    config_source: str,
    no_color: bool = False,
    console: Console | None = None,
) -> None:
    """Write a human-readable audit report to stdout (or a supplied Console)."""
    from rich.console import Console as RichConsole
    from rich.rule import Rule

    if console is None:
        console = RichConsole(no_color=no_color, highlight=False)

    console.print()
    console.print(
        f"[bold]utm-auditor[/bold] v{__version__}  •  "
        f"Config: {config_source}  •  "
        f"{row_count} row(s) audited"
    )
    console.print()

    if not findings:
        console.print("[bold green]✓ No issues found.[/bold green]")
        _summary(console, row_count, findings)
        return

    # Group by severity → rule_id.
    by_sev: dict[str, dict[str, list[Finding]]] = {
        s: defaultdict(list) for s in _SEVERITY_ORDER
    }
    for f in findings:
        by_sev[f.severity][f.rule_id].append(f)

    for severity in _SEVERITY_ORDER:
        rules = by_sev[severity]
        if not rules:
            continue
        sev_count = sum(len(v) for v in rules.values())
        style = _SEVERITY_STYLE[severity]
        icon = _SEVERITY_ICON[severity]
        console.print(
            Rule(
                f"[{style}]{icon}  {severity.upper()}  ({sev_count} finding(s))[/{style}]",
                style="dim",
            )
        )

        for rule_id in sorted(rules):
            rule_findings = rules[rule_id]
            console.print(
                f"  [{style}]{rule_id}[/{style}]  "
                f"[dim]({len(rule_findings)} finding(s))[/dim]"
            )

            # Show per-row detail for errors and warnings; just count for info.
            if severity in ("error", "warning"):
                for f in rule_findings:
                    from rich.markup import escape

                    short_url = (
                        f.url[:_URL_TRUNCATE] + "…"
                        if len(f.url) > _URL_TRUNCATE
                        else f.url
                    )
                    console.print(
                        f"    [dim]row {f.row_index + 1:>4}[/dim]  {escape(short_url)}"
                    )
                    console.print(f"           [dim]{escape(f.message)}[/dim]")
                    if f.suggested_fix:
                        console.print(
                            f"           [dim italic]Fix: {escape(f.suggested_fix)}[/dim italic]"
                        )
            console.print()

    _summary(console, row_count, findings)


def _summary(console: Console, row_count: int, findings: list[Finding]) -> None:
    errors = sum(1 for f in findings if f.severity == "error")
    warnings = sum(1 for f in findings if f.severity == "warning")
    infos = sum(1 for f in findings if f.severity == "info")

    parts: list[str] = []
    if errors:
        parts.append(f"[bold red]{errors} error(s)[/bold red]")
    if warnings:
        parts.append(f"[yellow]{warnings} warning(s)[/yellow]")
    if infos:
        parts.append(f"[cyan]{infos} info(s)[/cyan]")

    detail = ", ".join(parts) if parts else "[bold green]none[/bold green]"
    console.print()
    console.print(
        f"[bold]Summary:[/bold] {row_count} row(s)  •  "
        f"{len(findings)} finding(s)  •  {detail}"
    )
    console.print()
