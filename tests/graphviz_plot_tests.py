from data_lineage.lineage_network.network_plot import draw_lineage_plot

nodes = [
    {
        'id': '1',
        'name': 'raw_orders',
        'layer': 'RAW',
        'color': 'lightgray',
        'type': 'db_object'
    },
    {
        'id': '2',
        'name': 'raw_customers',
        'layer': 'RAW',
        'color': 'lightgray',
        'type': 'db_object'
    },
    {
        'id': '3',
        'name': 'raw_products',
        'layer': 'RAW',
        'color': 'lightgray',
        'type': 'db_object'
    },
    {
        'id': '4',
        'name': 'raw_suppliers',
        'layer': 'RAW',
        'color': 'lightgray',
        'type': 'db_object'
    },
    {
        'id': '5',
        'name': 'stg_customers',
        'layer': 'STG',
        'color': 'lightblue',
        'type': 'db_object'
    },
    {
        'id': '6',
        'name': 'stg_orders',
        'layer': 'STG',
        'color': 'lightblue',
        'type': 'db_object'
    },
    {
        'id': '7',
        'name': 'stg_products',
        'layer': 'STG',
        'color': 'lightblue',
        'type': 'file'
    },
    {
        'id': '8',
        'name': 'stg_suppliers',
        'layer': 'STG',
        'color': 'lightblue',
        'type': 'file'
    },
    {
        'id': '9',
        'name': 'int_orders_cleaned',
        'layer': 'INT',
        'color': 'lightyellow',
        'type': 'db_object'
    },
    {
        'id': '10',
        'name': 'int_customers_cleaned',
        'layer': 'INT',
        'color': 'lightyellow',
        'type': 'db_object'
    },
    {
        'id': '11',
        'name': 'int_products_cleaned',
        'layer': 'INT',
        'color': 'lightyellow',
        'type': 'file'
    },
    {
        'id': '12',
        'name': 'int_orders_with_customer',
        'layer': 'INT',
        'color': 'lightyellow',
        'type': 'db_object'
    },
    {
        'id': '13',
        'name': 'int_orders_with_product',
        'layer': 'INT',
        'color': 'lightyellow',
        'type': 'file'
    },
    {
        'id': '14',
        'name': 'dim_suppliers',
        'layer': 'DIM',
        'color': 'lightgreen',
        'type': 'db_object'
    },
    {
        'id': '15',
        'name': 'dim_customers',
        'layer': 'DIM',
        'color': 'lightgreen',
        'type': 'db_object'
    },
    {
        'id': '16',
        'name': 'dim_products',
        'layer': 'DIM',
        'color': 'lightgreen',
        'type': 'db_object'
    },
    {
        'id': '17',
        'name': 'fct_order_items',
        'layer': 'FACT',
        'color': 'orange',
        'type': 'db_object'
    },
    {
        'id': '18',
        'name': 'fct_sales_summary',
        'layer': 'FACT',
        'color': 'orange',
        'type': 'db_object'
    },
    {
        'id': '19',
        'name': 'mart_daily_sales',
        'layer': 'MART',
        'color': 'plum',
        'type': 'db_object'
    },
    {
        'id': '20',
        'name': 'mart_monthly_sales',
        'layer': 'MART',
        'color': 'plum',
        'type': 'file'
    },
    {
        'id': '21',
        'name': 'mart_supplier_quality',
        'layer': 'MART',
        'color': 'plum',
        'type': 'db_object'
    }
]

edges = [
    {'src_id': '1', 'tgt_id': '6'},
    {'src_id': '2', 'tgt_id': '5'},
    {'src_id': '3', 'tgt_id': '7'},
    {'src_id': '4', 'tgt_id': '8'},
    {'src_id': '6', 'tgt_id': '9'},
    {'src_id': '5', 'tgt_id': '10'},
    {'src_id': '7', 'tgt_id': '11'},
    {'src_id': '8', 'tgt_id': '14'},
    {'src_id': '9', 'tgt_id': '12'},
    {'src_id': '10', 'tgt_id': '12'},
    {'src_id': '12', 'tgt_id': '13'},
    {'src_id': '11', 'tgt_id': '13'},
    {'src_id': '13', 'tgt_id': '17'},
    {'src_id': '13', 'tgt_id': '18'},
    {'src_id': '17', 'tgt_id': '19'},
    {'src_id': '18', 'tgt_id': '19'},
    {'src_id': '18', 'tgt_id': '20'},
    {'src_id': '5', 'tgt_id': '15'},
    {'src_id': '7', 'tgt_id': '16'},
    {'src_id': '14', 'tgt_id': '21'}
]

layer_order = ["RAW", "STG", "INT", "DIM", "FACT", "MART", "OTHER"]

draw_lineage_plot(nodes, edges, layer_order)



