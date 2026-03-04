import pyodbc

SCHEMA_NAME = "schema_name"
TABLE_NAME = "table_name"

DB_CONFIG = {
    "driver": "ODBC Driver 18 for SQL Server",
    "server": "your_server.database.windows.net",
    "database": "your_database",
    "username": "your_username",
    "password": "your_password",
}


def get_azure_db_connection() -> pyodbc.Connection:
    connection_string = (
        f"DRIVER={{{DB_CONFIG['driver']}}};"
        f"SERVER=tcp:{DB_CONFIG['server']};"
        f"DATABASE={DB_CONFIG['database']};"
        f"UID={DB_CONFIG['username']};"
        f"PWD={DB_CONFIG['password']};"
        f"Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
    )
    return pyodbc.connect(connection_string)
