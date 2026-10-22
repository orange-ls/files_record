"""
替代料备料总表 fetcher
对应模型：alternative.prepare.materials（虚拟模型，无实体表）

替代料备料总表数据由 SQL 实时计算，不存储在数据库中。
只支持查询，不支持独立刷新。
"""
import logging

import psycopg2.extras

from ._base import to_markdown_table
from ._constants import ALERT_MAP
from ._sql_builders import build_alternative_sql

_logger = logging.getLogger(__name__)

TREE_FIELDS = [
    'bundling_number', 'name', 'total_usage', 'theo_non_rate', 'city',
    'sales', 'reserve_quantity', 'stock_quantity', 'gap_quantity',
    'wuhan_stock_quantity', 'stock_alert_status', 'sum_each_gap',
    'final_gap', 'xc02_quantity', 'xc16_quantity', 'xc17_quantity',
    'purchase_in_transit', 'dump_in_transit',
    'rma_in_transit', 'product_category3', 'spare_parts_category',
]

FIELD_LABELS = {
    'bundling_number': '捆绑料号',
    'name': '产品Ⅱ级分类',
    'total_usage': '总使用量',
    'theo_non_rate': '理论不良率',
    'city': '城市',
    'sales': '销量',
    'reserve_quantity': '备货量',
    'stock_quantity': '库存量',
    'gap_quantity': '缺口',
    'wuhan_stock_quantity': '武汉库存量',
    'stock_alert_status': '库存预警',
    'sum_each_gap': '各库区总缺口',
    'final_gap': '最终缺口',
    'xc02_quantity': 'XC02库存',
    'xc16_quantity': 'XC16库存',
    'xc17_quantity': 'XC17库存',
    'purchase_in_transit': '采购在途',
    'dump_in_transit': '转储在途',
    'rma_in_transit': 'RMA在途',
    'product_category3': '产品Ⅲ级分类',
    'spare_parts_category': '备件分类',
}


def query(conn, limit: int = 20, offset: int = 0, filters: dict = None,
          information_sources: str = None) -> dict:
    """
    查询替代料备料总表（虚拟模型，实时 SQL 计算）。
    :param information_sources: 信息来源过滤
    :param filters: 支持 bundling_number, name, city 等字段过滤
    """
    base_sql = build_alternative_sql(information_sources)

    where_clauses = ['1=1']
    params = []

    # 存量表模式：在外层 WHERE 过滤 information_sources
    if information_sources:
        where_clauses.append(f"information_sources = %s")
        params.append(information_sources)

    if filters:
        allowed = {'bundling_number', 'name', 'city', 'stock_alert_status', 'product_category3'}
        for key, val in filters.items():
            if key in allowed and val:
                where_clauses.append(f'{key} ILIKE %s')
                params.append(f'%{val}%')

    where_sql = ' AND '.join(where_clauses)

    with conn.cursor() as cur:
        cur.execute(f'SELECT COUNT(1) FROM ({base_sql}) T WHERE {where_sql}', params)
        total = cur.fetchone()[0]

    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            f'SELECT * FROM ({base_sql}) T WHERE {where_sql} ORDER BY bundling_number, city LIMIT %s OFFSET %s',
            params + [limit, offset]
        )
        records = [dict(r) for r in cur.fetchall()]

    # 库存预警转中文
    for rec in records:
        if rec.get('stock_alert_status'):
            rec['stock_alert_status'] = ALERT_MAP.get(rec['stock_alert_status'], rec['stock_alert_status'])

    # PO与存量模式下 SQL 不含 information_sources 列，补充空值以保持字段一致
    if not information_sources:
        for rec in records:
            rec.setdefault('information_sources', '')

    return {
        'total': total,
        'records': records,
        'fields': TREE_FIELDS,
        'field_labels': FIELD_LABELS,
        'markdown': to_markdown_table(records, TREE_FIELDS, FIELD_LABELS, total, limit, offset),
    }
