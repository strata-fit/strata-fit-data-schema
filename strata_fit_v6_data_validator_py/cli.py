from __future__ import annotations

import argparse
import json
import sys

from .algorithm import validate_file_errors
from .logs import setup_logging
from .schema import PandasDelimeter
from .settings import settings


def main() -> None:
    setup_logging(level=settings.logging.level)
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
        choices=[item.value for item in PandasDelimeter],
        default=PandasDelimeter.COMMA.value,
        help="CSV delimiter (default: ',')",
    )
    args = parser.parse_args()

    errors = validate_file_errors(args.input, delimiter=args.delimiter)
    output_json = json.dumps([error.model_dump() for error in errors], indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(output_json)
    else:
        print(output_json)

    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
