from sqlglot import parse_one, exp
import sqlglot
import re

sqlglot_version = tuple(int(part) for part in sqlglot.__version__.split(".")[:2])
assert sqlglot_version >= (10, 0), "sqlglot version 10.0 or higher is required"

def resolve_sql_lineage(sql: str, dialect: str = "tsql"):
    """
    Resolve data lineage for a single SQL statement.

    Parameters:
        sql (str): SQL statement (single statement only)
        dialect (str): SQL dialect for sqlglot parser (default 'tsql')

    Returns:
        dict: {"input_sources": [...], "output_targets": [...]}

    Raises:
        ValueError: if multiple statements are detected
    """
    # Preprocess SQL to handle DB2-specific syntax
    sql = _preprocess_db2_sql(sql)
    
    # Parse SQL using specified dialect
    tree = parse_one(sql, read=dialect)

    # Detect multiple statements
    if tree is None:
        raise ValueError("Unable to parse SQL statement.")
    if hasattr(tree, "statements") and len(tree.statements) > 1:
        raise ValueError("Multiple statements detected; only single statement supported.")

    # Step 1: gather CTE names
    cte_names = _get_cte_names(tree)

    # Step 2: gather output targets
    targets = _get_targets(tree)

    # Step 3: gather input sources, excluding CTEs and targets
    sources = _get_sources(tree, cte_names, targets)

    return {
        "sources": sorted(sources),
        "targets": sorted(targets),
    }


def classify_sql(sql: str, dialect: str = "tsql") -> str:
    """
    Classify SQL into one of:
        - "object_modification"
        - "data_upload"
        - "data_retrieval"
        - "index_creation"
    """
    # Preprocess SQL to handle DB2-specific syntax
    sql_preprocessed = _preprocess_db2_sql(sql)
    
    tree = parse_one(sql_preprocessed, read=dialect)

    # -----------------------------------------------
    # 0. Check for CREATE INDEX (index_creation)
    # -----------------------------------------------
    if isinstance(tree, exp.Create) and tree.kind == "INDEX":
        return "index_creation"

    # -----------------------------------------------
    # 1. Check for SELECT ... INTO (object_modification)
    # -----------------------------------------------
    # Must check before generic SELECT check, since SELECT ... INTO is also an exp.Select
    if isinstance(tree, exp.Select) and tree.find(exp.Into):
        return "object_modification"

    # -----------------------------------------------
    # 2. Detect queries that retrieve data
    # -----------------------------------------------
    if isinstance(tree, exp.Select):
        return "data_retrieval"

    # A SELECT wrapped in CTEs still retrieves data
    if isinstance(tree, exp.With) and isinstance(tree.this, exp.Select):
        return "data_retrieval"

    # -----------------------------------------------
    # 2. Detect external literal uploads
    # -----------------------------------------------

    # INSERT ... VALUES (...)
    for insert in tree.find_all(exp.Insert):
        values = insert.find(exp.Values)
        if values is not None:
            return "data_upload"

    # MERGE with VALUES (...) as source → external upload
    for merge in tree.find_all(exp.Merge):
        if merge.find(exp.Values):
            return "data_upload"

    # Optional: treat UPDATE with literal RHS as external upload
    for update in tree.find_all(exp.Update):
        # If any assignment contains a literal, treat as external upload
        for assignment in update.find_all(exp.SetItem):
            if isinstance(assignment.expression, exp.Literal):
                return "data_upload"

    # -----------------------------------------------
    # 3. Object-modifying operations without literal uploads
    # -----------------------------------------------

    # CREATE VIEW, CREATE TABLE, CREATE TABLE AS SELECT (but NOT CREATE INDEX)
    if isinstance(tree, exp.Create) and tree.kind != "INDEX":
        return "object_modification"

    # INSERT ... SELECT ...
    for insert in tree.find_all(exp.Insert):
        if insert.find(exp.Select):
            return "object_modification"

    # MERGE with SELECT/table source
    for merge in tree.find_all(exp.Merge):
        return "object_modification"

    # DROP, DELETE, UPDATE structure-changing operations
    if isinstance(tree, (exp.Drop, exp.Delete, exp.Update)):
        return "object_modification"

    # Fallback
    return "not_classified"



# ---------------- Helper Functions ---------------- #

def _preprocess_db2_sql(sql: str) -> str:
    """
    Preprocess DB2-specific SQL syntax to standard SQL.
    Converts DB2 temporal keywords to standard SQL format.
    
    Parameters:
        sql (str): SQL statement with potential DB2-specific syntax
    
    Returns:
        str: Preprocessed SQL with standardized syntax
    """
    # Convert CURRENT DATE to CURRENT_DATE (case-insensitive)
    sql = re.sub(r'\bCURRENT\s+DATE\b', 'CURRENT_DATE', sql, flags=re.IGNORECASE)
    
    # Convert CURRENT TIME to CURRENT_TIME (case-insensitive)
    sql = re.sub(r'\bCURRENT\s+TIME\b', 'CURRENT_TIME', sql, flags=re.IGNORECASE)
    
    # Convert CURRENT TIMESTAMP to CURRENT_TIMESTAMP (case-insensitive)
    sql = re.sub(r'\bCURRENT\s+TIMESTAMP\b', 'CURRENT_TIMESTAMP', sql, flags=re.IGNORECASE)
    
    return sql


def _get_cte_names(tree) -> set:
    """Collect names of CTEs to exclude them from input sources."""
    return {cte.alias.lower() for cte in tree.find_all(exp.CTE) if cte.alias}


def _get_targets(tree) -> set:
    """Identify output tables/views including CREATE VIEW, SELECT INTO, INSERT INTO, MERGE INTO, DROP TABLE, DELETE, UPDATE."""
    targets = set()

    # CREATE VIEW / CREATE TABLE AS SELECT
    if isinstance(tree, exp.Create) and tree.this:
        create_target = tree.this
        # For CREATE TABLE, tree.this is a Schema, need to extract the Table from it
        if isinstance(create_target, exp.Schema):
            create_target = create_target.this
        if create_target:
            targets.add(_identifier(create_target))

    # SELECT INTO
    for into in tree.find_all(exp.Into):
        if into.this:
            targets.add(_identifier(into.this))

    # INSERT INTO
    for insert in tree.find_all(exp.Insert):
        # Correct way: extract target table via Table node
        target_table = insert.find(exp.Table, bfs=True)
        if target_table is not None:
            targets.add(_identifier(target_table))

    # MERGE INTO
    for merge in tree.find_all(exp.Merge):
        target_table = merge.find(exp.Table, bfs=True)
        if target_table is not None:
            targets.add(_identifier(target_table))

    # DROP TABLE
    if isinstance(tree, exp.Drop):
        if tree.this:
            targets.add(_identifier(tree.this))

    # DELETE FROM
    for delete in tree.find_all(exp.Delete):
        target_table = delete.find(exp.Table, bfs=True)
        if target_table is not None:
            targets.add(_identifier(target_table))

    # UPDATE
    for update in tree.find_all(exp.Update):
        target_table = update.find(exp.Table, bfs=True)
        if target_table is not None:
            targets.add(_identifier(target_table))

    return targets


def _get_sources(tree, cte_names: set, targets: set) -> set:
    """Extract input tables/views, excluding CTEs and output targets."""
    sources = set()

    for node in tree.walk():
        if isinstance(node, exp.Table):
            ident = _identifier(node)
            # exclude CTEs and targets
            if node.name.lower() not in cte_names and ident not in targets:
                # For CREATE TABLE without SELECT, skip the table being created
                # by checking if this table is the direct target of a Create statement
                parent_create = node.find_ancestor(exp.Create)
                if parent_create:
                    # tree.this could be a Schema (for CREATE TABLE) or Table (for CREATE VIEW)
                    create_target = parent_create.this
                    if isinstance(create_target, exp.Schema):
                        create_target = create_target.this
                    if node == create_target:
                        continue
                # For DROP, DELETE, UPDATE, skip the table being modified
                parent_drop = node.find_ancestor(exp.Drop)
                if parent_drop and parent_drop.this == node:
                    continue
                parent_delete = node.find_ancestor(exp.Delete)
                if parent_delete:
                    continue
                parent_update = node.find_ancestor(exp.Update)
                if parent_update:
                    continue
                sources.add(ident)

    return sources


def _identifier(node: exp.Expression) -> str:
    """
    Build fully-qualified identifier (catalog.db.table) without aliases or table hints.
    Strips T-SQL table hints like WITH (NOLOCK)
    """
    parts = []
    if getattr(node, "catalog", None):
        parts.append(node.catalog)
    if getattr(node, "db", None):
        parts.append(node.db)
    parts.append(node.name)
    return ".".join(parts)
