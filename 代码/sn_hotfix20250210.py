import psycopg2
import psycopg2.extras
import logging
import uuid
from psycopg2.extras import execute_values

'''
    功能：获取整机存量表中的SN信息，并同步到BOM组件表中
    场景：溯源 整机存量表导入的数据没有BOM组件信息，需要同步到BOM组件表中
'''

def get_sn_data():
    try:
        # 创建数据库连接
        # # 测试环境
        connection = psycopg2.connect(
            host='10.0.23.146',
            port='54321',
            user='odoo',
            password='xctest$',
            dbname='xc-test'
        )
        # 生产环境
        # connection = psycopg2.connect(
        #     dbname="xc_materiel",
        #     user="xc",
        #     password="Dcxc7888$",
        #     host="10.0.23.199",
        #     port="5432"
        # )
        cursor = connection.cursor()

        # 获取整机存量表中的SN信息
        sql_get_sn = '''
        SELECT DISTINCT
            complete_sn 
        FROM
            "sn_service_complete_info"
        WHERE
            deliver_time BETWEEN '2024-12-25' AND '2024-12-29'
        '''
        cursor.execute(sql_get_sn)
        records = cursor.fetchall()

        sn_service_bom_info(connection, cursor, records)

        # 关闭数据库连接
        cursor.close()
        connection.close()
    except Exception as e:
        print(e)

def sn_service_bom_info(connection, cursor, records):
    sn_tuple = tuple(record[0] for record in records)
    if not sn_tuple:
        sn_tuple = ('',)
    batch_size = 500
    total_batches = (len(sn_tuple) + batch_size - 1) // batch_size  # 总批次数
    for i in range(total_batches):
        batch = sn_tuple[i * batch_size:(i + 1) * batch_size]
        logging.info(f'正在同步第 {i + 1}/{total_batches} 批次的BOM组件数据，共 {len(batch)} 条记录')
        sql = """WITH filtered_sn AS (
            SELECT *
            FROM sn_service_complete_info
            WHERE del_flag = '0' AND complete_sn IN %s
        ),
        filtered_mtdt AS (
            SELECT mtrl_prod_id_fk,real_sn,prd_seq_id_fk,mtrl_prod_dsc
            FROM ret_prd_mtdt
            WHERE mtrl_prod_id_fk != ''  and mtrl_prod_id_fk != prd_seq_id_fk
              AND (mtrl_mdl_stat IS NULL OR mtrl_mdl_stat NOT IN ('N', 'DISM')) AND UPPER(prd_seq_id_fk) IN %s
        )
        SELECT DISTINCT
            s.delivery_no,
            COALESCE(s.complete_sn, '') AS complete_sn,
            s.service_start_time,
            s.maintenance_service_end_date,
            s.service_product_type,
            s.customer_name,
            s.proj_name,
            s.crm_no AS crm_no,
            NULL AS material_supplier,
            CASE
                WHEN m.mtrl_prod_id_fk IS NOT NULL AND m.mtrl_prod_id_fk != ''
                THEN reverse(SUBSTRING(reverse(m.mtrl_prod_id_fk), 7))::INT || '-' || reverse(SUBSTRING(reverse(m.mtrl_prod_id_fk), 1, 6))
                ELSE ''
            END AS material_code,
            m.mtrl_prod_dsc AS material_desc,
            COALESCE(m.real_sn, '') AS bom_sn,
            s.complete_sale,
            s.complete_purchase_time,
            s.province,
            s.city,
            s.delivery_address,
            s.deliver_time,
            1 AS material_num,
            NULL AS is_add,
            NULL AS add_proj_name,
            s.model,
            NULL AS add_crm_no
        FROM
            filtered_sn AS s
            LEFT JOIN filtered_mtdt AS m ON s.complete_sn = m.prd_seq_id_fk
           WHERE m.mtrl_prod_id_fk not IN (SELECT wldm
            FROM vm_dcn_xsmx
            WHERE wlzms IN (
                '原材料-面膜、贴片类', 
                '原材料-包装箱类', 
                '原材料-塑料袋类', 
                '原材料-保修卡、合格证、装箱单类', 
                '原材料-胶带类', 
                '原材料-标签类', 
                '原材料-EPE类', 
                '原材料-栈板类', 
                '原材料-螺丝类', 
                '虚拟件-生产工艺'
            ));"""
        cursor.execute(sql, (batch, batch,))
        records_batch = cursor.fetchall()
        records_batch = remove_duplicates_records(records_batch, [0, 1, 9, 10, 11, 17])
        sync_records = []
        for record in records_batch:
            vals = {
                'unique_id': generate_sequences()[0],
                'delivery_no': record[0],
                'complete_sn': record[1],
                'service_start_time': record[2],
                'service_end_time': record[3],
                'service_product_type': record[4],
                'customer_name': record[5],
                'proj_name': record[6],
                'crm_no': record[7],
                'material_supplier': record[8],
                'material_code': record[9],
                'material_desc': record[10],
                'bom_sn': record[11],
                'sale': record[12],
                'purchase_time': record[13],
                'province': record[14],
                'city': record[15],
                'delivery_address': record[16],
                'deliver_time': record[17],
                'material_num': record[18],
                'is_add': record[19],
                'add_proj_name': record[20],
                'model': record[21],
                'add_crm_no': record[22],
                'write_flag': '0',
                'del_flag': '0',
                'create_date': 'NOW()',
                'write_date': 'NOW()',
                'create_uid': 2,
                'write_uid': 2
            }
            sync_records.append(vals)
        insert_records_in_batches(connection, cursor, sync_records)


def insert_records_in_batches(connection, cursor, records_to_sync, batch_size=50000):
    if not records_to_sync:
        return

    # 剔除物料号的记录
    records_to_sync = [record for record in records_to_sync if record.get('material_code') != '302-000191' and record.get('material_code') != '302-000189'
                        and record.get('material_code') != '302-000190' and record.get('material_code') != '303-000869']

    if not records_to_sync:
        logging.info("没有符合条件的记录需要同步")
        return

    insert_sql = """
    INSERT INTO sn_service_bom_info (
        unique_id, delivery_no, complete_sn, service_start_time, service_end_time,
        service_product_type, customer_name, proj_name, crm_no,
        material_supplier, material_code, material_desc, bom_sn,
        sale, purchase_time, province, city,
        delivery_address, deliver_time, material_num, is_add,
        add_proj_name, model,add_crm_no,write_flag, del_flag,
        create_date, write_date, create_uid, write_uid
    )
    VALUES %s
    ON CONFLICT (delivery_no, material_code, complete_sn, material_desc, bom_sn, deliver_time)
    DO UPDATE SET
        service_start_time = EXCLUDED.service_start_time,
        service_end_time = EXCLUDED.service_end_time,
        service_product_type = EXCLUDED.service_product_type,
        customer_name = EXCLUDED.customer_name,
        proj_name = EXCLUDED.proj_name,
        crm_no = EXCLUDED.crm_no,
        material_supplier = EXCLUDED.material_supplier,
        material_num = EXCLUDED.material_num,
        is_add = EXCLUDED.is_add,
        add_proj_name = EXCLUDED.add_proj_name,
        model = EXCLUDED.model,
        add_crm_no = EXCLUDED.add_crm_no,
        write_date = NOW()  -- 更新时设置当前时间
    WHERE sn_service_bom_info.write_flag != '1'
    """

    # 开始事务
    cursor.execute("BEGIN")
    # 分批插入
    total_batches = (len(records_to_sync) + batch_size - 1) // batch_size  # 总批次数
    for i in range(total_batches):
        batch = records_to_sync[i * batch_size:(i + 1) * batch_size]
        logging.info(f'正在同步第 {i + 1}/{total_batches} 批次的BOM组件数据，共 {len(batch)} 条记录')
        execute_values(cursor, insert_sql, [tuple(record.values()) for record in batch])
        connection.commit()
    logging.info("所有批次同步完成")


def remove_duplicates_records(records, indexs=[]):
    """
    去重同步记录中，联合主键重复记录
    """
    if indexs is None:
        indexs = []
    new_records = list()
    remove_duplicates_keys = set()
    for record in records:
        key = ''
        for index in indexs:
            key += f'-{str(record[index])}'
        if key not in remove_duplicates_keys:
            remove_duplicates_keys.add(key)
            new_records.append(record)
    return new_records

def generate_sequences(num=1):
    ids = []
    for i in range(0, num):
        ids.append(str(uuid.uuid1()).replace('-', ''))
    return ids

if __name__ == '__main__':
    get_sn_data()