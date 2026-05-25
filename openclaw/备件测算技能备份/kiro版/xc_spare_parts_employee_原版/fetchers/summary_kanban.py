"""
汇总看板 fetcher
对应模型：summary.kanban
数据库表：summary_kanban

刷新逻辑来源：SummaryKanban.sync_summary_kanban_data()
前置依赖：bom_total_table（需先刷新）
"""
import logging

import psycopg2.extras

from ._base import (
    ProgressCallback, build_result, count_records,
    fetch_records, report, to_markdown_table, transaction,
)
from ._sql_builders import build_prepare_sql, build_alternative_sql

_logger = logging.getLogger(__name__)

TREE_FIELDS = [
    'proj_name', 'server_aging', 'delivery_location', 'stock_location',
    'material_code', 'bundling_number', 'material_desc', 'spare_parts_category',
    'material_name', 'product_category3', 'sum_count', 'reserve_quantity',
    'stock_total', 'gap_quantity', 'wuhan_stock_quantity', 'gap_total',
    'purchase_in_transit', 'dump_in_transit', 'rma_in_transit',
    'xc_02', 'xc_16', 'xc_17', 'has_media_retention', 'information_sources',
    'proj_number', 'server_stare_time', 'server_end_time', 'sale', 'remark',
]

FIELD_LABELS = {
    'proj_name': '项目名',
    'server_aging': '服务时效',
    'delivery_location': '交付地点',
    'stock_location': '库存地点',
    'material_code': '物料代码',
    'bundling_number': '捆绑料号',
    'material_desc': '物料描述',
    'spare_parts_category': '备件大类',
    'material_name': '产品Ⅱ级分类',
    'product_category3': '产品Ⅲ级分类',
    'sum_count': '总数量',
    'reserve_quantity': '备货量',
    'stock_total': '库存量',
    'gap_quantity': '缺口',
    'wuhan_stock_quantity': '武汉库存量',
    'gap_total': '最终缺口',
    'purchase_in_transit': '采购在途',
    'dump_in_transit': '转储在途',
    'rma_in_transit': 'RMA在途',
    'xc_02': 'XC02',
    'xc_16': 'XC16',
    'xc_17': 'XC17',
    'has_media_retention': '是否介质保留',
    'information_sources': '信息来源',
    'proj_number': 'CRM立项编号',
    'server_stare_time': '服务开始时间',
    'server_end_time': '服务结束时间',
    'sale': '销售员',
    'remark': '备注',
}


def refresh(conn, on_progress: ProgressCallback = None) -> dict:
    """刷新汇总看板（依赖 bom_total_table 已刷新）"""
    TOTAL_STEPS = 4
    try:
        # ── Step 1: 从 BOM总表聚合基础数据 ──
        report(on_progress, 1, TOTAL_STEPS, '从 BOM总表聚合汇总看板基础数据...')
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute('''
                SELECT
                    proj_name, server_aging, delivery_location, stock_location,
                    material_mode AS material_code, bundling_number, information_sources,
                    SUM(sum_count) AS sum_count,
                    MAX(base_material.material_desc) AS material_desc,
                    MAX(base_material.spare_parts_category) AS spare_parts_category,
                    MAX(base_material.name) AS material_name,
                    MAX(base_material.product_category3) AS product_category3,
                    MAX(proj_number) AS proj_number,
                    CASE WHEN POSITION('介质保留' IN MAX(server_desc)) > 0 THEN '是' ELSE '否' END AS has_media_retention,
                    MAX(server_stare_time) AS server_stare_time,
                    MAX(server_end_time) AS server_end_time,
                    MAX(sale) AS sale
                FROM bom_total_table
                LEFT JOIN base_material ON bom_total_table.material_mode = base_material.material_code
                GROUP BY proj_name, server_aging, delivery_location, stock_location,
                         material_mode, bundling_number, information_sources
            ''')
            records = cur.fetchall()

        report(on_progress, 1, TOTAL_STEPS, f'BOM总表聚合完成，共 {len(records)} 条')

        # ── Step 2: 获取备料计算数据 ──
        report(on_progress, 2, TOTAL_STEPS, '计算备料数据（备货量、库存量、缺口等）...')
        prepare_sql = build_prepare_sql()
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(prepare_sql)
            prepare_rows = cur.fetchall()

        prepare_dict = {(r['material_code'], r['city']): r for r in prepare_rows}

        alternative_sql = build_alternative_sql()
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(alternative_sql)
            alt_rows = cur.fetchall()

        alt_dict = {(r['bundling_number'], r['city']): r for r in alt_rows}

        # ── Step 3: 合并备料数据 ──
        report(on_progress, 3, TOTAL_STEPS, '合并备料数据，准备写入...')
        insert_rows = []
        for rec in records:
            rec = dict(rec)
            stock_location = '武汉项目' if rec['stock_location'] == '武汉' else rec['stock_location']

            # 优先用单一物料维度，否则用捆绑料号维度
            if rec['material_code'] == rec.get('bundling_number'):
                prepare = prepare_dict.get((rec['material_code'], stock_location), {})
            else:
                prepare = alt_dict.get((rec.get('bundling_number'), stock_location), {})

            insert_rows.append((
                rec['proj_name'], rec['server_aging'], rec['delivery_location'],
                rec['stock_location'], rec['material_code'], rec.get('bundling_number'),
                rec['information_sources'], rec['sum_count'], rec['material_desc'],
                rec['spare_parts_category'], rec['material_name'], rec['product_category3'],
                rec['proj_number'], rec['has_media_retention'],
                rec['server_stare_time'], rec['server_end_time'], rec['sale'],
                prepare.get('reserve_quantity'), prepare.get('stock_quantity'),
                prepare.get('gap_quantity'), prepare.get('wuhan_stock_quantity'),
                prepare.get('final_gap'),
                prepare.get('xc02_quantity'), prepare.get('xc16_quantity'), prepare.get('xc17_quantity'),
                prepare.get('purchase_in_transit'), prepare.get('dump_in_transit'),
                prepare.get('rma_in_transit'),
            ))

        # ── Step 4: 清空并写入 ──
        report(on_progress, 4, TOTAL_STEPS, f'写入汇总看板，共 {len(insert_rows)} 条...')
        with transaction(conn):
            cur = conn.cursor()
            cur.execute('TRUNCATE summary_kanban')
            if insert_rows:
                psycopg2.extras.execute_values(cur, '''
                    INSERT INTO summary_kanban (
                        proj_name, server_aging, delivery_location, stock_location,
                        material_code, bundling_number, information_sources, sum_count,
                        material_desc, spare_parts_category, material_name, product_category3,
                        proj_number, has_media_retention, server_stare_time, server_end_time, sale,
                        reserve_quantity, stock_total, gap_quantity, wuhan_stock_quantity, gap_total,
                        xc_02, xc_16, xc_17, purchase_in_transit, dump_in_transit, rma_in_transit
                    ) VALUES %s
                ''', insert_rows)

        count = len(insert_rows)
        report(on_progress, TOTAL_STEPS, TOTAL_STEPS, f'✅ 汇总看板刷新完成，共写入 {count} 条')
        return build_result(True, count)

    except Exception as e:
        _logger.error('[xc_spare_parts] 汇总看板刷新失败：%s', e, exc_info=True)
        return build_result(False, error=str(e))


def query(conn, limit: int = 20, offset: int = 0, filters: dict = None) -> dict:
    """查询汇总看板"""
    where_clauses = ['1=1']
    params = []

    if filters:
        allowed = {'proj_name', 'material_code', 'bundling_number', 'stock_location',
                   'information_sources', 'server_aging', 'material_name', 'proj_number'}
        for key, val in filters.items():
            if key in allowed and val:
                where_clauses.append(f'{key} ILIKE %s')
                params.append(f'%{val}%')

    where_sql = ' AND '.join(where_clauses)
    fields_sql = ', '.join(TREE_FIELDS)
    base_sql = f'SELECT {fields_sql} FROM summary_kanban WHERE {where_sql} ORDER BY proj_name DESC'

    total = count_records(conn, f'SELECT 1 FROM summary_kanban WHERE {where_sql}', params)
    records = fetch_records(conn, base_sql, params, limit, offset)

    return {
        'total': total,
        'records': records,
        'fields': TREE_FIELDS,
        'field_labels': FIELD_LABELS,
        'markdown': to_markdown_table(records, TREE_FIELDS, FIELD_LABELS, total, limit, offset),
    }
