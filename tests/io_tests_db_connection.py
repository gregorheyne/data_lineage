import os
import pyodbc
from pathlib import Path

dir_tmp_data = Path(os.getcwd()) / "tmp_data_io"
print(f"Base directory for sql database: {dir_tmp_data}")
DB_file = dir_tmp_data / "test_database.sqlite"

def get_pyodbc_sqlite_connection():
    connection_string = (
        f"DRIVER={{SQLite3}};"
        f"Database={os.path.abspath(DB_file)};"
    )
    pyodbc_conn = pyodbc.connect(connection_string)
    return pyodbc_conn