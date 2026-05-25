"""
其他库区库存 fetcher
对应模型：other.reservoir.area.stock
数据库表：other_reservoir_area_stock

刷新逻辑来源：OtherReservoirAreaStock.get_wms_data()
外部依赖：WMS 接口（与 reservoir_area_stock 相同接口，不同库存地编码）
"""
import copy
import logging

import psycopg2.extras

from ._base import (
    ProgressCallback, build_result, count_records,
    fetch_records, report, to_markdown_table, transaction,
)
from .reservoir_area_stock import _get_wms_stock, RMA_PARAMS

_logger = logging.getLogger(__name__)

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

# 其他库区库存地编码 → 城市名称映射
OTHER_STOCK_PARAMS = [
    {'city': '北京民生银行', 'param': 'KCDBJ-BJMSYHBJC'},
    {'city': '合肥张蕾蕾', 'param': 'KCDBJ-HFZLLBJC'},
    {'city': '厦门苏贤圣', 'param': 'KCDBJ-XMSXSBJC'},
    {'city': '上海太平洋保险', 'param': 'KCDBJ-SHTPYBXBJC'},
    {'city': '上海王洋洋', 'param': 'KCDBJ-SHWYYBJC'},
    {'city': '上海中国银联', 'param': 'KCDBJ-SHZGYLBJC'},
    {'city': '威海银行', 'param': 'KCDBJ-WHYHBJC'},
    {'city': '长春国税局', 'param': 'KCDBJ-CCGSJBJC'},
    {'city': '廊坊软通', 'param': 'KCDBJ-LFRTBJC'},
    {'city': '北京亦庄', 'param': 'KCDBJ-BJYZBJC'},
    {'city': '呼和浩特联通云基地', 'param': 'KCDBJ-LTYJDBJC'},
    {'city': '汕头移动', 'param': 'KCDBJ-STHYQBJC'},
    {'city': '佛山人保', 'param': 'KCDBJ-FSLZMBJC'},
    {'city': '新疆JS', 'param': 'KCDBJ-XJJSBJC'},
    {'city': '玉溪', 'param': 'KCDBJ-YXWXZ'},
    {'city': '上海交行', 'param': 'KCDBJ-SHJHBJC'},
    {'city': '郑州联通', 'param': 'KCDBJ-ZZLTBJC'},
    {'city': '福州兴业银行', 'param': 'KCDBJ-FZXYYHBJC'},
    {'city': '北京建设银行', 'param': 'KCDBJ-BJJSYHBJC'},
    {'city': '上海人行清算', 'param': 'KCDBJ-SHRHQSBJC'},
    {'city': '枣庄联通', 'param': 'KCDBJ-ZZLTBJC2'},
    {'city': '广州移动', 'param': 'KCDBJ-GZYDBJC'},
    {'city': '上海银联外高桥', 'param': 'KCDBJ-SHYLWGQBJC'},
    {'city': '上海银联顾唐路', 'param': 'KCDBJ-SHYLGTLBJC'},
    {'city': '宁波移动', 'param': 'KCDBJ-NBYDBJC'},
    {'city': '北京银联', 'param': 'KCDBJ-BJYLBJC'},
    {'city': '武汉建行', 'param': 'KCDBJ-WHJHBJC'},
    {'city': '大连邮储银行', 'param': 'KCDBJ-DLYCYHBJC'},
    {'city': '合肥邮储银行湖滨', 'param': 'KCDBJ-HFYCYHBJC'},
    {'city': '廊坊银行', 'param': 'KCDBJ-LFYHBJC'},
    {'city': '合肥邮储银行南岗', 'param': 'KCDBJ-HFYCYHBJC2'},
    {'city': '福建金税', 'param': 'KCDBJ-FJJSBJC'},
    {'city': '上海光大证券', 'param': 'KCDBJ-SHGDZQBJC'},
    {'city': '超时硬盘', 'param': 'KCDBJ-CSYPC'},
    {'city': '武汉废品', 'param': 'KCDBJ-WHFPC'},
    {'city': '武汉测试仓', 'param': 'KCDBJ-WHCSC'},
    {'city': '武汉借用仓', 'param': 'KCDBJ-WHJYC'},
    {'city': '维修在途', 'param': 'WHWXC-WXZT'},
    {'city': '委外维修', 'param': 'WHWXC-WWWX'},
    {'city': '湛江移动', 'param': 'KCDBJ-ZJYDBJC'},
    {'city': '南京移动', 'param': 'KCDBJ-NJYDBJC'},
    {'city': '天津电信', 'param': 'KCDBJ-TJDXBJC'},
    {'city': '作战指挥项目', 'param': 'KCDBJ-ZZZHXMBJC'},
    {'city': '金华银行', 'param': 'KCDBJ-JHYHBJC'},
    {'city': '成都太平洋保险', 'param': 'KCDBJ-CDTPYBXBJC'},
    {'city': '呼和浩特建行', 'param': 'KCDBJ-HHHTJHBJC'},
    {'city': '哈尔滨联通', 'param': 'KCDBJ-HEBLTBJC'},
    {'city': '哈尔滨移动', 'param': 'KCDBJ-HEBYDBJC'},
    {'city': '喀什', 'param': 'KCDBJ-KSBJC'},
    {'city': '吐鲁番', 'param': 'KCDBJ-TLFBJC'},
    {'city': '巴州', 'param': 'KCDBJ-BZBJC'},
    {'city': '和田', 'param': 'KCDBJ-HTBJC'},
    {'city': '咸阳联通', 'param': 'KCDBJ-XYLTBJC'},
    {'city': '北京中央国债', 'param': 'KCDBJ-BJZYGZBJC'},
    {'city': '无锡人行清算', 'param': 'KCDBJ-WXRHQSBJC'},
    {'city': '上海中国人寿', 'param': 'KCDBJ-SHZGRSBJC'},
    {'city': '厦门税务', 'param': 'KCDBJ-XMSWBJC'},
    {'city': '北京中国人寿备件仓', 'param': 'KCDBJ-BJZGRSBJC'},
    {'city': '安顺国家电投', 'param': 'KCDBJ-ASGJDTBJC'},
    {'city': '北京人行清算', 'param': 'KCDBJ-BJRHQSBJC'},
    {'city': '上海浦江国家实验室', 'param': 'KCDBJ-SHPJGJSYSBJC'},
    {'city': '徐州国家管网', 'param': 'KCDBJ-XZGJGWBJC'},
    {'city': '北京国家管网', 'param': 'KCDBJ-BJGJGWBJC'},
]

_OTHER_PARAM_TO_CITY = {p['param']: p['city'] for p in OTHER_STOCK_PARAMS}
_OTHER_CITY_FIELDS = [p['city'] for p in OTHER_STOCK_PARAMS]


def refresh(conn, on_progress: ProgressCallback = None) -> dict:
    """从 WMS 接口同步其他库区库存"""
    TOTAL_STEPS = 4
    try:
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

        report(on_progress, 2, TOTAL_STEPS, f'调用 WMS 接口，共 {len(sap_nos)} 个物料...')
        stock_list = _get_wms_stock(sap_nos)

        report(on_progress, 3, TOTAL_STEPS, '分类处理其他库区库存数据...')
        real_res = []
        for r in stock_list:
            city = _OTHER_PARAM_TO_CITY.get(r['stock_address'])
            if city:
                temp = copy.deepcopy(r)
                temp['stock_address'] = city
                real_res.append(temp)

        report(on_progress, 4, TOTAL_STEPS, f'写入其他库区库存，共 {len(real_res)} 条...')
        with transaction(conn):
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute('SELECT material_code, material_desc, supplier_pn, name, product_category3, spare_parts_category FROM base_material')
            base_dict = {r['material_code']: r for r in cur.fetchall()}

            cur.execute('DELETE FROM other_reservoir_area_stock')
            insert_data = []
            for r in real_res:
                base = base_dict.get(r['sap_no'], {})
                insert_data.append((
                    r['sap_no'], r['stock_address'], r['quantity'],
                    base.get('material_desc', ''), base.get('supplier_pn', ''),
                    base.get('name', ''), base.get('product_category3', ''),
                    base.get('spare_parts_category', ''),
                ))

            if insert_data:
                psycopg2.extras.execute_values(cur, '''
                    INSERT INTO other_reservoir_area_stock
                    (sap_no, city, num, material_desc, supplier_pn, material_type, product_category3, spare_parts_category)
                    VALUES %s
                ''', insert_data)

        count = len(insert_data)
        report(on_progress, TOTAL_STEPS, TOTAL_STEPS, f'✅ 其他库区库存刷新完成，共写入 {count} 条')
        return build_result(True, count)

    except Exception as e:
        _logger.error('[xc_spare_parts] 其他库区库存刷新失败：%s', e, exc_info=True)
        return build_result(False, error=str(e))


def query(conn, limit: int = 20, offset: int = 0, filters: dict = None) -> dict:
    """查询其他库区库存，以物料为维度聚合"""
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
    city_agg = ', '.join(
        f"SUM(CASE WHEN city='{c}' THEN num ELSE 0 END) AS \"{c}\""
        for c in _OTHER_CITY_FIELDS
    )

    base_sql = f'''
        SELECT ras.sap_no,
               MAX(COALESCE(bn.bundling_number, ras.sap_no)) AS bundling_number,
               MAX(ras.material_desc) AS material_desc,
               MAX(ras.supplier_pn) AS supplier_pn,
               MAX(ras.spare_parts_category) AS spare_parts_category,
               MAX(ras.material_type) AS material_type,
               MAX(ras.product_category3) AS product_category3,
               {city_agg}
        FROM other_reservoir_area_stock ras
        LEFT JOIN bundling_part_number bn ON ras.sap_no = bn.material_mode
        WHERE {where_sql}
        GROUP BY ras.sap_no ORDER BY ras.sap_no
    '''

    with conn.cursor() as cur:
        cur.execute(f'SELECT COUNT(DISTINCT sap_no) FROM other_reservoir_area_stock ras WHERE {where_sql}', params)
        total = cur.fetchone()[0]

    records = fetch_records(conn, base_sql, params, limit, offset)

    # 展示字段：基础字段 + 前10个特殊库区
    display_cities = _OTHER_CITY_FIELDS[:10]
    display_fields = TREE_FIELDS_BASE + display_cities
    display_labels = {**FIELD_LABELS, **{c: c for c in display_cities}}

    return {
        'total': total,
        'records': records,
        'fields': display_fields,
        'field_labels': display_labels,
        'markdown': to_markdown_table(records, display_fields, display_labels, total, limit, offset),
    }
