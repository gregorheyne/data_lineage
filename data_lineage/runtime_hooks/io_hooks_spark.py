# spark_io_logger.py

"""
Spark IO Logger Module
----------------------

Logs Spark read/write operations:
  • spark.read.format("delta").load(path) → logs format, path
  • spark.read.csv(path) → logs path
  • spark.read.format("sqlserver").option("query", "...").load() → logs query
  • All write operations (write.format(...).save(path))

Also logs Databricks execution context:
  • notebook path
  • user name
  • cluster id

To enable:
    import spark_io_logger
    spark_io_logger.enable()
"""

from pyspark.sql import DataFrameReader, DataFrameWriter

# -------------------------
# Databricks context extraction
# -------------------------

_context = {"user": "unknown", "notebook": "unknown", "cluster": "unknown"}

def _get_context_info():
    try:
        from pyspark.dbutils import DBUtils  # works in recent DBR
        dbutils = DBUtils(spark)

        ctx = dbutils.notebook().getContext()

        user = ctx.userName().get() if ctx.userName().isDefined() else "unknown"
        notebook = ctx.notebookPath().get() if ctx.notebookPath().isDefined() else "unknown"
        cluster = ctx.clusterId().get() if ctx.clusterId().isDefined() else "unknown"

        return {"user": user, "notebook": notebook, "cluster": cluster}

    except Exception:
        return {"user": "unknown", "notebook": "unknown", "cluster": "unknown"}

# -------------------------
# Internal logging function
# -------------------------

def _log(msg):
    prefix = (
        f"user={_context['user']} "
        f"notebook={_context['notebook']} "
        f"cluster={_context['cluster']}"
    )
    print(f"[SPARK IO] {prefix} | {msg}")

# -------------------------
# Save original functions
# -------------------------

_ORIG = {
    "read_load": DataFrameReader.load,
    "read_csv": DataFrameReader.csv,
    "read_json": DataFrameReader.json,
    "read_parquet": DataFrameReader.parquet,
    "read_table": DataFrameReader.table,

    "write_save": DataFrameWriter.save,
    "write_csv": DataFrameWriter.csv,
    "write_parquet": DataFrameWriter.parquet,
    "write_insertInto": DataFrameWriter.insertInto,
}

# -------------------------
# READ wrappers
# -------------------------

def _patched_read_load(self, path=None, format=None, schema=None):
    fmt = self._format or format
    opts = getattr(self, "_options", {})

    if fmt == "sqlserver":
        _log(f"READ SQLSERVER options={opts}")
        if "query" in opts:
            _log(f"QUERY: {opts['query']}")
    else:
        _log(f"READ {fmt} path={path} options={opts}")

    return _ORIG["read_load"](self, path, format, schema)


def _patched_read_csv(self, path, *a, **kw):
    _log(f"READ CSV path={path}")
    return _ORIG["read_csv"](self, path, *a, **kw)


def _patched_read_json(self, path, *a, **kw):
    _log(f"READ JSON path={path}")
    return _ORIG["read_json"](self, path, *a, **kw)


def _patched_read_parquet(self, path, *a, **kw):
    _log(f"READ PARQUET path={path}")
    return _ORIG["read_parquet"](self, path, *a, **kw)


def _patched_read_table(self, table, *a, **kw):
    _log(f"READ TABLE {table}")
    return _ORIG["read_table"](self, table, *a, **kw)

# -------------------------
# WRITE wrappers
# -------------------------

def _patched_write_save(self, path=None, *a, **kw):
    opts = getattr(self, "_options", {})
    _log(f"WRITE format={self._source} path={path} mode={self._mode} options={opts}")
    return _ORIG["write_save"](self, path, *a, **kw)


def _patched_write_csv(self, path, *a, **kw):
    _log(f"WRITE CSV path={path} mode={self._mode}")
    return _ORIG["write_csv"](self, path, *a, **kw)


def _patched_write_parquet(self, path, *a, **kw):
    _log(f"WRITE PARQUET path={path} mode={self._mode}")
    return _ORIG["write_parquet"](self, path, *a, **kw)


def _patched_write_insertInto(self, table, *a, **kw):
    _log(f"WRITE INSERT INTO TABLE {table} mode={self._mode}")
    return _ORIG["write_insertInto"](self, table, *a, **kw)

# -------------------------
# Enable / Disable
# -------------------------

def enable():
    """Enable Spark IO logging by monkey-patching DataFrameReader/Writer."""
    global _context
    _context = _get_context_info()

    # Patch reads
    DataFrameReader.load = _patched_read_load
    DataFrameReader.csv = _patched_read_csv
    DataFrameReader.json = _patched_read_json
    DataFrameReader.parquet = _patched_read_parquet
    DataFrameReader.table = _patched_read_table

    # Patch writes
    DataFrameWriter.save = _patched_write_save
    DataFrameWriter.csv = _patched_write_csv
    DataFrameWriter.parquet = _patched_write_parquet
    DataFrameWriter.insertInto = _patched_write_insertInto

    _log("Spark IO Logger ENABLED")


def disable():
    """Restore original Spark behavior."""
    # Restore reads
    DataFrameReader.load = _ORIG["read_load"]
    DataFrameReader.csv = _ORIG["read_csv"]
    DataFrameReader.json = _ORIG["read_json"]
    DataFrameReader.parquet = _ORIG["read_parquet"]
    DataFrameReader.table = _ORIG["read_table"]

    # Restore writes
    DataFrameWriter.save = _ORIG["write_save"]
    DataFrameWriter.csv = _ORIG["write_csv"]
    DataFrameWriter.parquet = _ORIG["write_parquet"]
    DataFrameWriter.insertInto = _ORIG["write_insertInto"]

    _log("Spark IO Logger DISABLED")
