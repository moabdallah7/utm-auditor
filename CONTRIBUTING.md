# Contributing to utm-auditor

## Adding a new rule — one file, one test

The rule engine is a registry: rules self-register by being imported.
Adding a rule means exactly one new source file and one new test file.
No changes to the core loop.

### Step 1 — Create `utm_auditor/rules/rNN_<name>.py`

```python
# utm_auditor/rules/r08_example.py
from utm_auditor.models import Config, Finding, RowData
from utm_auditor.rules.registry import effective_severity, register

_RULE_ID = "example_rule"


@register(_RULE_ID, "warning")          # second arg = default severity
def check(rows: list[RowData], config: Config) -> list[Finding]:
    severity = effective_severity(_RULE_ID, "warning", config)
    findings: list[Finding] = []
    for row in rows:
        if row.parsed is None:
            continue                     # malformed_url handles unparseable rows
        # ... your logic here ...
    return findings
```

Rules are **pure functions**: given the same `rows` and `config`, they always
return the same findings. No I/O, no state, no network.

- Per-row rules iterate over `rows` internally.
- Cross-row rules (e.g. duplicates) can inspect the full list.
- Use `row.parsed.query_params` for UTM values; `row.raw` for original CSV columns.
- Skip rows where `row.parsed is None` unless your rule specifically targets
  malformed URLs.

### Step 2 — Register it in `utm_auditor/rules/__init__.py`

```python
from utm_auditor.rules import (  # noqa: F401
    ...
    r08_example,            # ← append here
)
```

### Step 3 — Write `tests/test_r08_example.py`

Cover at minimum:

| Case | What to assert |
|---|---|
| Clean row | `findings == []` |
| Each failure mode | Correct `rule_id`, `severity`, message text |
| Malformed row | Skipped (no findings) |
| `severity_overrides` in config | Overridden severity respected |

Use the helpers in `tests/conftest.py`:

```python
from tests.conftest import make_row
from utm_auditor.models import Config
from utm_auditor.rules.r08_example import check

def test_flags_x():
    row = make_row(0, "https://example.com?utm_source=g&utm_medium=cpc&utm_campaign=x")
    findings = check([row], Config.defaults())
    assert len(findings) == 1
    assert findings[0].rule_id == "example_rule"
```

### Step 4 — Add to the README rule catalog

Add a row to the **Rule catalog** table in README.md.

### Step 5 — Run the full suite

```bash
pip install -e ".[dev]"
pytest
ruff check utm_auditor tests
mypy utm_auditor
```

---

## Development setup

```bash
git clone https://github.com/your-org/utm-auditor.git
cd utm-auditor
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## Code style

- `ruff` for linting and formatting (`ruff check`, `ruff format`)
- `mypy --strict` for type checking
- No comments explaining *what* the code does — only *why* if non-obvious
- All public functions need return-type annotations

## Commit messages

One-line imperative summary under 72 characters.  Reference an issue number
when applicable (`fix #42`).

## Issue / PR etiquette

- Use the provided issue templates.
- Keep PRs focused: one rule or one fix per PR.
- CI must be green before requesting review.
