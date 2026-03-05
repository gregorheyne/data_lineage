import os
from data_lineage.lineage_network.network_base import register_node
from data_lineage.lineage_network.network_base import register_edge
from data_lineage.lineage_parsers.sql_parser import resolve_sql_lineage
from data_lineage.lineage_parsers.sql_parser import classify_sql

def process_io_logs_df(
        df_io_logs,
        str_required_in_caller_one_file=None,
        str_forbidden_in_caller_one_file=None):

    # group by module, user, cwd
    groupby_cols = ['module', 'user', 'cwd']
    df_io_logs['module_GROUP'] = df_io_logs.groupby(groupby_cols).transform('ngroup') + 1
    # set a python node based on module and io_context
    df_io_logs['PYTHON_NODE_NAME'] = df_io_logs['module'] + ' (' + df_io_logs['io_context'] + ')'
    # set an source_type column that can be used later for defining layers in plotting
    df_io_logs['source_type'] = 'io_logs_py'

    if str_required_in_caller_one_file:
        # str_required_in_caller_one_file = 'Documents/coding/transfer/data_architecture'
        flag_1 = df_io_logs['caller_1_file'].str.contains(str_required_in_caller_one_file)
        print(f'removing {(~flag_1).sum()} log statements not having {str_required_in_caller_one_file} in "caller_1_file')
        df_io_logs = df_io_logs[flag_1]

    return df_io_logs

def add_io_logs_to_network(df_io_logs):

    # get unique action types:
    actions_in_io_logs = set(df_io_logs['action'].unique())

    # distinguish file io and db io actions
    file_read_actions = ['pd_read_csv', 'pd_read_pickle', 'pd_read_excel']
    file_write_actions = ['pd_to_csv', 'pd_to_pickle']
    db_read_actions = ['pd_read_sql']
    db_cursor_actions = ['pyodbc.cursor.execute', 'pyodbc.cursor.executemany']

    # - retrieve (combined) sources and targets within each record
    #  - for file io actions, source and target are files
    #  - for db io actions, resolve lineage from query 
    # - and populate nodes dict including type info
    io_records = df_io_logs.to_dict(orient='records')
    meta_attributes_for_nodes = ['io_context', 'module', 'source_type']
    treated_io_types = set()
    for record in io_records:
        # record = io_records[0]
        if record['action'] in file_read_actions:
            src = record['source']
            tgt = record['PYTHON_NODE_NAME']
            record_meta_dict = {key: record[key] for key in record.keys() if key in meta_attributes_for_nodes}
            register_node(src, 'file', meta_dict=record_meta_dict)
            register_node(tgt, 'py_node', meta_dict=record_meta_dict)
            register_edge(src, tgt, 'to_py_node')
            treated_io_types = treated_io_types.union(file_read_actions)
        if record['action'] in file_write_actions:
            src = record['PYTHON_NODE_NAME']
            tgt = record['target']
            record_meta_dict = {key: record[key] for key in record.keys() if key in meta_attributes_for_nodes}
            register_node(src, 'py_node', meta_dict=record_meta_dict)
            register_node(tgt, 'file', meta_dict=record_meta_dict)
            register_edge(src, tgt, 'from_py_node')
            treated_io_types = treated_io_types.union(file_write_actions)
        if record['action'] in db_read_actions:
            record_meta_dict = {key: record[key] for key in record.keys() if key in meta_attributes_for_nodes}
            query = record['query']
            query_lineage = resolve_sql_lineage(query)
            srcs = query_lineage['sources']
            tgts = query_lineage['targets']
            assert not tgts, f'found targets in {query} for {record["action"]}'
            # fill nodes and edges
            tgt = record['PYTHON_NODE_NAME']
            register_node(tgt, 'py_node', meta_dict=record_meta_dict)
            for src in srcs:
                node_meta = record_meta_dict | ({'schema': src['schema']} if src.get('schema') else {})
                register_node(src['combined_name'], 'db_object', meta_dict=node_meta)
                register_edge(src['combined_name'], tgt, 'to_py_node')
            treated_io_types = treated_io_types.union(db_read_actions)
        if record['action'] in db_cursor_actions:
            record_meta_dict = {key: record[key] for key in record.keys() if key in meta_attributes_for_nodes}
            query = record['query']
            try:
                query_classification = classify_sql(query)
                if query_classification == 'not_classified':
                    print(f'not classified query: {query}')
                    continue
            except Exception as e:
                print(f'classify_sql failed on:\n{query}')
                print(f'Exception:\n{e}')
                continue
            query_lineage = resolve_sql_lineage(query)
            sources = query_lineage['sources']
            targets = query_lineage['targets']
            if query_classification == 'data_retrieval':
                # check that targets in query lineage is empty
                assert not targets, 'found targets in data retrieval query'
                # add nodes and edges
                tgt = record['PYTHON_NODE_NAME']
                register_node(tgt, 'py_node', meta_dict=record_meta_dict)
                for src in sources:
                    node_meta = record_meta_dict | ({'schema': src['schema']} if src.get('schema') else {})
                    register_node(src['combined_name'], 'db_object', meta_dict=node_meta)
                    register_edge(src['combined_name'], tgt, 'to_py_node')
            if query_classification == 'data_upload':
                # check that sources in query lineage is empty
                assert not sources, 'found sources in data upload query'
                # add nodes and edges
                src = record['PYTHON_NODE_NAME']
                register_node(src, 'py_node', meta_dict=record_meta_dict)
                for tgt in targets:
                    node_meta = record_meta_dict | ({'schema': tgt['schema']} if tgt.get('schema') else {})
                    register_node(tgt['combined_name'], 'db_object', meta_dict=node_meta)
                    register_edge(src, tgt['combined_name'], 'from_py_node')
            if query_classification == 'object_modification':
                if sources and targets:
                    for src in sources:
                        for tgt in targets:
                            src_meta = record_meta_dict | ({'schema': src['schema']} if src.get('schema') else {})
                            tgt_meta = record_meta_dict | ({'schema': tgt['schema']} if tgt.get('schema') else {})
                            register_node(src['combined_name'], 'db_object', meta_dict=src_meta)
                            register_node(tgt['combined_name'], 'db_object', meta_dict=tgt_meta)
                            register_edge(src['combined_name'], tgt['combined_name'], 'db_native')
                if sources and not targets:
                    assert 1==2, 'detected object_modification query without targets'
                if not sources and targets:
                    for tgt in targets:
                        node_meta = record_meta_dict | ({'schema': tgt['schema']} if tgt.get('schema') else {})
                        register_node(tgt['combined_name'], 'db_object', meta_dict=node_meta)
            treated_io_types = treated_io_types.union(db_cursor_actions)
    assert actions_in_io_logs.difference(treated_io_types) == set(), 'detected io action without node/edge mapping'

    return None


def add_pbip_sources_to_network(path_to_pbip_file, pbip_sources):

    pbi_name = os.path.basename(path_to_pbip_file)

    for pbip_source in pbip_sources:
        # pbip_source = pbip_sources[0]
        src = pbip_source['name']
        tgt = pbi_name

        src_meta_dict = {'source_type': 'PBI', 'pbi_name': pbi_name, 'module': pbi_name}
        if (pbip_source['type'] == 'db_object') and pbip_source['schema']:
            src_meta_dict = src_meta_dict | {'schema': pbip_source['schema']}

        register_node(src, pbip_source['type'], meta_dict=src_meta_dict)
        register_node(tgt, 'pbi', meta_dict={'source_type': 'PBI', 'pbi_name': pbi_name, 'module': pbi_name})
        register_edge(src, tgt, 'to_pbi_node')

    return None


