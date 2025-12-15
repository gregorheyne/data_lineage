import os
import pyodbc
import pandas as pd
from pathlib import Path

dir_io_tests_data = Path(os.getcwd()) / "tests/io_tests_data"
dir_io_tests_data.mkdir(parents=True, exist_ok=True)
print(f"Base directory for data I/O: {dir_io_tests_data}")
DB_file = dir_io_tests_data / "test_database.sqlite"


def save_data(df, csv_path=None, pkl_path=None):

    df.to_csv(csv_path, index=False)
    df.to_pickle(pkl_path)

    print("\nData saved.")
    return None


def load_data(csv_path, pkl_path):
    """Helper function to read back the data."""
    df_csv = pd.read_csv(csv_path)
    df_pkl = pd.read_pickle(pkl_path)

    print("\nData loaded.")
    return df_csv, df_pkl

def get_pyodbc_sqlite_connection():
    connection_string = (
        f"DRIVER={{SQLite3}};"
        f"Database={os.path.abspath(DB_file)};"
    )
    pyodbc_conn = pyodbc.connect(connection_string)
    return pyodbc_conn



def pd_to_sqlite_db(df, table_name):
    # we dont hook this one as i dont plan on using pd.to_sql
    pyodbc_conn = get_pyodbc_sqlite_connection()
    df.to_sql(
        name=table_name,
        con=pyodbc_conn,
        if_exists="replace",
        index=False)
    pyodbc_conn.close()
    return None

def read_sql_sqlite(sql_query):
    pyodbc_conn = get_pyodbc_sqlite_connection()
    df = pd.read_sql(sql_query, pyodbc_conn)
    pyodbc_conn.close()
    return df

def pyodbc_execute_sql_sqlite(sql_command):
    pyodbc_conn = get_pyodbc_sqlite_connection()
    cursor = pyodbc_conn.cursor()
    cursor.execute(sql_command)
    pyodbc_conn.commit()
    cursor.close()
    pyodbc_conn.close()
    return None

def pyodbc_execute_many_sql_sqlite(sql_command, data):
    pyodbc_conn = get_pyodbc_sqlite_connection()
    cursor = pyodbc_conn.cursor()
    cursor.fast_executemany = True
    cursor.executemany(sql_command, data)
    pyodbc_conn.commit()
    cursor.close()
    pyodbc_conn.close()
    return None


