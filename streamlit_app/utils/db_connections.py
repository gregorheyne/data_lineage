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


def get_pyodbc_connection() -> pyodbc.Connection:
    connection_string = (
        f"DRIVER={{{DB_CONFIG['driver']}}};"
        f"SERVER=tcp:{DB_CONFIG['server']};"
        f"DATABASE={DB_CONFIG['database']};"
        f"UID={DB_CONFIG['username']};"
        f"PWD={DB_CONFIG['password']};"
        f"Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
    )
    return pyodbc.connect(connection_string)


def ensure_event_table_exists():
    conn = get_pyodbc_connection()
    cursor = conn.cursor()

    schema_exists = cursor.execute(
        "SELECT 1 FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = ?",
        SCHEMA_NAME,
    ).fetchone()
    if not schema_exists:
        cursor.execute(f"CREATE SCHEMA [{SCHEMA_NAME}]")
        conn.commit()

    table_exists = cursor.execute(
        "SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?",
        SCHEMA_NAME,
        TABLE_NAME,
    ).fetchone()
    if not table_exists:
        cursor.execute(f"""
            CREATE TABLE [{SCHEMA_NAME}].[{TABLE_NAME}] (
                session_id  NVARCHAR(MAX),
                timestamp   DATETIME2,
                user_id     NVARCHAR(MAX),
                page_name   NVARCHAR(MAX),
                event_type  NVARCHAR(MAX),
                metadata    NVARCHAR(MAX)
            )
        """)
        conn.commit()

    cursor.close()
    conn.close()

    return None
