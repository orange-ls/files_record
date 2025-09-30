import psycopg2

src_conn = psycopg2.connect(
    host="10.0.23.199",
    port="5432",
    user="xc",
    password="Dcxc7888$",
    dbname="xc_materiel"
)

tgt_conn = psycopg2.connect(
    host="10.0.23.146",
    port="54321",
    user="odoo",
    password="xctest$",
    dbname="xc-test"
)

def generate_seatunnel_conf(table_name):
    src_cur = src_conn.cursor()
    tgt_cur = tgt_conn.cursor()

    src_cur.execute("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name=%s ORDER BY ordinal_position
    """, (table_name,))
    src_cols = [r[0] for r in src_cur.fetchall()]

    tgt_cur.execute("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name=%s ORDER BY ordinal_position
    """, (table_name,))
    tgt_cols = [r[0] for r in tgt_cur.fetchall()]

    common_cols = [c for c in src_cols if c in tgt_cols]

    col_str = ",".join(common_cols)
    placeholders = ",".join(["?"] * len(common_cols))

    conf = f"""
env {{
  execution.parallelism = 2
  job.mode = "BATCH"
}}

source {{
  Jdbc {{
    url = "jdbc:postgresql://10.0.23.199:5432/xc_materiel"
    driver = "org.postgresql.Driver"
    user = "xc"
    password = "Dcxc7888$"
    query = "SELECT {col_str} FROM {table_name};"
  }}
}}

transform {{}}

sink {{
  jdbc {{
    url = "jdbc:postgresql://10.0.23.146:54321/xc-test"
    driver = "org.postgresql.Driver"
    user = "odoo"
    password = "xctest$"
    query = "INSERT INTO {table_name} ({col_str}) VALUES ({placeholders});"
  }}
}}
    """
    return conf


table_map = [
    {'en': 'purchase_order_inventory', 'ch': 'PO单与存量'},
    {'en': 'base_material', 'ch': '物料基础数据'},
    {'en': 'bundling_part_number', 'ch': '捆绑料号'},
    {'en': 'non_electronic_materials', 'ch': '非电子物料'},
    {'en': 'material_bom', 'ch': '物料BOM'},
    {'en': 'reservoir_area_stock', 'ch': '各库区库存'},
    {'en': 'other_reservoir_area_stock', 'ch': '其他库区库存'},
    {'en': 'kunpeng_daily', 'ch': '鲲鹏日报'},
    {'en': 'rma_transit', 'ch': 'RMA在途'},
    {'en': 'purchasing_transit', 'ch': '采购在途'},
    {'en': 'material_transformation', 'ch': '物料转换'},
    {'en': 'reject_ratio', 'ch': '不良率'},
    {'en': 'dump_transit', 'ch': '转储在途'},
]

for t in table_map:
    table_name = t['en']
    table_name_ch = t['ch']
    print(f"*********表名: {table_name_ch}*************\n")
    print(generate_seatunnel_conf(table_name))
    print('\n\n')
