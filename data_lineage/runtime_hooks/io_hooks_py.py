import re
import inspect
import functools
import os
import time
import pyodbc
import getpass
import uuid
import pandas as pd
from datetime import datetime
from contextvars import ContextVar

__all__ = ["install_io_hooks"]

IO_LOG_RECORDS = []

user_name = getpass.getuser()
cwd = os.getcwd()
module_name = os.getenv("IO_HOOKS_MAIN_NAME", 'default_module_name')


# Context ID variable (per-thread / per-task)
current_io_context = ContextVar("current_io_context", default=None)

def start_io_context(name=None):
    """Start a new logical io_context."""
    if not name:
        io_ctx_id = f"io_ctx_id-{uuid.uuid4()}"
    else:
        io_ctx_id = f"{name}-io_ctx_id-{uuid.uuid4()}"
    current_io_context.set(io_ctx_id)
    return io_ctx_id

def get_io_context():
    """Get the current io_context ID, if any."""
    return current_io_context.get()

def clear_io_context():
    """Optional: reset io_context to None."""
    current_io_context.set(None)

def _format_frame(frame_info):
    """
    Format a frame into a structured object:
    {
        "file": "main.py",
        "line": 14,
        "function": <module> or function name
    }
    """
    return {
        "file": frame_info.filename if frame_info.filename else None,
        # "file": os.path.basename(frame_info.filename) if frame_info.filename else None,
        "line": frame_info.lineno,
        # "function": module_name if frame_info.function == "<module>" and module_name else frame_info.function
        "function": frame_info.function
    }


def _get_call_chain(max_depth=10):
    """
    Returns a (cut-off) call chain tracing where the pandas I/O call originated.

    Example:
    main.py:12 → helper.py:33 in load_data
    """
    stack = inspect.stack()
    callers = []

    for frame_info in stack:  # [2:]:  # skip wrapper and pandas internals

        # Skip frames inside this hook file
        if frame_info.filename == __file__:
            continue

        # - Skip pandas internal frames
        # - actually dont skip those as this caller info is useful to distinguish
        #   (pd?) internally triggered calls of cur.execute after pd.read_sql
        # - logs are cleaned later of internal calls
        # if "pandas" in frame_info.filename.replace("\\", "/"):
        #     continue

        callers.append(frame_info)

        if len(callers) >= max_depth:
            break

    if not callers:
        return "Unknown caller"

    chain_list = []
    for fi in callers:
        chain_list.append(_format_frame(fi))

    return chain_list


def _sanitize_insert_query(query):
    """
    Convert an INSERT query with values to a template showing structure only.
    
    Example:
    INSERT INTO table (col1, col2, col3) VALUES (1, 'abc', 3.14)
    →
    INSERT INTO table (col1, col2, col3) VALUES (?, ?, ?)
    """
    # Match VALUES (...) patterns and replace with placeholders
    sanitized = re.sub(
        r'VALUES\s*\((.*?)\)',
        lambda m: f"VALUES ({', '.join('?' for _ in m.group(1).split(','))})",
        query,
        flags=re.IGNORECASE | re.DOTALL
    )
    return sanitized

def _check_same_as_last(record):
    """Check if the new record is the same as the last logged record."""
    if not IO_LOG_RECORDS:
        return False
    last_record = IO_LOG_RECORDS[-1]
    caller_chain_cols_last = [k for k in last_record.keys() if k.startswith("caller_")]
    caller_chain_cols = [k for k in record.keys() if k.startswith("caller_")]
    if len(caller_chain_cols) != len(caller_chain_cols_last):
        return False
    keys_to_check = caller_chain_cols + ["action", 'io_context', "source", "target", "query", "user", "cwd"]
    for key in keys_to_check:
        if record.get(key) is None and last_record.get(key) is None:
            continue
        if record.get(key) != last_record.get(key):
            return False
    return True


def _log(action, source=None, target=None, query=None, duration_ms=None, meta=None):

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    caller_chain = _get_call_chain()
    io_ctx = get_io_context()

    record = {
        "module": module_name,
        "timestamp": timestamp,
        "io_context": io_ctx,
        "count": 1,
        "action": action,
        "source": str(source) if source else None,
        "target": str(target) if target else None,
        "query": query if not query or action != "pyodbc.cursor.execute" else _sanitize_insert_query(query),
        "duration_ms": duration_ms,
        "user": user_name,
        "cwd": cwd,
        "meta": meta or {}
    }
    # flatten caller chain for JSON serialization
    for i, caller in enumerate(caller_chain):
        record[f"caller_{i+1}_file"] = caller["file"]
        record[f"caller_{i+1}_line"] = caller["line"]
        record[f"caller_{i+1}_function"] = caller["function"]

    # Check for duplicate with last record
    if _check_same_as_last(record):
        IO_LOG_RECORDS[-1]["count"] += 1
        IO_LOG_RECORDS[-1]["duration_ms"] += duration_ms or 0
        return None  # skip logging duplicate

    IO_LOG_RECORDS.append(record)

    # Optional display for debugging (pretty one-line summary)
    if caller_chain:
        display_chain = " -> ".join(
            f"{c['file']}:{c['line']} in {c['function']}" for c in caller_chain
        )
    else:
        display_chain = "Unknown"

    io_ctx_print_str = None
    if io_ctx:
        io_ctx_print_str = io_ctx.split('io_ctx_id')[0]
    print(f"[io_log: {timestamp}] [{io_ctx_print_str}] {action}: src={source} tgt={target} | caller: {display_chain}")

    return None


# functions for external accessing / usage
def get_registered_io_actions():
    """Return a set of registered I/O action types."""
    return set([
        "pd_read_csv",
        "pd_to_csv",
        "pd_read_pickle",
        "pd_to_pickle",
        "pd_read_excel",
        "pd_read_sql",
        "pyodbc.cursor.execute",
        "pyodbc.cursor.executemany"
    ])

def write_io_logs_to_csv(fp_io_logs=None):

    # logs to pandas
    df_io_logs = pd.DataFrame(IO_LOG_RECORDS)

    # pandas to csv
    if not fp_io_logs:
        fp_io_logs = 'io_logs.csv'
    print(f'writing {fp_io_logs}')
    df_io_logs.to_csv(fp_io_logs, index=False, sep=';')
    print('done')

    return None



# ---------------- Patch IO functions ----------------
# Save originals so we can call them
_original_pd_read_csv = pd.read_csv
_original_pd_to_csv = pd.DataFrame.to_csv
_original_pd_read_pickle = pd.read_pickle
_original_pd_to_pickle = pd.DataFrame.to_pickle
_original_pd_read_sql = pd.read_sql
_original_pd_read_excel = pd.read_excel


@functools.wraps(_original_pd_read_csv)
def _hooked_pd_read_csv(*args, **kwargs):
    # try to extract the filepath (pandas signature uses filepath_or_buffer)
    filepath = None
    if args:
        filepath = args[0]
    else:
        filepath = kwargs.get("filepath_or_buffer") or kwargs.get("path")
    start = time.perf_counter()
    result = _original_pd_read_csv(*args, **kwargs)
    duration_ms = (time.perf_counter() - start) * 1000
    _log("pd_read_csv", source=filepath, duration_ms=duration_ms)
    return result

@functools.wraps(_original_pd_to_csv)
def _hooked_pd_to_csv(self, *args, **kwargs):
    # extract path_or_buf (first positional argument or kwarg)
    if args:
        # for DataFrame.to_csv, args[0] = path_or_buf
        filepath = args[0]
    else:
        filepath = kwargs.get("path_or_buf") or kwargs.get("path")

    start = time.perf_counter()
    result = _original_pd_to_csv(self, *args, **kwargs)
    duration_ms = (time.perf_counter() - start) * 1000

    _log("pd_to_csv", target=filepath, duration_ms=duration_ms)
    return result

@functools.wraps(_original_pd_read_excel)
def _hooked_pd_read_excel(*args, **kwargs):
    # extract the filepath-like argument (pandas.read_excel signature uses `io`)
    if args:
        filepath = args[0]
    else:
        filepath = (
            kwargs.get("io") 
            or kwargs.get("path") 
            or kwargs.get("excel_io")  # older / alternative kw
        )

    start = time.perf_counter()
    result = _original_pd_read_excel(*args, **kwargs)
    duration_ms = (time.perf_counter() - start) * 1000
    _log("pd_read_excel", source=filepath, duration_ms=duration_ms)
    return result

@functools.wraps(_original_pd_read_pickle)
def _hooked_pd_read_pickle(*args, **kwargs):
    filepath = None
    if args:
        filepath = args[0]
    else:
        filepath = kwargs.get("path") or kwargs.get("filepath_or_buffer")
    start = time.perf_counter()
    result = _original_pd_read_pickle(*args, **kwargs)
    duration_ms = (time.perf_counter() - start) * 1000
    _log("pd_read_pickle", source=filepath, duration_ms=duration_ms)
    return result

@functools.wraps(_original_pd_to_pickle)
def _hooked_pd_to_pickle(self, path, *args, **kwargs):
    start = time.perf_counter()
    result = _original_pd_to_pickle(self, path, *args, **kwargs)
    duration_ms = (time.perf_counter() - start) * 1000
    _log("pd_to_pickle", target=path, duration_ms=duration_ms)
    return result

@functools.wraps(_original_pd_read_sql)
def _hooked_pd_read_sql(sql, con, *args, **kwargs):
    start = time.perf_counter()
    result = _original_pd_read_sql(sql, con, *args, **kwargs)
    duration_ms = (time.perf_counter() - start) * 1000
    
    conn_repr = getattr(con, 'dsn', None) or str(con)
    _log("pd_read_sql", source=conn_repr, query=sql, duration_ms=duration_ms)
    return result

# we use a wrapper around pyodbc.Connection to hook the cursor.execute method
# since cursor.execute is not directly accessible for patching
# and neither is connection.cursor
# as both are readonly attributes
class _HookedPyodbcCursor:
    """Wrapper around pyodbc.Cursor that logs execute calls."""
    def __init__(self, cursor):
        self._cursor = cursor
    
    def execute(self, sql, *args, **kwargs):
        start = time.perf_counter()
        try:
            result = self._cursor.execute(sql, *args, **kwargs)
            duration_ms = (time.perf_counter() - start) * 1000
            _log("pyodbc.cursor.execute", query=sql, duration_ms=duration_ms, meta={"status": "success"})
            return result
        except Exception as e:
            duration_ms = (time.perf_counter() - start) * 1000
            _log("pyodbc.cursor.execute", query=sql, duration_ms=duration_ms, meta={"status": "error", "error": str(e)})
            raise

    def executemany(self, sql, seq_of_parameters):
        start = time.perf_counter()
        try:
            result = self._cursor.executemany(sql, seq_of_parameters)
            duration_ms = (time.perf_counter() - start) * 1000
            _log("pyodbc.cursor.executemany", query=sql, duration_ms=duration_ms, meta={"status": "success"})
            return result
        except Exception as e:
            duration_ms = (time.perf_counter() - start) * 1000
            _log("pyodbc.cursor.executemany", query=sql, duration_ms=duration_ms, meta={"status": "error", "error": str(e)})
            raise

    def __getattr__(self, name):
        # Delegate all other attributes/methods to the wrapped cursor
        return getattr(self._cursor, name)

class _HookedPyodbcConnection:
    """Wrapper around pyodbc.Connection that returns hooked cursors."""
    def __init__(self, connection):
        self._connection = connection
    
    def cursor(self, *args, **kwargs):
        """Return a wrapped cursor."""
        cursor = self._connection.cursor(*args, **kwargs)
        return _HookedPyodbcCursor(cursor)

    #######
    # - below two defintions ensure that the hook works in a context manager situation,
    #   i.e. if the actual code is liek:
    # with conn_gen() as conn:
    #     df = pd.read_sql(query, conn)
    # - apparently this doesnt work with __getattr__, since enter and exit are methods encoded in C and not visible to __getattr__
    def __enter__(self):
        self._connection.__enter__()  # enter the real connection
        return self                   # but return the WRAPPED connection

    def __exit__(self, exc_type, exc, tb):
        return self._connection.__exit__(exc_type, exc, tb)
    #######

    def __getattr__(self, name):
        # Delegate all other attributes/methods to the wrapped connection
        return getattr(self._connection, name)


_original_pyodbc_connect = pyodbc.connect

@functools.wraps(_original_pyodbc_connect)
def _hooked_pyodbc_connect(*args, **kwargs):
    """Hook pyodbc.connect() to return a wrapped connection."""
    connection = _original_pyodbc_connect(*args, **kwargs)
    return _HookedPyodbcConnection(connection)


def install_io_hooks():
    """Install io hooks (idempotent)."""
    # install only if not already installed
    if pd.read_csv is not _hooked_pd_read_csv:
        pd.read_csv = _hooked_pd_read_csv

    if pd.DataFrame.to_csv is not _hooked_pd_to_csv:
        pd.DataFrame.to_csv = _hooked_pd_to_csv

    if pd.read_pickle is not _hooked_pd_read_pickle:
        pd.read_pickle = _hooked_pd_read_pickle

    if pd.DataFrame.to_pickle is not _hooked_pd_to_pickle:
        pd.DataFrame.to_pickle = _hooked_pd_to_pickle

    if pd.read_excel is not _hooked_pd_read_excel:
        pd.read_excel = _hooked_pd_read_excel

    if pd.read_sql is not _hooked_pd_read_sql:
        pd.read_sql = _hooked_pd_read_sql

    if pyodbc.connect is not _hooked_pyodbc_connect:
        pyodbc.connect = _hooked_pyodbc_connect
    print("I/O hooks installed.")

# Install hooks on import
install_io_hooks()
