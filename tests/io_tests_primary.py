import pandas as pd
import numpy as np
from data_lineage.runtime_hooks.io_hooks_py import start_io_context
from tests.io_tests_utils import dir_io_tests_data
from tests.io_tests_utils import save_data, load_data
from tests.io_tests_utils import pd_to_sqlite_db, read_sql_sqlite, pyodbc_execute_sql_sqlite


def create_random_dataframe(rows=1000, cols=10):
    """Create a DataFrame with random float values."""
    data = np.random.rand(rows, cols)
    col_names = [f"col_{i+1}" for i in range(cols)]
    return pd.DataFrame(data, columns=col_names)


def run_primary_tests():

    start_io_context("primary_tests")

    print("Creating random dataframe...\n")
    df = create_random_dataframe()

    csv_path = dir_io_tests_data / "sample_data.csv"
    pkl_path = dir_io_tests_data / "sample_data.pkl"

    print("Saving data as csv and pickle\n")
    save_data(df, csv_path=csv_path, pkl_path=pkl_path)

    print("Loading data from csv and pickle\n")
    df_csv, df_pkl = load_data(csv_path, pkl_path)

    # check pd.read_sql and pyodbc hooks
    # against a sqlite database
    table_name = "random_data"

    print("Writing DataFrame to SQLite database using pyodbc...\n")
    pd_to_sqlite_db(df, table_name)

    print("Reading data back from SQLite database using pyodbc...\n")
    sql_query = f"SELECT * FROM {table_name} LIMIT 100;"
    df_sql = read_sql_sqlite(sql_query)
    print(f'shape after reading back with pd.read_sql: {df_sql.shape}')

    print("Executing SQL command using pyodbc...\n")
    sql_command = f"DELETE FROM {table_name} WHERE rowid > 5;"
    pyodbc_execute_sql_sqlite(sql_command)
    # check deletion
    df_sql_after_delete = read_sql_sqlite(f"SELECT count(*) as count FROM {table_name};")
    print("Row count after deletion:", df_sql_after_delete['count'].iloc[0])

    return None



