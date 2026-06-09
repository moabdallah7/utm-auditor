from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

Severity = Literal["error", "warning", "info"]

UTM_PARAMS: tuple[str, ...] = (
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
)

_VALID_SEPARATORS: frozenset[str] = frozenset({"underscore", "hyphen", "any"})
_VALID_CASINGS: frozenset[str] = frozenset({"lower", "upper", "any"})
_VALID_SEVERITIES: frozenset[str] = frozenset({"error", "warning", "info"})


@dataclass(frozen=True)
class Finding:
    row_index: int
    url: str
    rule_id: str
    severity: Severity
    message: str
    suggested_fix: str | None = None


@dataclass(frozen=True)
class ParsedURL:
    scheme: str
    netloc: str
    # First value per key; preserves parse order.
    query_params: dict[str, str]


@dataclass
class RowData:
    index: int
    raw: dict[str, str]
    url: str
    # None when the URL is malformed; malformed_url rule fires on these rows.
    parsed: ParsedURL | None


@dataclass
class Config:
    # Full replacement of defaults when supplied; ["utm_source"] means ONLY source is required.
    required_params: list[str] = field(
        default_factory=lambda: ["utm_source", "utm_medium", "utm_campaign"]
    )
    # Absent field → "any" (no casing check).
    casing: dict[str, str] = field(
        default_factory=lambda: {"utm_source": "lower", "utm_medium": "lower"}
    )
    # "underscore" | "hyphen" | "any".  "any" disables _ vs - check; whitespace always flagged.
    separator: str = "underscore"
    # Membership test is case-insensitive (normalize both sides to lowercase).
    allowed_values: dict[str, list[str]] = field(default_factory=dict)
    campaign_pattern: str | None = None
    # Key lookup and value membership are both case-insensitive (trim + lowercase).
    platform_source_map: dict[str, list[str]] = field(default_factory=dict)
    severity_overrides: dict[str, Severity] = field(default_factory=dict)

    @classmethod
    def defaults(cls) -> Config:
        return cls()

    @classmethod
    def load(cls, path: Path) -> Config:
        try:
            raw = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise ValueError(f"Cannot read config file {path}: {exc}") from exc
        try:
            data: object = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path} is not valid JSON: {exc}") from exc
        if not isinstance(data, dict):
            raise ValueError(f"{path} must be a JSON object, got {type(data).__name__}")
        return cls._from_dict(data, path)

    @classmethod
    def _from_dict(cls, data: dict[str, object], path: Path) -> Config:
        errors: list[str] = []

        required_params = data.get("required_params", ["utm_source", "utm_medium", "utm_campaign"])
        if not isinstance(required_params, list) or not all(
            isinstance(p, str) for p in required_params
        ):
            errors.append("required_params must be a list of strings")
            required_params = ["utm_source", "utm_medium", "utm_campaign"]

        separator = data.get("separator", "underscore")
        if not isinstance(separator, str) or separator not in _VALID_SEPARATORS:
            errors.append(
                f"separator must be one of {sorted(_VALID_SEPARATORS)}, got {separator!r}"
            )
            separator = "underscore"

        casing_raw = data.get("casing", {"utm_source": "lower", "utm_medium": "lower"})
        casing: dict[str, str] = {}
        if not isinstance(casing_raw, dict):
            errors.append("casing must be a JSON object")
        else:
            for k, v in casing_raw.items():
                if not isinstance(v, str) or v not in _VALID_CASINGS:
                    errors.append(
                        f"casing[{k!r}] must be one of {sorted(_VALID_CASINGS)}, got {v!r}"
                    )
                else:
                    casing[k] = v

        allowed_raw = data.get("allowed_values", {})
        allowed_values: dict[str, list[str]] = {}
        if not isinstance(allowed_raw, dict):
            errors.append("allowed_values must be a JSON object")
        else:
            for k, v in allowed_raw.items():
                if not isinstance(v, list) or not all(isinstance(s, str) for s in v):
                    errors.append(f"allowed_values[{k!r}] must be a list of strings")
                else:
                    allowed_values[k] = v

        campaign_pattern: str | None = None
        cp_raw = data.get("campaign_pattern", None)
        if cp_raw is not None:
            if not isinstance(cp_raw, str):
                errors.append("campaign_pattern must be a string")
            else:
                try:
                    re.compile(cp_raw)
                    campaign_pattern = cp_raw
                except re.error as exc:
                    errors.append(f"campaign_pattern is not a valid regex: {exc}")

        psm_raw = data.get("platform_source_map", {})
        platform_source_map: dict[str, list[str]] = {}
        if not isinstance(psm_raw, dict):
            errors.append("platform_source_map must be a JSON object")
        else:
            for k, v in psm_raw.items():
                if not isinstance(v, list) or not all(isinstance(s, str) for s in v):
                    errors.append(f"platform_source_map[{k!r}] must be a list of strings")
                else:
                    platform_source_map[k] = v

        so_raw = data.get("severity_overrides", {})
        severity_overrides: dict[str, Severity] = {}
        if not isinstance(so_raw, dict):
            errors.append("severity_overrides must be a JSON object")
        else:
            for k, v in so_raw.items():
                if not isinstance(v, str) or v not in _VALID_SEVERITIES:
                    errors.append(
                        f"severity_overrides[{k!r}] must be one of "
                        f"{sorted(_VALID_SEVERITIES)}, got {v!r}"
                    )
                else:
                    severity_overrides[k] = v  # type: ignore[assignment]

        if errors:
            bullet = "\n  • "
            raise ValueError(f"Invalid config {path}:{bullet}{bullet.join(errors)}")

        return cls(
            required_params=list(required_params),
            casing=casing if casing_raw else {"utm_source": "lower", "utm_medium": "lower"},
            separator=str(separator),
            allowed_values=allowed_values,
            campaign_pattern=campaign_pattern,
            platform_source_map=platform_source_map,
            severity_overrides=severity_overrides,
        )
