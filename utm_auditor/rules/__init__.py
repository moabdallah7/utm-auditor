# Importing each module registers its rule(s) in the registry.
# Add a new rule by creating rNN_<name>.py and appending it here.
from utm_auditor.rules import (  # noqa: F401
    r01_missing_params,
    r02_malformed_url,
    r03_casing,
    r04_separator,
    r05_naming_convention,
    r06_duplicates,
    r07_platform_source,
)
