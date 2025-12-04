"""
tests/test_validation.py

The test instantiates one fake node, feeds it the example CSV and checks that
the algorithm returns the expected structure:
    {
      "total_rows": …,
      "total_errors": …,
      "error_rate": …,
      "errors": [...],
      "validation_passed": bool
    }
"""

from pathlib import Path
import json
import warnings

from vantage6.algorithm.tools.mock_client import MockAlgorithmClient

warnings.filterwarnings("ignore", category=UserWarning)

# --------------------------------------------------------------------------- #
# 1 │  Data sets per ‘organization’
# --------------------------------------------------------------------------- #
# Feel free to add more orgs or point to a different CSV for negative/positive
# test-cases.  The key requirement is: db_type must be 'csv'.
data_dir = Path(__file__).parent.parent / "data"
dataset_ok   = {"database": data_dir / "example_digione_mbc_data_model_03.csv",
                "db_type": "csv"}

# one org → one list with that single dataset
datasets_per_org = [[dataset_ok]]
org_ids = [0]

# --------------------------------------------------------------------------- #
# 2 │  Instantiate mock client
# --------------------------------------------------------------------------- #
client = MockAlgorithmClient(
    datasets=datasets_per_org,
    organization_ids=org_ids,
    module="digione_v6_data_validator_py",  
)

# --------------------------------------------------------------------------- #
# 3 │  Submit the task
# --------------------------------------------------------------------------- #
task = client.task.create(
    input_={
        "method": "validate_data",
        "kwargs": {}
    },
    organizations=org_ids              
)

# --------------------------------------------------------------------------- #
# 4 │  Collect result(s)
# --------------------------------------------------------------------------- #
# MockAlgorithmClient returns a *list* with one JSON string per organization.
results_json_per_org = client.result.get(task["id"])
result_dict = results_json_per_org

print("\nValidator result:")
for k, v in result_dict.items():
    if k != "errors":    # don't spam the console
        print(f"  {k:17}: {v}")

# --------------------------------------------------------------------------- #
# 5 │  Simple assertions
# --------------------------------------------------------------------------- #
assert "validation_passed" in result_dict
assert "total_rows"       in result_dict
assert "total_errors"     in result_dict

# Sanity: total_errors == 0  → validation_passed must be True (and vice-versa)
assert (result_dict["total_errors"] == 0) == result_dict["validation_passed"]

print("\n✅  Vantage6 mock-test finished successfully.")
