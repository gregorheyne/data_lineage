import os

SCHEMA_NAME = "schema_name"
TABLE_NAME = "table_name"

DB_CONFIG = {
    "driver": "ODBC Driver 18 for SQL Server",
    "server": "your_server.database.windows.net",
    "database": "your_database",
    "username": "your_username",
    "password": "your_password",
}

PROD_DB_CONFIG = {
    "server": "your_server.database.windows.net",
    "database": "your_database",
}


def get_azure_db_connection():
    env = os.environ.get("APP_ENVIRONMENT", "dev")

    if env == "prod":
        import pymssql
        return pymssql.connect(
            server=PROD_DB_CONFIG["server"],
            user=os.environ["DB_USER"],
            password=os.environ["DB_PASSWORD"],
            database=PROD_DB_CONFIG["database"],
        )
    else:
        import pyodbc
        connection_string = (
            f"DRIVER={{{DB_CONFIG['driver']}}};"
            f"SERVER=tcp:{DB_CONFIG['server']};"
            f"DATABASE={DB_CONFIG['database']};"
            f"UID={DB_CONFIG['username']};"
            f"PWD={DB_CONFIG['password']};"
            f"Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
        )
        return pyodbc.connect(connection_string)
