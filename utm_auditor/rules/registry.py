from __future__ import annotations

from collections.abc import Callable

from utm_auditor.models import Config, Finding, RowData, Severity

RuleFunc = Callable[[list[RowData], Config], list[Finding]]

# Maps rule_id → (function, default_severity).
_REGISTRY: dict[str, tuple[RuleFunc, Severity]] = {}


def register(rule_id: str, default_severity: Severity) -> Callable[[RuleFunc], RuleFunc]:
    """Decorator that registers a rule function under rule_id."""

    def decorator(fn: RuleFunc) -> RuleFunc:
        if rule_id in _REGISTRY:
            raise RuntimeError(f"Rule {rule_id!r} is already registered")
        _REGISTRY[rule_id] = (fn, default_severity)
        return fn

    return decorator


def all_rules() -> dict[str, tuple[RuleFunc, Severity]]:
    """Return a snapshot of the registry (deterministic insertion order)."""
    return dict(_REGISTRY)


def effective_severity(rule_id: str, default: Severity, config: Config) -> Severity:
    """Return the severity for rule_id, honoring any severity_overrides in config."""
    override = config.severity_overrides.get(rule_id)
    return override if override is not None else default
