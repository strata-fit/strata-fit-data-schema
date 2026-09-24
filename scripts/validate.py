"""Compatibility shim: the real implementation now lives in
strata_fit_v6_data_validator_py.cli. Kept at this import path so the
`strata-fit-validate` console script (pyproject.toml) doesn't need to change.
"""

from strata_fit_v6_data_validator_py.cli import main

__all__ = ["main"]

if __name__ == "__main__":
    main()
