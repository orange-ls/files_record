"""
各库区库存 fetcher
对应模型：reservoir.area.stock
数据库表：reservoir_area_stock

刷新逻辑来源：ReservoirAreaStock.get_wms_data()
外部依赖：WMS 接口（get_stock）
刷新时同步写入：rma_transit
"""
import copy
import hashlib
import json
import logging
import time

import psycopg2.extras
import requests

from ._base import (
    ProgressCallback, build_result, count_records,
    fetch_records, report, to_markdown_table, transaction,
)
from ._config import get_wms_config

_logger = logging.getLogger(__name__)

# tree 视图基础字段（城市列动态生成，查询时聚合）
TREE_FIELDS_BASE = [
    'sap_no', 'bundling_number', 'material_desc', 'supplier_pn',
    'spare_parts_category', 'material_type', 'product_category3',
]

FIELD_LABELS = {
    'sap_no': '物料代码',
    'bundling_number': '捆绑料号',
    'material_desc': '物料描述',
    'supplier_pn': '供应商PN码',
    'spare_parts_category': '备件大类',
    'material_type': '产品Ⅱ级分类',
    'product_category3': '产品Ⅲ级分类',
}

# 库存地编码 → 城市名称映射（来自 reservoir_area_stock.py stock_params）
STOCK_PARAMS = [
    {'city': '贵阳', 'param': 'KCDBJ-GYBJC'},
    {'city': '长沙', 'param': 'KCDBJ-CSBJC'},
    {'city': '杭州', 'param': 'KCDBJ-HZBJC'},
    {'city': '佛山', 'param': 'KCDBJ-FSBJC'},
    {'city': '武汉', 'param': 'KCDBJ-WHBJC'},
    {'city': '武汉项目', 'param': 'KCDBJ-WHXMC'},
    {'city': '待定', 'param': 'KCDBJ-WHBJC'},
    {'city': '上海', 'param': 'KCDBJ-SHBJC'},
    {'city': '合肥', 'param': 'KCDBJ-HFBJC'},
    {'city': '肇庆', 'param': 'KCDBJ-ZQBJC'},
    {'city': '福州', 'param': 'KCDBJ-FZBJC'},
    {'city': '南宁', 'param': 'KCDBJ-NNBJC'},
    {'city': '北京', 'param': 'KCDBJ-BJBJC'},
    {'city': '西安', 'param': 'KCDBJ-XABJC'},
    {'city': '广州', 'param': 'KCDBJ-GZBJC'},
    {'city': '宁波', 'param': 'KCDBJ-NBBJC'},
    {'city': '汕头', 'param': 'KCDBJ-STBJC'},
    {'city': '成都', 'param': 'KCDBJ-CDBJC'},
    {'city': '昆明', 'param': 'KCDBJ-KMBJC'},
    {'city': '长春', 'param': 'KCDBJ-CCBJC'},
    {'city': '石家庄', 'param': 'KCDBJ-SJZBJC'},
    {'city': '济南', 'param': 'KCDBJ-JNBJC'},
    {'city': '太原', 'param': 'KCDBJ-TYBJC'},
    {'city': '呼和浩特', 'param': 'KCDBJ-HHHTBJC'},
    {'city': '沈阳', 'param': 'KCDBJ-SYBJC'},
    {'city': '哈尔滨', 'param': 'KCDBJ-HEBBJC'},
    {'city': '乌鲁木齐', 'param': 'KCDBJ-WLMQBJC'},
    {'city': '天津', 'param': 'KCDBJ-TJBJC'},
    {'city': '兰州', 'param': 'KCDBJ-LZBJC'},
    {'city': '银川', 'param': 'KCDBJ-YCBJC'},
    {'city': '大连', 'param': 'KCDBJ-DLBJC'},
    {'city': '西宁', 'param': 'KCDBJ-XNBJC'},
    {'city': '南京', 'param': 'KCDBJ-NJBJC'},
    {'city': '阿克苏', 'param': 'KCDBJ-AKSBJC'},
    {'city': '深圳', 'param': 'KCDBJ-SZBJC'},
    {'city': '东莞', 'param': 'KCDBJ-DGBJC'},
    {'city': '烟台', 'param': 'KCDBJ-YTBJC'},
    {'city': '海口', 'param': 'KCDBJ-HKBJC'},
    {'city': '重庆', 'param': 'KCDBJ-CQBJC'},
    {'city': '厦门', 'param': 'KCDBJ-XMBJC'},
    {'city': '郑州', 'param': 'KCDBJ-ZZBJC'},
    {'city': '龙岩', 'param': 'KCDBJ-LYBJC'},
    {'city': '青岛', 'param': 'KCDBJ-QDBJC'},
    {'city': '南昌', 'param': 'KCDBJ-NCBJC'},
    {'city': '廊坊', 'param': 'KCDBJ-LFBJC'},
]

# RMA 库存地编码
RMA_PARAMS = ['WHWXC-FCZT']

# 库存地编码 → 城市名 快速查找
_PARAM_TO_CITY = {p['param']: p['city'] for p in STOCK_PARAMS}


def _get_wms_stock(sap_nos: list) -> list:
    """
    调用 WMS 接口获取库存数据。
    复制自 ReservoirAreaStock.get_real_stock() 逻辑。
    返回：[{'sap_no': '302-xxx', 'stock_address': 'KCDBJ-WHBJC', 'quantity': 10}, ...]
    """
    cfg = get_wms_config()
    app_secret = cfg['app_secret']
    app_key = cfg['app_key']
    sub_app_key = cfg['sub_app_key']
    base_url = cfg['base_url']

    timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
    sign_str = (app_secret
                + 'app_key' + app_key
                + 'customerId' + sub_app_key
                + 'formatjson'
                + 'methodstorageapi'
                + 'sign_methodMD5'
                + 'timestamp' + timestamp)
    sign = hashlib.md5(sign_str.encode()).hexdigest().upper()

    # 构建请求体（每次最多 200 个物料）
    results = []
    batch_size = 200
    for i in range(0, len(sap_nos), batch_size):
        batch = sap_nos[i:i + batch_size]
        body = {
            'materialIds': batch,
            'warehouseId': '1200004260',
            'type': 2,
        }
        payload = {
            'app_key': app_key,
            'customerId': sub_app_key,
            'format': 'json',
            'method': 'storageapi',
            'sign_method': 'MD5',
            'timestamp': timestamp,
            'sign': sign,
            'body': json.dumps(body),
        }
        resp = requests.post(base_url, data=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        items = data.get('data', [])
        for item in items:
            ext_id = item.get('extmaterialId', '')
            leading_zeros = len(ext_id) - len(ext_id.lstrip('0'))
            if leading_zeros == 9:
                sap_no = ext_id[9:12] + '-' + ext_id[12:]
            elif leading_zeros == 10:
                sap_no = ext_id[10:12] + '-' + ext_id[12:]
            elif leading_zeros == 11:
                sap_no = ext_id[11:14] + '-' + ext_id[14:]
            else:
                sap_no = ext_id[9:12] + '-' + ext_id[12:]
            results.append({
                'sap_no': sap_no,
                'stock_address': item.get('stockId', ''),
                'quantity': item.get('avaliableQty', 0),
            })
    return results


def refresh(conn, on_progress: ProgressCallback = None) -> dict:
    """从 WMS 接口同步各库区库存，同时写入 rma_transit"""
    TOTAL_STEPS = 5
    try:
        # ── Step 1: 获取 BOM总表物料代码 ──
        report(on_progress, 1, TOTAL_STEPS, '读取 BOM总表物料代码...')
        with conn.cursor() as cur:
            cur.execute('SELECT material_mode FROM bom_total_table GROUP BY material_mode')
            rows = cur.fetchall()

        sap_nos = []
        for (material_mode,) in rows:
            if material_mode.startswith('69'):
                continue
            sap = '0' * (18 - len(material_mode.replace('-', ''))) + material_mode.replace('-', '')
            if len(sap) == 18:
                sap_nos.append(sap)

        # ── Step 2: 调用 WMS 接口 ──
        report(on_progress, 2, TOTAL_STEPS, f'调用 WMS 接口，共 {len(sap_nos)} 个物料...')
        stock_list = _get_wms_stock(sap_nos)
        report(on_progress, 2, TOTAL_STEPS, f'WMS 返回 {len(stock_list)} 条库存记录')

        # ── Step 3: 分类处理（各库区 vs RMA）──
        report(on_progress, 3, TOTAL_STEPS, '分类处理库存数据...')
        real_res = []   # 各库区库存
        rma_res = []    # RMA 在途
        rma_set = {}    # {sap_no: quantity}

        for r in stock_list:
            city = _PARAM_TO_CITY.get(r['stock_address'])
            if city:
                temp = copy.deepcopy(r)
                temp['stock_address'] = city
                real_res.append(temp)
            if r['stock_address'] in RMA_PARAMS:
                sap = r['sap_no']
                rma_set[sap] = rma_set.get(sap, 0) + r['quantity']
                rma_res.append(r)

        # ── Step 4: 关联 base_material，写入各库区库存 ──
        report(on_progress, 4, TOTAL_STEPS, f'写入各库区库存，共 {len(real_res)} 条...')
        with transaction(conn):
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

            # 获取 base_material 信息
            cur.execute('SELECT material_code, material_desc, supplier_pn, name, product_category3, spare_parts_category FROM base_material')
            base_dict = {r['material_code']: r for r in cur.fetchall()}

            # 获取捆绑料号
            cur.execute('SELECT material_mode, bundling_number FROM bundling_part_number')
            bundling_dict = {r['material_mode']: r['bundling_number'] for r in cur.fetchall()}

            cur.execute('DELETE FROM reservoir_area_stock')

            insert_data = []
            for r in real_res:
                base = base_dict.get(r['sap_no'], {})
                insert_data.append((
                    r['sap_no'],
                    r['stock_address'],
                    r['quantity'],
                    base.get('material_desc', ''),
                    base.get('supplier_pn', ''),
                    base.get('name', ''),
                    base.get('product_category3', ''),
                    base.get('spare_parts_category', ''),
                ))

            if insert_data:
                psycopg2.extras.execute_values(cur, '''
                    INSERT INTO reservoir_area_stock
                    (sap_no, city, num, material_desc, supplier_pn, material_type, product_category3, spare_parts_category)
                    VALUES %s
                ''', insert_data)

            # ── Step 5: 写入 rma_transit ──
            report(on_progress, 5, TOTAL_STEPS, f'写入 RMA在途，共 {len(rma_set)} 个物料...')
            rma_insert = []
            for sap_no, quantity in rma_set.items():
                if quantity == 0:
                    continue
                base = base_dict.get(sap_no, {})
                bundling_code = bundling_dict.get(sap_no, sap_no)
                rma_insert.append((
                    sap_no,
                    base.get('material_desc', ''),
                    base.get('supplier_pn', ''),
                    base.get('name', ''),
                    base.get('product_category3', ''),
                    quantity,
                    bundling_code,
                ))

            if rma_insert:
                cur.execute('DELETE FROM rma_transit')
                psycopg2.extras.execute_values(cur, '''
                    INSERT INTO rma_transit
                    (material_code, material_desc, supplier_pn, name, product_category3, quantity, bundling_number)
                    VALUES %s
                ''', rma_insert)

        count = len(insert_data)
        report(on_progress, TOTAL_STEPS, TOTAL_STEPS,
               f'✅ 各库区库存刷新完成，写入 {count} 条；RMA在途写入 {len(rma_insert)} 条')
        return build_result(True, count)

    except Exception as e:
        _logger.error('[xc_spare_parts] 各库区库存刷新失败：%s', e, exc_info=True)
        return build_result(False, error=str(e))


def query(conn, limit: int = 20, offset: int = 0, filters: dict = None) -> dict:
    """
    查询各库区库存，以物料为维度聚合，展示基础字段 + 武汉/北京等城市列。
    查询结果中城市列以 JSON 形式附加在 records 中。
    """
    where_clauses = ['1=1']
    params = []

    if filters:
        allowed = {'sap_no', 'material_desc', 'bundling_number', 'supplier_pn',
                   'spare_parts_category', 'material_type'}
        for key, val in filters.items():
            if key in allowed and val:
                where_clauses.append(f'ras.{key} ILIKE %s')
                params.append(f'%{val}%')

    where_sql = ' AND '.join(where_clauses)

    # 聚合查询：每个物料一行，城市列横向展开
    city_names = [p['city'] for p in STOCK_PARAMS]
    city_agg = ', '.join(
        f"SUM(CASE WHEN city='{c}' THEN num ELSE 0 END) AS \"{c}\""
        for c in city_names
    )

    base_sql = f'''
        SELECT
            ras.sap_no,
            MAX(COALESCE(bn.bundling_number, ras.sap_no)) AS bundling_number,
            MAX(ras.material_desc) AS material_desc,
            MAX(ras.supplier_pn) AS supplier_pn,
            MAX(ras.spare_parts_category) AS spare_parts_category,
            MAX(ras.material_type) AS material_type,
            MAX(ras.product_category3) AS product_category3,
            {city_agg}
        FROM reservoir_area_stock ras
        LEFT JOIN bundling_part_number bn ON ras.sap_no = bn.material_mode
        WHERE {where_sql}
        GROUP BY ras.sap_no
        ORDER BY ras.sap_no
    '''

    count_sql = f'''
        SELECT COUNT(DISTINCT sap_no) FROM reservoir_area_stock ras WHERE {where_sql}
    '''
    with conn.cursor() as cur:
        cur.execute(count_sql, params)
        total = cur.fetchone()[0]

    records = fetch_records(conn, base_sql, params, limit, offset)

    # 展示字段：基础字段 + 主要城市（武汉、北京、上海等前10个）
    display_cities = ['武汉', '北京', '上海', '成都', '广州', '西安', '南京', '合肥', '深圳', '天津']
    display_fields = TREE_FIELDS_BASE + display_cities
    display_labels = {**FIELD_LABELS, **{c: c for c in display_cities}}

    return {
        'total': total,
        'records': records,
        'fields': display_fields,
        'field_labels': display_labels,
        'markdown': to_markdown_table(records, display_fields, display_labels, total, limit, offset),
    }
