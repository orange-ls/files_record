"""
鲲鹏日报 fetcher
对应模型：kunpeng.daily
数据库表：kunpeng_daily

刷新逻辑来源：KunpengDaily.get_bi_view_data()
外部依赖：Oracle BI 视图 DCDWS.VW_DCN_DIKCMX
"""
import logging

import cx_Oracle
import psycopg2.extras

from ._base import (
    ProgressCallback, build_result, count_records,
    fetch_records, report, to_markdown_table, transaction,
)
from ._config import get_oracle_conn_str

_logger = logging.getLogger(__name__)

TREE_FIELDS = [
    'service_scope_code', 'service_category', 'factory_code', 'factory_category',
    'bundling_number', 'material_code', 'material_desc', 'batch_code',
    'material_category_name', 'material_group_name', 'stock_category',
    'stock_address', 'stock_name', 'stock_quantity',
]

FIELD_LABELS = {
    'service_scope_code': '业务范围代码',
    'service_category': '业务类型',
    'factory_code': '工厂代码',
    'factory_category': '工厂类型',
    'bundling_number': '捆绑料号',
    'material_code': '物料代码',
    'material_desc': '中文物料名称',
    'batch_code': '批次代码',
    'material_category_name': '物料类型名称',
    'material_group_name': '物料组名称',
    'stock_category': '库存地分类',
    'stock_address': '库存地代码',
    'stock_name': '库存地名称',
    'stock_quantity': '实际库存数量',
}

_ORACLE_SQL = '''
SELECT
    事业部名称, 业务范围代码, 业务类型, 工厂代码, 工厂类型, 是否鲲泰工厂, 是否可售,
    库存地分类, 库存地代码, 库存地名称,
    虚拟物料号,
    cast(cast(substr(物料代码,1,12) as NUMBER) as varchar2(3)) || '-' || substr(物料代码,-6) 物料代码,
    物料名称, 批次代码, 物料类型名称, 物料组名称,
    产品线, 产品分类, 产品系列, 主板类型, 是否信创主板, 主板核数,
    移动平均单价, 实际库存数量, 实存金额, DOS, 可售库存数量
FROM DCDWS.VW_DCN_DIKCMX
'''


def refresh(conn, on_progress: ProgressCallback = None) -> dict:
    """从 Oracle BI 视图同步鲲鹏日报数据"""
    TOTAL_STEPS = 4
    try:
        # ── Step 1: 连接 Oracle ──
        report(on_progress, 1, TOTAL_STEPS, '连接 Oracle BI 视图...')
        conn_str = get_oracle_conn_str()
        oracle_conn = cx_Oracle.Connection(conn_str)
        oracle_cur = oracle_conn.cursor()

        # ── Step 2: 拉取数据 ──
        report(on_progress, 2, TOTAL_STEPS, '从 Oracle 拉取鲲鹏日报数据...')
        oracle_cur.execute(_ORACLE_SQL)
        rows = oracle_cur.fetchall()
        cols = [d[0] for d in oracle_cur.description]
        oracle_conn.close()
        report(on_progress, 2, TOTAL_STEPS, f'Oracle 数据拉取完成，共 {len(rows)} 条')

        # ── Step 3: 关联捆绑料号 ──
        report(on_progress, 3, TOTAL_STEPS, '关联捆绑料号，写入数据库...')
        with transaction(conn):
            cur = conn.cursor()
            cur.execute('DELETE FROM kunpeng_daily')

            # 构建 VALUES 子句，关联 bundling_part_number
            # 构建数据列表，空值直接用 None（psycopg2 自动转为 SQL NULL）
            _ORACLE_FIELDS = [
                '事业部名称', '业务范围代码', '业务类型', '工厂代码', '工厂类型',
                '是否鲲泰工厂', '是否可售', '库存地分类', '库存地代码', '库存地名称',
                '虚拟物料号', '物料代码', '物料名称', '批次代码', '物料类型名称',
                '物料组名称', '产品线', '产品分类', '产品系列', '主板类型',
                '是否信创主板', '主板核数', '移动平均单价', '实际库存数量',
                '实存金额', 'DOS', '可售库存数量',
            ]
            data = []
            for row in rows:
                result = dict(zip(cols, row))
                data.append(tuple(result.get(f) for f in _ORACLE_FIELDS))

            # 先 SELECT 关联捆绑料号，再 INSERT
            select_sql = '''
                SELECT COALESCE(b.bundling_number, T.material_code) AS bundling_number, T.*
                FROM (VALUES %s) AS T (
                    division_name, service_scope_code, service_category, factory_code,
                    factory_category, is_kt_factory, is_sale, stock_category, stock_address, stock_name,
                    invented_material_code, material_code, material_desc, batch_code, material_category_name,
                    material_group_name, prod_line, prod_category, prod_range, board_category, is_xc_board,
                    board_core, avg_price, stock_quantity, real_amount, dos, sale_stock_quantity
                )
                LEFT JOIN bundling_part_number b ON T.material_code = b.material_mode
            '''
            psycopg2.extras.execute_values(cur, select_sql, data, fetch=True)
            bund_recs = cur.fetchall()

            insert_sql = '''
                INSERT INTO kunpeng_daily (
                    bundling_number, division_name, service_scope_code, service_category, factory_code,
                    factory_category, is_kt_factory, is_sale, stock_category, stock_address, stock_name,
                    invented_material_code, material_code, material_desc, batch_code, material_category_name,
                    material_group_name, prod_line, prod_category, prod_range, board_category, is_xc_board,
                    board_core, avg_price, stock_quantity, real_amount, dos, sale_stock_quantity
                ) VALUES %s
            '''
            psycopg2.extras.execute_values(cur, insert_sql, bund_recs)

        count = len(rows)
        report(on_progress, TOTAL_STEPS, TOTAL_STEPS, f'✅ 鲲鹏日报刷新完成，共写入 {count} 条')
        return build_result(True, count)

    except Exception as e:
        _logger.error('[xc_spare_parts] 鲲鹏日报刷新失败：%s', e, exc_info=True)
        return build_result(False, error=str(e))


def query(conn, limit: int = 20, offset: int = 0, filters: dict = None) -> dict:
    """查询鲲鹏日报，默认过滤借用在途库"""
    where_clauses = ["stock_category != '借用在途库'"]
    params = []

    if filters:
        allowed = {'material_code', 'bundling_number', 'factory_code', 'stock_address',
                   'service_category', 'stock_category', 'material_desc'}
        for key, val in filters.items():
            if key in allowed and val:
                where_clauses.append(f'{key} ILIKE %s')
                params.append(f'%{val}%')

    where_sql = ' AND '.join(where_clauses)
    fields_sql = ', '.join(TREE_FIELDS)
    base_sql = f'SELECT {fields_sql} FROM kunpeng_daily WHERE {where_sql} ORDER BY material_code'

    total = count_records(conn, f'SELECT 1 FROM kunpeng_daily WHERE {where_sql}', params)
    records = fetch_records(conn, base_sql, params, limit, offset)

    return {
        'total': total,
        'records': records,
        'fields': TREE_FIELDS,
        'field_labels': FIELD_LABELS,
        'markdown': to_markdown_table(records, TREE_FIELDS, FIELD_LABELS, total, limit, offset),
    }
