from data_lineage.lineage_parsers.sql_parser import resolve_sql_lineage
from data_lineage.lineage_parsers.sql_parser import classify_sql

# test cases
def test_resolve_sql_lineage(sql, expected):

    results = resolve_sql_lineage(sql)
    print(f'test sql: {sql}')
    assert set(results['sources']) == set(expected['sources']), f"Expected {expected['sources']}, got {results['sources']}"
    assert set(results['targets']) == set(expected['targets']), f"Expected {expected['targets']}, got {results['targets']}"
    print('passed!')

    return None

def run_sql_lineage_tests():

    ###################
    # select from tests
    ###################
    sql = "SELECT * FROM schema.table1 as tab1;"
    expected = {'sources': ['schema.table1'], 'targets': []}
    test_resolve_sql_lineage(sql, expected)

    sql = "SELECT col1, col2 FROM db.schema.table2 WHERE col3 > 100;"
    expected = {'sources': ['db.schema.table2'], 'targets': []}
    test_resolve_sql_lineage(sql, expected)


    ###################
    # create view tests
    ###################
    sql = """
        CREATE VIEW sales.vw_revenue AS
        WITH base AS (
            SELECT * FROM source.orders
        ),
        agg AS (
            SELECT customer_id, SUM(amount) AS total
            FROM base
            GROUP BY customer_id
        )
        SELECT a.customer_id, a.total, c.region
        FROM agg a
        JOIN source.customers c ON c.id = a.customer_id;"""
    expected = {'sources': ['source.customers', 'source.orders'], 'targets': ['sales.vw_revenue']}
    test_resolve_sql_lineage(sql, expected)

    sql="""CREATE VIEW dbo.V_New AS
        WITH vcte AS (
            SELECT * FROM dbo.Physical3
        )
        SELECT * FROM vcte JOIN dbo.Physical4 p4 ON vcte.id = p4.id"""
    expected = {'sources': ['dbo.Physical3', 'dbo.Physical4'], 'targets': ['dbo.V_New']}
    test_resolve_sql_lineage(sql, expected)

    sql="""CREATE VIEW V_New AS
        WITH vcte AS (
            SELECT * FROM Physical3
        )
        SELECT * FROM vcte JOIN dbo.Physical4 p4 ON vcte.id = p4.id"""
    expected = {'sources': ['Physical3', 'dbo.Physical4'], 'targets': ['V_New']}
    test_resolve_sql_lineage(sql, expected)


    ###################
    # select into tests
    ###################
    sql = """
        SELECT *
        INTO [new_schema].[new_table]
        FROM [db1].[t1] t
        JOIN db2.t2 ON t.id = t2.id;"""
    expected = {'sources': ['db1.t1', 'db2.t2'], 'targets': ['new_schema.new_table']}
    test_resolve_sql_lineage(sql, expected)

    sql = """
        WITH cte1 AS (
            SELECT * FROM dbo.Physical1
        ),
        cte2 AS (
            SELECT * FROM cte1 JOIN dbo.Physical2 p2 ON cte1.id = p2.id
        )
        SELECT * INTO dbo.NewTable FROM cte2"""
    expected = {'sources': ['dbo.Physical1', 'dbo.Physical2'], 'targets': ['dbo.NewTable']}
    test_resolve_sql_lineage(sql, expected)

    sql = """SELECT * INTO dbo.OnlyFromView FROM V_AnotherView"""
    expected = {'sources': ['V_AnotherView'], 'targets': ['dbo.OnlyFromView']}
    test_resolve_sql_lineage(sql, expected)

    sql = """WITH cte1 AS (
            SELECT * FROM dbo.V_ViewA
        ),
        cte2 AS (
            SELECT * FROM cte1 JOIN V_ViewB b ON cte1.id = b.id
        )
        SELECT * INTO dbo.NewTable_1 FROM cte2"""
    expected = {'sources': ['V_ViewB', 'dbo.V_ViewA'], 'targets': ['dbo.NewTable_1']}
    test_resolve_sql_lineage(sql, expected)

    sql="""SELECT * INTO dbo.OnlyFromView_2 FROM V_ViewOnly;"""
    expected = {'sources': ['V_ViewOnly'], 'targets': ['dbo.OnlyFromView_2']}
    test_resolve_sql_lineage(sql, expected)

    ###################
    # Insert Into test
    ###################
    sql = """
        INSERT INTO dbo.target_table (id, name)
        SELECT id, name FROM dbo.source_table;"""
    expected = {'sources': ['dbo.source_table'], 'targets': ['dbo.target_table']}
    test_resolve_sql_lineage(sql, expected)

    ###################
    # Merge Into test
    ###################
    sql = """
        MERGE INTO dbo.tgt AS t
        USING dbo.src AS s
        ON t.id = s.id
        WHEN MATCHED THEN UPDATE SET t.value = s.value;"""
    expected = {'sources': ['dbo.src'], 'targets': ['dbo.tgt']}
    test_resolve_sql_lineage(sql, expected)

    ###################
    # Drop Table test
    ###################
    sql = "DROP TABLE random_data;"
    expected = {'sources': [], 'targets': ['random_data']}
    test_resolve_sql_lineage(sql, expected)

    ###################
    # Create Table test
    ###################
    sql = """CREATE TABLE random_data (
        "col_1" REAL,
        "col_2" REAL,
        "col_3" REAL
        )"""
    expected = {'sources': [], 'targets': ['random_data']}
    test_resolve_sql_lineage(sql, expected)

    sql = """CREATE TABLE schema.random_data (
        "col_1" REAL,
        "col_2" REAL,
        "col_3" REAL
        )"""
    expected = {'sources': [], 'targets': ['schema.random_data']}
    test_resolve_sql_lineage(sql, expected)

    ###################
    # Delete From test
    ###################
    sql = "DELETE FROM random_data WHERE rowid > 5;"
    expected = {'sources': [], 'targets': ['random_data']}
    test_resolve_sql_lineage(sql, expected)


    # not sure how we want to handle temp tables yet
    # sql = """SELECT t.col INTO dbo.Derived FROM PhysicalTable2 t JOIN #temp z ON t.x = z.x"""
    # test_resolve_sql_lineage((sql)
    return None

def run_sql_classify_test():

    print('run_sql_classify_test')

    sql = "SELECT id, name FROM analytics.users WHERE active = 1"
    assert 'data_retrieval' == classify_sql(sql), f'classification failed on {sql}'
    print(f'passed for "{sql}" as {classify_sql(sql)}')

    sql = "CREATE TABLE analytics.new_users (id INT, name TEXT)"
    assert 'object_modification' == classify_sql(sql), f'classification failed on {sql}'
    print(f'passed for "{sql}" as {classify_sql(sql)}')

    sql = "CREATE VIEW v AS SELECT * FROM t"
    assert 'object_modification' == classify_sql(sql), f'classification failed on {sql}'
    print(f'passed for "{sql}" as {classify_sql(sql)}')

    sql = 'INSERT INTO target SELECT * FROM source'
    assert 'object_modification' == classify_sql(sql), f'classification failed on {sql}'
    print(f'passed for "{sql}" as {classify_sql(sql)}')

    sql = "INSERT INTO t VALUES (1,'x',3)"
    assert 'data_upload' == classify_sql(sql), f'classification failed on {sql}'
    print(f'passed for "{sql}" as {classify_sql(sql)}')

    return None


if __name__ == "__main__":
    run_sql_lineage_tests()
    run_sql_classify_test()
