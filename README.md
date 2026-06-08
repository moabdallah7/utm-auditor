# utm-auditor

**An open-source campaign URL quality checker for marketing teams that need reliable attribution data — deterministic, dependency-light, and runnable in CI with no API keys.**

utm-auditor reads a CSV of campaign URLs, runs a configurable rule engine against every row, and produces:

- a colour terminal report grouped by severity
- a cleaned CSV with normalised values and audit annotation columns
- an optional structured JSON report

Every finding traces to a deterministic rule.  No network I/O, no AI guessing,
no API keys required.

---

## Install

```bash
pip install utm-auditor
```

Requires Python 3.11+.  Dependencies: [Click](https://click.palletsprojects.com/) and [Rich](https://github.com/Textualize/rich).

---

## Quickstart

```bash
# Audit with built-in defaults
utm-auditor campaigns.csv

# Audit with your conventions file
utm-auditor campaigns.csv --config conventions.json

# Custom URL column, JSON report, fail CI on warnings
utm-auditor campaigns.csv \
  --url-column landing_url \
  --json report.json \
  --fail-on warning
```

The cleaned CSV is written to `campaigns.cleaned.csv` by default.
Use `--out path/to/output.csv` to change the location.

---

## Terminal output

```
utm-auditor v0.1.0  •  Config: conventions.json  •  8 row(s) audited

────────────── ✗  ERRORS  (3 finding(s)) ──────────────

  malformed_url  (1 finding(s))
    row    5  not-a-url
           Malformed URL: missing URL scheme (expected https://)
           Fix: Ensure the URL starts with https:// and has a valid hostname

  missing_required_utm  (2 finding(s))
    row    6  https://acme.com/home?utm_source=google&utm_medium=cpc
           Missing required UTM parameter: 'utm_campaign'
           Fix: Add utm_campaign=<value> to the URL query string

────────────── ⚠  WARNINGS  (5 finding(s)) ──────────────

  casing_violation  (2 finding(s))
    row    1  https://acme.com/sale?utm_source=Google&utm_medium=CPC&utm_…
           utm_source='Google' must be lowercase
           Fix: Change to utm_source='google'
  ...

Summary: 8 row(s)  •  8 finding(s)  •  3 error(s), 4 warning(s), 1 info(s)
```

```
utm-auditor v0.1.0  •  Config: built-in defaults  •  3 row(s) audited

✓ No issues found.

Summary: 3 row(s)  •  0 finding(s)  •  none
```

---

## Cleaned CSV

Each output row contains the original columns (URL normalised in place) plus:

| Column | Values | Meaning |
|---|---|---|
| `audit_status` | `clean` / `error` / `warning` / `info` | Worst finding severity for this row |
| `audit_findings` | semicolon-separated rule IDs | Which rules fired |
| `audit_changes` | semicolon-separated descriptions | What was normalised |

---

## Rule catalog

| Rule ID | What it flags | Why it matters | Default severity |
|---|---|---|---|
| `missing_required_utm` | `utm_source`, `utm_medium`, or `utm_campaign` absent (configurable) | Missing params = broken attribution in every analytics tool | **error** |
| `malformed_url` | Unparseable URL, missing scheme/host, undecodable query string | The URL will never be tracked; entire row is unreliable | **error** |
| `casing_violation` | UTM param value does not match per-field casing rule (`lower`/`upper`) | Mixed case produces duplicate dimension values in GA4/Adobe | **warning** |
| `separator_violation` | Leading/trailing/embedded spaces, or `_` vs `-` inconsistency | Spaces cause broken URLs; mixed separators split campaigns into phantom segments | **warning** |
| `naming_convention_violation` | Value not in `allowed_values` allow-list, or `utm_campaign` fails `campaign_pattern` regex | Typos and ad-hoc names make segment filtering unreliable | **warning** |
| `duplicate_campaign` | Same `utm_campaign` across rows with different URLs | Ambiguous attribution — the analytics tool cannot tell which creative drove a conversion | **warning** |
| `duplicate_url` | Exact URL (all params) repeated | Usually a data-entry error or copy-paste | **info** |
| `source_platform_mismatch` | `utm_source` not in the allow-list for the row's `platform` column | Misrouted attribution — conversions credited to the wrong channel | **warning** |
| `unknown_platform` | `platform` column value has no entry in `platform_source_map` | Config coverage gap — new platform added without updating the map | **info** |

All severities are overridable per-rule via `severity_overrides` in `conventions.json`.

---

## conventions.json reference

All keys are optional.  Omitting the file entirely runs with documented built-in defaults (shown below).

```jsonc
{
  // Full replacement — NOT merged with defaults.
  // ["utm_source"] means ONLY source is required; [] means nothing is required.
  "required_params": ["utm_source", "utm_medium", "utm_campaign"],

  // Per-field casing rule.  Absent field = "any" (no check).
  "casing": {
    "utm_source":   "lower",   // "lower" | "upper" | "any"
    "utm_medium":   "lower"
  },

  // Preferred separator within UTM param values.
  // "any" disables the _ vs - consistency check; whitespace is always flagged.
  "separator": "underscore",  // "underscore" | "hyphen" | "any"

  // Allow-list per param.  Membership test is case-insensitive (both sides
  // normalised to lowercase).  Separate concern from casing rule.
  "allowed_values": {
    "utm_medium": ["cpc", "email", "organic", "social", "referral", "display"]
  },

  // Full-match regex applied to utm_campaign.  null = skip.
  "campaign_pattern": "^[a-z0-9_]+$",

  // Maps platform column value → acceptable utm_source values.
  // Key lookup and value membership are both case-insensitive (trim + lowercase).
  "platform_source_map": {
    "google":   ["google", "google_ads"],
    "facebook": ["facebook", "meta"],
    "email":    ["mailchimp", "klaviyo"]
  },

  // Override the default severity for any rule ID.
  "severity_overrides": {
    "duplicate_url":   "warning",
    "unknown_platform": "warning"
  }
}
```

### Built-in defaults

| Key | Default |
|---|---|
| `required_params` | `["utm_source", "utm_medium", "utm_campaign"]` |
| `casing` | `{"utm_source": "lower", "utm_medium": "lower"}` |
| `separator` | `"underscore"` |
| `allowed_values` | `{}` (no allow-list checks) |
| `campaign_pattern` | `null` (no pattern check) |
| `platform_source_map` | `{}` (rule 7 is a no-op) |
| `severity_overrides` | `{}` |

---

## CLI reference

```
utm-auditor [OPTIONS] INPUT_FILE

Arguments:
  INPUT_FILE  CSV file containing campaign URLs.

Options:
  --config FILE        Path to conventions.json.  Omit for built-in defaults.
  --url-column COLUMN  Name of the URL column.  Default: 'url'; auto-detected if absent.
  --out FILE           Cleaned CSV output path.  Default: campaigns.cleaned.csv
  --json FILE          Write full structured findings to a JSON file.
  --fail-on LEVEL      Exit non-zero when any finding is at or above this level.
                       Choices: error | warning | info.  Default: error.
  --no-color           Disable colour output (auto-disabled when piped).
  --version            Show version and exit.
  -h, --help           Show this message and exit.
```

### Exit codes

| Code | Meaning |
|---|---|
| `0` | No findings at or above `--fail-on` severity |
| `1` | One or more findings at or above `--fail-on` severity |
| `2` | Usage error (bad config, missing column, etc.) |

### CSV column detection

If `--url-column` is not supplied:

1. A column literally named `url` is used.
2. Otherwise every column is scanned; the one where ≥ 80 % of non-empty values
   parse as absolute URLs (`https://…` / `http://…`) is used.
3. If none or multiple candidates are found, the tool exits with an error and
   instructs you to use `--url-column`.

Unknown columns are passed through to the cleaned CSV unchanged.

---

## CI integration

```yaml
# .github/workflows/utm-audit.yml
- name: Audit campaign URLs
  run: utm-auditor campaigns.csv --config conventions.json --fail-on warning
```

---

## Architecture

```
utm_auditor/
├── models.py           Finding, ParsedURL, RowData, Config
├── engine.py           run_audit() — iterates registry, sorts findings
├── parsing/
│   ├── csv_loader.py   load_csv() — header detection, column resolution
│   └── url_parser.py   parse_url() + malformed_reason()
├── rules/
│   ├── registry.py     @register decorator, all_rules(), effective_severity()
│   ├── r01_missing_params.py
│   ├── r02_malformed_url.py
│   ├── r03_casing.py
│   ├── r04_separator.py
│   ├── r05_naming_convention.py
│   ├── r06_duplicates.py
│   └── r07_platform_source.py
├── report/
│   ├── terminal.py     Rich terminal renderer
│   ├── json_report.py  JSON file renderer
│   └── cleaned_csv.py  Cleaned CSV renderer + URL normaliser
└── cli/
    └── main.py         Click CLI — arg parsing and wiring only, no business logic
```

The engine and rule modules have **no I/O dependencies** and can be imported
directly without the CLI for programmatic use.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) — adding a rule is one file + one test.

## License

MIT — see [LICENSE](LICENSE).
