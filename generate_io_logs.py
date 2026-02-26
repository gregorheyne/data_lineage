import os
os.environ["IO_HOOKS_MAIN_NAME"] = "test_module"  # used by the hook to replace the <module> function name
import data_lineage.runtime_hooks.io_hooks_py as io_hooks_py
from pathlib import Path
from tests.io_tests_primary import run_primary_tests
from tests.io_tests_secondary import run_secondary_tests

# three lines as the could be in normal code where io hooks should be used
run_primary_tests()
run_secondary_tests()
io_hooks_py.write_io_logs_to_csv(Path('data/io_logs.csv'))
