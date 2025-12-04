import argparse
import json
import sys

import pandas as pd

from api.logic import load_data_models_from_settings, validate_csv
from api.schema import PandasDelimeter
from config.config import settings


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate a CSV file against the STRATA-FIT data schema."
    )
    parser.add_argument("--input", required=True, help="Path to the input CSV file")
    parser.add_argument(
        "--output",
        required=False,
        help="Path to write JSON errors (stdout if omitted)",
    )
    parser.add_argument(
        "--delimiter",
        choices=[d.value for d in PandasDelimeter],
        default=PandasDelimeter.COMMA.value,
        help="CSV delimiter (default: ',')",
    )
    args = parser.parse_args()

    df = pd.read_csv(args.input, delimiter=args.delimiter, keep_default_na=False)

    models = load_data_models_from_settings()
    model = models[settings.app.data.model_name]
    _, errors = validate_csv(df, model)

    output_json = json.dumps([e.model_dump() for e in errors], indent=2)
    if args.output:
        with open(args.output, "w") as f:
            f.write(output_json)
    else:
        print(output_json)

    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
