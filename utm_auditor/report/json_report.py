from __future__ import annotations

import dataclasses
import json
from pathlib import Path

from utm_auditor.models import Finding


def render_json(findings: list[Finding], path: Path) -> None:
    """Write full structured findings to a JSON file."""
    data = [dataclasses.asdict(f) for f in findings]
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
