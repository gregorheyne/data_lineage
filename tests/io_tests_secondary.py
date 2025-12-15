import pandas as pd
import numpy as np
from data_lineage.runtime_hooks.io_hooks_py import start_io_context
from tests.io_tests_utils import dir_io_tests_data
from tests.io_tests_utils import load_data
from tests.io_tests_utils import read_sql_sqlite, pyodbc_execute_sql_sqlite
from tests.io_tests_utils import pyodbc_execute_many_sql_sqlite


def run_secondary_tests():

    """
    Run secondary tests for data I/O and database operations.
    mainly to see how the hooks behave when called from a different module
    than the main one.
    and to have a look at the log records collected by the hooks.
    """

    start_io_context("secondary_tests")

    csv_path = dir_io_tests_data / "sample_data.csv"
    pkl_path = dir_io_tests_data / "sample_data.pkl"

    print("Loading data from csv and pickle\n")
    df_csv, df_pkl = load_data(csv_path, pkl_path)

    # create table random_data_secondary in sqlite database via pyodbc
    # and insert first 10 rows from the dataframe into it
    table_name = "random_data_secondary"
    print("Writing DataFrame to SQLite database using pyodbc...\n")
    pyodbc_execute_sql_sqlite(f"DROP TABLE IF EXISTS {table_name};")
    pyodbc_execute_sql_sqlite(f"""
        CREATE TABLE {table_name} (
            id INTEGER PRIMARY KEY,
            col_1 REAL,
            col_2 REAL,
            col_3 REAL,
            col_4 REAL,
            col_5 REAL,
            col_6 REAL,
            col_7 REAL,
            col_8 REAL,
            col_9 REAL,
            col_10 REAL
        );
        """)

    # now insert data
    for index, row in df_csv.iloc[:10].iterrows():
        sql_command = f"""
            INSERT INTO {table_name} (col_1, col_2, col_3, col_4, col_5, col_6, col_7, col_8, col_9, col_10)
            VALUES ({row['col_1']}, {row['col_2']}, {row['col_3']}, {row['col_4']}, {row['col_5']},
                    {row['col_6']}, {row['col_7']}, {row['col_8']}, {row['col_9']}, {row['col_10']});
            """
        pyodbc_execute_sql_sqlite(sql_command)
    print("Data inserted into SQLite database.\n")
    # read back a few records
    sql_query = f"SELECT * FROM {table_name} LIMIT 10;"
    df_sql = read_sql_sqlite(sql_query)
    print(f'shape after reading back with pd.read_sql: {df_sql.shape}')

    # execute many for df_csv rows 10 to end
    print("Inserting multiple records using executemany...\n")
    data_to_insert = df_csv.iloc[10:].to_records(index=False).tolist()
    sql_command_many = f"""
        INSERT INTO {table_name} (col_1, col_2, col_3, col_4, col_5, col_6, col_7, col_8, col_9, col_10)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
    pyodbc_execute_many_sql_sqlite(sql_command_many, data_to_insert)
    print("Multiple records inserted into SQLite database.\n")
    # get count of records now
    sql_query_count = f"SELECT count(*) as record_count FROM {table_name};"
    df_count = read_sql_sqlite(sql_query_count)
    print(f"Total records in {table_name}: {df_count['record_count'].iloc[0]}")


    return None



