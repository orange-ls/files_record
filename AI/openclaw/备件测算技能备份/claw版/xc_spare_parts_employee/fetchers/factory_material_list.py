"""
工厂物料清单 fetcher
对应模型：factory.material.list
数据库表：factory_material_list

刷新逻辑来源：FactoryMaterialList.refresh_pn_data()
外部依赖：WMS K3 BA 数据库（MySQL）
"""
import logging

import pymysql
import psycopg2.extras

from ._base import (
    ProgressCallback, build_result, count_records,
    fetch_records, report, to_markdown_table, transaction,
)
from ._config import get_wms_k3_config

_logger = logging.getLogger(__name__)

TREE_FIELDS = [
    'sap_no', 'industry_standard_desc', 'material_desc',
    'product_category2', 'product_category3',
]

FIELD_LABELS = {
    'sap_no': '物料代码',
    'industry_standard_desc': '工业标准描述',
    'material_desc': '物料描述',
    'product_category2': '产品Ⅱ级分类',
    'product_category3': '产品Ⅲ级分类',
}

_K3_SQL = '''
SELECT ext_material_id, pn, material_name
FROM ba_cust_mater
LEFT JOIN ba_cust_mater_pn ON ba_cust_mater.material_id = ba_cust_mater_pn.material_id
LEFT JOIN ba_material ON ba_cust_mater.material_id = ba_material.material_id
GROUP BY ext_material_id, pn, material_name
'''


def refresh(conn, on_progress: ProgressCallback = None) -> dict:
    """从 WMS K3 BA 数据库同步工厂物料清单"""
    TOTAL_STEPS = 4
    try:
        # ── Step 1: 连接 K3 BA 数据库 ──
        report(on_progress, 1, TOTAL_STEPS, '连接 WMS K3 BA 数据库...')
        k3_cfg = get_wms_k3_config()
        k3_conn = pymysql.connect(
            host=k3_cfg['host'],
            port=k3_cfg['port'],
            db=k3_cfg['dbname'],
            user=k3_cfg['user'],
            password=k3_cfg['password'],
            charset='utf8mb4',
        )
        k3_cur = k3_conn.cursor(pymysql.cursors.DictCursor)

        # ── Step 2: 拉取数据 ──
        report(on_progress, 2, TOTAL_STEPS, '从 K3 BA 拉取工厂物料数据...')
        k3_cur.execute(_K3_SQL)
        rows = k3_cur.fetchall()
        k3_conn.close()
        report(on_progress, 2, TOTAL_STEPS, f'K3 BA 数据拉取完成，共 {len(rows)} 条')

        # ── Step 3: 规范化物料代码，去重 ──
        report(on_progress, 3, TOTAL_STEPS, '规范化物料代码，关联产品分类...')
        with conn.cursor() as cur:
            cur.execute('SELECT sap_no, product_category2, product_category3 FROM xc_plm_material WHERE product_category2 IS NOT NULL')
            plm_map = {r[0]: (r[1], r[2]) for r in cur.fetchall()}

        unique_keys = set()
        unique_records = []
        for row in rows:
            sap_no = row.get('ext_material_id', '')
            if len(sap_no) == 18:
                sap_no = str(sap_no).lstrip('0')
                sap_no = f'{sap_no[:-6]}-{sap_no[-6:]}'
            key = (sap_no, row.get('pn'), row.get('material_name'))
            if key in unique_keys:
                continue
            unique_keys.add(key)
            pro2, pro3 = plm_map.get(sap_no, ('', ''))
            unique_records.append((sap_no, row.get('pn', ''), row.get('material_name', ''), pro2, pro3))

        # ── Step 4: 写入数据库 ──
        report(on_progress, 4, TOTAL_STEPS, f'写入工厂物料清单，共 {len(unique_records)} 条...')
        with transaction(conn):
            cur = conn.cursor()
            cur.execute('DELETE FROM factory_material_list')
            if unique_records:
                psycopg2.extras.execute_values(cur, '''
                    INSERT INTO factory_material_list
                    (sap_no, industry_standard_desc, material_desc, product_category2, product_category3)
                    VALUES %s
                ''', unique_records)

        count = len(unique_records)
        report(on_progress, TOTAL_STEPS, TOTAL_STEPS, f'✅ 工厂物料清单刷新完成，共写入 {count} 条')
        return build_result(True, count)

    except Exception as e:
        _logger.error('[xc_spare_parts] 工厂物料清单刷新失败：%s', e, exc_info=True)
        return build_result(False, error=str(e))


def query(conn, limit: int = 20, offset: int = 0, filters: dict = None) -> dict:
    """查询工厂物料清单"""
    where_clauses = ['1=1']
    params = []

    if filters:
        allowed = {'sap_no', 'industry_standard_desc', 'material_desc',
                   'product_category2', 'product_category3'}
        for key, val in filters.items():
            if key in allowed and val:
                where_clauses.append(f'{key} ILIKE %s')
                params.append(f'%{val}%')

    where_sql = ' AND '.join(where_clauses)
    fields_sql = ', '.join(TREE_FIELDS)
    base_sql = f'SELECT {fields_sql} FROM factory_material_list WHERE {where_sql} ORDER BY sap_no'

    total = count_records(conn, f'SELECT 1 FROM factory_material_list WHERE {where_sql}', params)
    records = fetch_records(conn, base_sql, params, limit, offset)

    return {
        'total': total,
        'records': records,
        'fields': TREE_FIELDS,
        'field_labels': FIELD_LABELS,
        'markdown': to_markdown_table(records, TREE_FIELDS, FIELD_LABELS, total, limit, offset),
    }
