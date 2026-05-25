"""
欠料调拨总表 fetcher
对应模型：material.shortage
数据库表：material_shortage

刷新逻辑来源：MaterialShortage.sync_data()
前置依赖：prepare_materials / alternative_prepare_materials（虚拟计算）
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
    'material_code', 'bundling_number', 'material_description', 'spare_parts_category',
    'name', 'shortage_city', 'shortage_qty', 'transfer_city', 'transfer_city_stock',
    'service_lead_time', 'sales_qty', 'wuhan_main_stock', 'region_l1_stock',
    'region_first_level_stock', 'planner_remark', 'product_category3', 'import_flag',
]

FIELD_LABELS = {
    'material_code': '物料代码',
    'bundling_number': '捆绑料号',
    'material_description': '物料描述',
    'spare_parts_category': '备件大类',
    'name': '产品Ⅱ级分类',
    'shortage_city': '欠料城市',
    'shortage_qty': '欠料数量',
    'transfer_city': '调拨城市',
    'transfer_city_stock': '调拨城市库存',
    'service_lead_time': '服务时效',
    'sales_qty': '销售数量',
    'wuhan_main_stock': '武汉总库库存',
    'region_l1_stock': '区域L1库',
    'region_first_level_stock': '区域一级库库存',
    'planner_remark': '计划员备注',
    'product_category3': '产品Ⅲ级分类',
    'import_flag': '导入标记',
}


def refresh(conn, on_progress: ProgressCallback = None) -> dict:
    """
    刷新欠料调拨总表。
    逻辑：
      1. 保留手工导入数据（import_flag='是'）和计划员备注
      2. 删除非导入数据
      3. 从备料总表/替代料备料总表中筛选 sales>0 且 stock_quantity=0 的物料
      4. 计算调拨城市、区域一级库等字段
      5. 写入数据库
    """
    TOTAL_STEPS = 5
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # ── Step 1: 保留备注 ──
            report(on_progress, 1, TOTAL_STEPS, '保留计划员备注...')
            cur.execute('''
                SELECT material_code, shortage_city, information_sources, planner_remark
                FROM material_shortage
                WHERE planner_remark IS NOT NULL AND planner_remark != ''
            ''')
            remark_datas = {
                (r['material_code'], r['shortage_city'], r['information_sources']): r['planner_remark']
                for r in cur.fetchall()
            }

            # ── Step 2: 获取 WMS 库房分配数据 ──
            report(on_progress, 2, TOTAL_STEPS, '读取 WMS 库房分配数据...')
            cur.execute('SELECT address, alternative_store, regional_first_store FROM wms_storeroom_table GROUP BY address, alternative_store, regional_first_store')
            wms_rows = cur.fetchall()
            wms_alt = {r['address']: r['alternative_store'] for r in wms_rows}
            wms_regional = {r['address']: r['regional_first_store'] for r in wms_rows}

            # ── Step 3: 获取备料数据 ──
            report(on_progress, 3, TOTAL_STEPS, '计算备料总表和替代料备料总表...')

            # 获取捆绑料号对应的物料描述（用于替代料描述选择）
            cur.execute('SELECT bundling_number, material_mode AS material_code, material_desc FROM bundling_part_number GROUP BY bundling_number, material_mode, material_desc')
            bundling_desc = {}
            for r in cur.fetchall():
                bundling_desc.setdefault(r['bundling_number'], []).append(r)

            prepare_sql = build_prepare_sql(information_sources='')
            cur.execute(prepare_sql)
            prepare_records = [r for r in cur.fetchall()
                               if r.get('sales', 0) > 0 and r.get('stock_quantity', 0) == 0
                               and r.get('material_code') == r.get('bundling_number')]

            alt_sql = build_alternative_sql(information_sources='')
            cur.execute(alt_sql)
            alt_records = [r for r in cur.fetchall()
                           if r.get('sales', 0) > 0 and r.get('stock_quantity', 0) == 0]

            # ── Step 4: 构建插入数据 ──
            report(on_progress, 4, TOTAL_STEPS, f'构建欠料数据，共 {len(prepare_records) + len(alt_records)} 条...')

            # 获取各库区库存（用于计算调拨城市库存）
            cur.execute('SELECT sap_no, city, num FROM reservoir_area_stock')
            reservoir_sap = {}
            for r in cur.fetchall():
                reservoir_sap.setdefault(r['sap_no'], []).append(r)

            cur.execute('SELECT bundling_number, city, num FROM reservoir_area_stock ras LEFT JOIN bundling_part_number bn ON ras.sap_no = bn.material_mode')
            reservoir_bind = {}
            for r in cur.fetchall():
                reservoir_bind.setdefault(r['bundling_number'], []).append(r)

            # 获取服务时效
            cur.execute('''
                SELECT string_agg(DISTINCT server_aging, ',') AS server_aging,
                       CASE stock_location WHEN '武汉' THEN '武汉项目' ELSE stock_location END AS stock_location,
                       material_code
                FROM summary_kanban GROUP BY stock_location, material_code
            ''')
            service_sap = {(r['material_code'], r['stock_location']): r['server_aging'] for r in cur.fetchall()}

            cur.execute('''
                SELECT string_agg(DISTINCT server_aging, ',') AS server_aging, stock_location, bundling_number
                FROM summary_kanban GROUP BY stock_location, bundling_number
            ''')
            service_bind = {(r['bundling_number'], r['stock_location']): r['server_aging'] for r in cur.fetchall()}

            cur.execute('SELECT SUM(sum_count) AS sum_count, bundling_number, stock_location FROM summary_kanban GROUP BY stock_location, bundling_number')
            count_datas = {(r['stock_location'], r['bundling_number']): r['sum_count'] for r in cur.fetchall()}

            insert_rows = []
            for rec in prepare_records:
                rec = dict(rec)
                city = rec.get('city', '')
                transfer_city = wms_alt.get(city, '')
                region_l1 = wms_regional.get(city, '')
                transfer_stock = sum(r.get(transfer_city, 0) for r in reservoir_sap.get(rec['material_code'], []))
                wuhan_stock = sum(r.get('武汉', 0) for r in reservoir_sap.get(rec['material_code'], []))
                region_stock = sum(r.get(region_l1, 0) for r in reservoir_sap.get(rec['material_code'], []))
                service_str = service_sap.get((rec['material_code'], city), '')
                service_lead = _get_service_level(service_str)
                sales_qty = count_datas.get((city, rec.get('bundling_number')), 0)
                key = (rec['material_code'], city, '存量表')
                insert_rows.append((
                    rec['material_code'], rec.get('bundling_number'), rec.get('material_desc'),
                    rec.get('spare_parts_category'), rec.get('name'), city,
                    rec.get('gap_quantity'), transfer_city, transfer_stock,
                    service_lead, sales_qty, wuhan_stock, region_l1, region_stock,
                    remark_datas.get(key, ''), '存量表', rec.get('product_category3'),
                ))

            for rec in alt_records:
                rec = dict(rec)
                city = rec.get('city', '')
                bundling = rec.get('bundling_number', '')
                transfer_city = wms_alt.get(city, '')
                region_l1 = wms_regional.get(city, '')
                transfer_stock = sum(r.get(transfer_city, 0) for r in reservoir_bind.get(bundling, []))
                wuhan_stock = sum(r.get('武汉', 0) for r in reservoir_bind.get(bundling, []))
                region_stock = sum(r.get(region_l1, 0) for r in reservoir_bind.get(bundling, []))
                service_str = service_bind.get((bundling, city), '')
                service_lead = _get_service_level(service_str)
                sales_qty = count_datas.get((city, bundling), 0)

                # 替代料物料描述选择逻辑（参考原始 sync_data 中的 77-/88-/99- 前缀规则）
                desc_list = bundling_desc.get(bundling, [])
                selected_desc = None
                if bundling.startswith('77-'):
                    # 任一描述即可
                    selected_desc = desc_list[0]['material_desc'] if desc_list else None
                elif bundling.startswith('88-'):
                    # 优先选 302- 开头且不含"机箱"
                    preferred = [d for d in desc_list if d['material_code'].startswith('302-') and '机箱' not in (d['material_desc'] or '')]
                    selected_desc = preferred[0]['material_desc'] if preferred else (desc_list[0]['material_desc'] if desc_list else None)
                elif bundling.startswith('99-'):
                    # 优先选 302- 开头
                    preferred = [d for d in desc_list if d['material_code'].startswith('302-')]
                    selected_desc = preferred[0]['material_desc'] if preferred else (desc_list[0]['material_desc'] if desc_list else None)
                else:
                    selected_desc = desc_list[0]['material_desc'] if desc_list else None

                key = (bundling, city, '存量表')
                insert_rows.append((
                    bundling, bundling, selected_desc,
                    rec.get('spare_parts_category'), rec.get('name'), city,
                    rec.get('gap_quantity'), transfer_city, transfer_stock,
                    service_lead, sales_qty, wuhan_stock, region_l1, region_stock,
                    remark_datas.get(key, ''), '存量表', rec.get('product_category3'),
                ))

        # ── Step 5: 写入数据库 ──
        report(on_progress, 5, TOTAL_STEPS, f'写入欠料调拨总表，共 {len(insert_rows)} 条...')
        with transaction(conn):
            cur = conn.cursor()
            cur.execute("DELETE FROM material_shortage WHERE import_flag != '是' OR import_flag IS NULL")
            if insert_rows:
                psycopg2.extras.execute_values(cur, '''
                    INSERT INTO material_shortage (
                        material_code, bundling_number, material_description, spare_parts_category,
                        name, shortage_city, shortage_qty, transfer_city, transfer_city_stock,
                        service_lead_time, sales_qty, wuhan_main_stock, region_l1_stock,
                        region_first_level_stock, planner_remark, information_sources, product_category3
                    ) VALUES %s
                    ON CONFLICT (material_code, shortage_city, information_sources)
                    DO UPDATE SET
                        bundling_number = EXCLUDED.bundling_number,
                        material_description = EXCLUDED.material_description,
                        shortage_qty = EXCLUDED.shortage_qty,
                        transfer_city = EXCLUDED.transfer_city,
                        transfer_city_stock = EXCLUDED.transfer_city_stock,
                        service_lead_time = EXCLUDED.service_lead_time,
                        sales_qty = EXCLUDED.sales_qty,
                        wuhan_main_stock = EXCLUDED.wuhan_main_stock,
                        region_l1_stock = EXCLUDED.region_l1_stock,
                        region_first_level_stock = EXCLUDED.region_first_level_stock,
                        planner_remark = EXCLUDED.planner_remark
                ''', insert_rows)

        count = len(insert_rows)
        report(on_progress, TOTAL_STEPS, TOTAL_STEPS, f'✅ 欠料调拨总表刷新完成，共写入 {count} 条')
        return build_result(True, count)

    except Exception as e:
        _logger.error('[xc_spare_parts] 欠料调拨总表刷新失败：%s', e, exc_info=True)
        return build_result(False, error=str(e))


def query(conn, limit: int = 20, offset: int = 0, filters: dict = None) -> dict:
    """查询欠料调拨总表"""
    where_clauses = ['1=1']
    params = []

    if filters:
        allowed = {'material_code', 'bundling_number', 'shortage_city', 'service_lead_time',
                   'name', 'spare_parts_category', 'information_sources'}
        for key, val in filters.items():
            if key in allowed and val:
                where_clauses.append(f'{key} ILIKE %s')
                params.append(f'%{val}%')

    where_sql = ' AND '.join(where_clauses)
    fields_sql = ', '.join(TREE_FIELDS)
    base_sql = f'SELECT {fields_sql} FROM material_shortage WHERE {where_sql} ORDER BY service_lead_time, shortage_city'

    total = count_records(conn, f'SELECT 1 FROM material_shortage WHERE {where_sql}', params)
    records = fetch_records(conn, base_sql, params, limit, offset)

    return {
        'total': total,
        'records': records,
        'fields': TREE_FIELDS,
        'field_labels': FIELD_LABELS,
        'markdown': to_markdown_table(records, TREE_FIELDS, FIELD_LABELS, total, limit, offset),
    }


def _get_service_level(config_desc: str) -> str:
    """服务时效判断，委托给 _constants 中的统一实现"""
    from ._constants import get_service_level
    return get_service_level(config_desc, default='')
