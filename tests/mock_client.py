from __future__ import annotations

import json

from pathlib import Path

import pandas as pd

from strata_fit_v6_data_validator_py.algorithm import validate_dataframe


def main() -> None:
    data_path = Path(__file__).parent / "fixtures" / "valid.csv"
    frame = pd.read_csv(data_path)
    result = validate_dataframe(frame)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
