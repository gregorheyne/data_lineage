import os
import sys
from pathlib import Path
import json
os.environ["HOOK_MAIN_NAME"] = "custom_name_for_repo"  # used by the hook to replace the <module> function name
# import file_hooks_pandas as file_hooks
import data_lineage.runtime_hooks.io_hooks_py as io_hooks_py
from tests.io_tests_primary import run_primary_tests
from tests.io_tests_secondary import run_secondary_tests


if __name__ == "__main__":
    run_primary_tests()
    run_secondary_tests()

    print('\nPrint a random record for checking:')
    record = io_hooks_py.IO_LOG_RECORDS[-2]
    print(json.dumps(record, indent=2))

    import pandas as pd
    pd.DataFrame(io_hooks_py.IO_LOG_RECORDS)
