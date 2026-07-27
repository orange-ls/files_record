"""
BOM总表 fetcher
对应模型：bom.total.table
数据库表：bom_total_table

刷新逻辑来源：BomTotalTable.refresh_bom_total()
刷新依赖：purchase_order_inventory（手工导入，无需刷新）
刷新后触发：crm_table、reservoir_area_stock、other_reservoir_area_stock、kunpeng_daily
"""
import datetime
import logging

import psycopg2.extras

from ._base import (
    ProgressCallback, build_result, count_records,
    fetch_records, report, to_markdown_table, transaction,
)

_logger = logging.getLogger(__name__)

# tree 视图字段（按 bom_total_table_views.xml 顺序）
TREE_FIELDS = [
    'proj_name', 'server_desc', 'server_aging', 'delivery_location',
    'stock_location', 'material_mode', 'material_desc', 'sum_count',
    'spare_parts_type', 'information_sources', 'proj_number', 'sale',
    'remark', 'write_time', 'bundling_number', 'server_stare_time',
    'server_end_time', 'product_category3', 'spare_parts_category',
]

FIELD_LABELS = {
    'proj_name': '项目名',
    'server_desc': '服务描述',
    'server_aging': '服务时效',
    'delivery_location': '交付地点',
    'stock_location': '库存地点',
    'material_mode': '物料代码',
    'material_desc': '物料描述',
    'sum_count': '总数量',
    'spare_parts_type': '产品Ⅱ级分类',
    'information_sources': '信息来源',
    'proj_number': 'CRM立项编号',
    'sale': '销售员',
    'remark': '备注',
    'write_time': '更新日期',
    'bundling_number': '捆绑料号',
    'server_stare_time': '服务开始时间',
    'server_end_time': '服务结束时间',
    'product_category3': '产品Ⅲ级分类',
    'spare_parts_category': '备件大类',
}


def refresh(conn, on_progress: ProgressCallback = None) -> dict:
    """
    刷新 BOM总表。
    逻辑：
      1. 读取 purchase_order_inventory 作为数据源
      2. 递归展开 material_bom
      3. 应用 material_transformation 物料转换
      4. 过滤 non_electronic_materials 非电子物料
      5. 关联溯源系统获取服务时间、销售信息
      6. 清空旧数据，批量写入新数据
    """
    TOTAL_STEPS = 6
    try:
        with transaction(conn):
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

            # ── Step 1: 读取旧数据（用于 extend.warranty 比对）──
            report(on_progress, 1, TOTAL_STEPS, '读取旧 BOM 数据用于延保比对...')
            cur.execute('SELECT material_mode, proj_name, stock_location, server_aging, write_time, information_sources FROM bom_total_table')
            old_records = cur.fetchall()
            old_dict = {
                (r['material_mode'], r['proj_name'], r['stock_location'],
                 r['server_aging'], r['write_time']): r
                for r in old_records
            }

            # ── Step 2: 读取数据源 ──
            report(on_progress, 2, TOTAL_STEPS, '读取 PO单与存量、物料转换、溯源数据...')
            cur.execute('SELECT * FROM purchase_order_inventory')
            material_list = cur.fetchall()

            cur.execute('''
                SELECT proj_name, MAX(crm_no) AS crm_no, MAX(is_add) AS is_add, MAX(add_crm_no) AS add_crm_no
                FROM sn_service_bom_info WHERE proj_name IS NOT NULL GROUP BY proj_name
            ''')
            crm_datas = {r['proj_name']: r for r in cur.fetchall()}

            cur.execute('SELECT crm_no, MAX(complete_sale) AS complete_sale FROM sn_service_complete_info WHERE crm_no IS NOT NULL GROUP BY crm_no')
            sale_datas = {r['crm_no']: r for r in cur.fetchall()}

            cur.execute('SELECT crm_no, MAX(sale) AS complete_sale FROM sn_service_bom_info WHERE crm_no IS NOT NULL GROUP BY crm_no')
            bom_datas = {r['crm_no']: r for r in cur.fetchall()}

            cur.execute('SELECT material_code, name, product_category3, spare_parts_category FROM base_material')
            type_dict = {r['material_code']: (r['name'], r['product_category3'], r['spare_parts_category']) for r in cur.fetchall()}

            cur.execute('SELECT material_mode, bundling_number FROM bundling_part_number')
            bundling_dict = {r['material_mode']: r['bundling_number'] for r in cur.fetchall()}

            cur.execute('''
                SELECT DISTINCT proj_name, crm_no,
                    MIN(service_start_time) start_time,
                    MAX(maintenance_service_end_date) end_date
                FROM sn_service_complete_info
                WHERE crm_no IS NOT NULL AND crm_no != ''
                GROUP BY proj_name, crm_no
            ''')
            sn_rows = cur.fetchall()
            sn_proj_dict = {r['proj_name']: r for r in sn_rows}
            sn_crm_dict = {r['crm_no']: r for r in sn_rows}

            # ── Step 3: 递归展开 BOM ──
            report(on_progress, 3, TOTAL_STEPS, '递归展开物料 BOM...')
            material_modes = [r['material_mode'] for r in material_list]
            if material_modes:
                cur.execute('''
                    WITH RECURSIVE r AS (
                        SELECT material_code, assembly, bom_assembly, bom_quantity
                        FROM material_bom WHERE material_code = ANY(%s)
                        UNION ALL
                        SELECT M.material_code, M.assembly, M.bom_assembly,
                               M.bom_quantity * r.bom_quantity
                        FROM material_bom M, r WHERE M.material_code = r.assembly
                    )
                    SELECT assembly, material_code, bom_quantity, bom_assembly
                    FROM r WHERE assembly NOT IN (SELECT r.material_code FROM r)
                ''', (material_modes,))
                bom_data = cur.fetchall()
            else:
                bom_data = []

            bom_dict = {}
            for bom in bom_data:
                bom_dict.setdefault(bom['material_code'], []).append(bom)

            # ── Step 4: 构建结果列表 ──
            report(on_progress, 4, TOTAL_STEPS, '构建 BOM 展开结果，应用物料转换...')
            cur.execute('SELECT sap_69_no, sap_302_no, material_desc FROM material_transformation')
            ma_trans = {r['sap_69_no']: r for r in cur.fetchall()}

            cur.execute('SELECT material_mode FROM non_electronic_materials')
            non_set = {r['material_mode'] for r in cur.fetchall()}

            result_list = []
            for red in material_list:
                red = dict(red)
                # 补充 CRM 立项编号
                proj_result = crm_datas.get(red['proj_name'])
                if proj_result:
                    if proj_result['is_add'] in ('否', None):
                        red['proj_number'] = proj_result['crm_no'] or red['proj_number']
                    else:
                        red['proj_number'] = proj_result['add_crm_no'] or proj_result['crm_no']
                # 补充销售员
                sale_result = sale_datas.get(red['proj_number']) or bom_datas.get(red['proj_number'])
                red['sale'] = sale_result['complete_sale'] if sale_result else None

                # BOM 展开
                material_bom = bom_dict.get(red['material_mode'])
                if material_bom:
                    for bom in material_bom:
                        result_list.append({
                            'material_mode': bom['assembly'],
                            'material_desc': str(bom['bom_assembly'] or ''),
                            'sum': bom['bom_quantity'] * red['sum'],
                            'proj_name': str(red['proj_name'] or ''),
                            'delivery_location': str(red['delivery_location'] or ''),
                            'stock_location': str(red['stock_location'] or ''),
                            'information_sources': str(red['information_sources'] or ''),
                            'server_desc': str(red['server_desc'] or ''),
                            'server_aging': str(red['server_aging'] or ''),
                            'proj_number': str(red['proj_number'] or ''),
                            'sale': str(red['sale'] or ''),
                            'remark': str(red['remark'] or ''),
                            'write_time': red['write_date'],
                        })
                else:
                    red['write_time'] = red['write_date']
                    result_list.append(red)

            # 应用物料转换
            for item in result_list:
                record = ma_trans.get(item['material_mode'])
                if record:
                    item['material_mode'] = record['sap_302_no']
                    item['material_desc'] = record['material_desc']

            # 过滤非电子物料
            new_list = [r for r in result_list if r['material_mode'] not in non_set]

            # ── Step 5: 构造插入数据（含延保判断）──
            report(on_progress, 5, TOTAL_STEPS, f'准备写入 {len(new_list)} 条数据...')
            insert_rows = []
            extend_rows = []  # 延保数据批量收集
            today = datetime.date.today()
            for item in new_list:
                pro2, pro3, big_cat = type_dict.get(item['material_mode'], ('', '', ''))
                bundling_number = bundling_dict.get(item['material_mode'], item['material_mode'])

                name_start = sn_proj_dict.get(item.get('proj_name'), {}).get('start_time')
                name_end = sn_proj_dict.get(item.get('proj_name'), {}).get('end_date')
                crm_start = sn_crm_dict.get(item.get('proj_number'), {}).get('start_time')
                crm_end = sn_crm_dict.get(item.get('proj_number'), {}).get('end_date')
                server_start = name_start or crm_start
                server_end = name_end or crm_end

                if server_end:
                    info_source = '过保' if server_end < today else '存量表'
                elif not server_start and not server_end:
                    info_source = item.get('information_sources', '')
                else:
                    info_source = item.get('information_sources', '')

                # 延保判断：旧值是过保 → 新值是存量表，收集到批量列表
                key = (item['material_mode'], item.get('proj_name'), item.get('stock_location'),
                       item.get('server_aging'), item.get('write_time'))
                old = old_dict.get(key)
                if old and old.get('information_sources') == '过保' and info_source == '存量表':
                    extend_rows.append((
                        old['material_mode'], item.get('material_desc'), item.get('sum'),
                        old['proj_name'], item.get('delivery_location'), old['stock_location'],
                        old['information_sources'], item.get('server_desc'), old['server_aging'],
                        item.get('proj_number'), item.get('sale'), item.get('remark'),
                        old['write_time'], pro2, pro3, bundling_number, server_start, server_end, big_cat,
                    ))

                insert_rows.append((
                    item['material_mode'], item.get('material_desc', ''),
                    item.get('sum', 0), item.get('proj_name', ''),
                    item.get('delivery_location', ''), item.get('stock_location', ''),
                    info_source, item.get('server_desc', ''), item.get('server_aging', ''),
                    item.get('proj_number', ''), item.get('sale', ''), item.get('remark', ''),
                    item.get('write_time'), pro2, pro3, bundling_number, server_start, server_end, big_cat,
                ))

            # 批量写入延保数据（避免循环内逐条 INSERT）
            if extend_rows:
                psycopg2.extras.execute_values(cur, '''
                    INSERT INTO extend_warranty_bom_table
                    (material_mode, material_desc, sum_count, proj_name, delivery_location,
                     stock_location, information_sources, server_desc, server_aging,
                     proj_number, sale, remark, write_time, spare_parts_type,
                     product_category3, bundling_number, server_stare_time, server_end_time,
                     spare_parts_category)
                    VALUES %s
                    ON CONFLICT DO NOTHING
                ''', extend_rows)

            # ── Step 6: 清空并批量写入 ──
            report(on_progress, 6, TOTAL_STEPS, '清空旧数据，批量写入...')
            cur.execute('DELETE FROM bom_total_table')
            psycopg2.extras.execute_values(cur, '''
                INSERT INTO bom_total_table
                (material_mode, material_desc, sum_count, proj_name, delivery_location,
                 stock_location, information_sources, server_desc, server_aging,
                 proj_number, sale, remark, write_time, spare_parts_type,
                 product_category3, bundling_number, server_stare_time, server_end_time,
                 spare_parts_category)
                VALUES %s
                ON CONFLICT (material_mode, proj_name, stock_location, information_sources, server_aging, write_time)
                DO UPDATE SET sum_count = EXCLUDED.sum_count + bom_total_table.sum_count
            ''', insert_rows)

            count = len(insert_rows)
            report(on_progress, TOTAL_STEPS, TOTAL_STEPS, f'✅ BOM总表刷新完成，共写入 {count} 条')
            return build_result(True, count)

    except Exception as e:
        _logger.error('[xc_spare_parts] BOM总表刷新失败：%s', e, exc_info=True)
        return build_result(False, error=str(e))


def query(conn, limit: int = 20, offset: int = 0, filters: dict = None) -> dict:
    """
    查询 BOM总表，返回 tree 视图字段。
    :param filters: 支持 material_mode, proj_name, information_sources, stock_location 等字段过滤
    """
    where_clauses = ['1=1']
    params = []

    if filters:
        allowed = {'material_mode', 'proj_name', 'information_sources', 'stock_location',
                   'server_aging', 'bundling_number', 'spare_parts_type', 'proj_number'}
        for key, val in filters.items():
            if key in allowed and val:
                where_clauses.append(f'{key} ILIKE %s')
                params.append(f'%{val}%')

    where_sql = ' AND '.join(where_clauses)
    base_sql = f'''
        SELECT {", ".join(TREE_FIELDS)}
        FROM bom_total_table
        WHERE {where_sql}
        ORDER BY write_time DESC, proj_name
    '''

    total = count_records(conn, f'SELECT 1 FROM bom_total_table WHERE {where_sql}', params)
    records = fetch_records(conn, base_sql, params, limit, offset)

    return {
        'total': total,
        'records': records,
        'fields': TREE_FIELDS,
        'field_labels': FIELD_LABELS,
        'markdown': to_markdown_table(records, TREE_FIELDS, FIELD_LABELS, total, limit, offset),
    }
