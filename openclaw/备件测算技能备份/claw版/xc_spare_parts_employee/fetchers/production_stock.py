"""
生产系统PO单 fetcher
对应模型：production.stock / production.batch.detail
数据库表：production_stock / production_batch_detail

刷新逻辑来源：ProductionStock.sync_data()
外部依赖：BCM 数据库（xc-bcm）
"""
import copy
import logging

import psycopg2
import psycopg2.extras

from ._base import (
    ProgressCallback, build_result, count_records,
    fetch_records, report, to_markdown_table, transaction,
)
from ._config import get_bcm_config

_logger = logging.getLogger(__name__)

TREE_FIELDS = [
    'sap_no', 'bundle', 'config_description', 'product_category2', 'product_category3',
    'total_qty', 'wuhan_stock', 'final_gap', 'service_lead_time', 'whbj_num',
    'transit_transfer', 'transit_rma', 'transit_purchase',
    'raw_material_wuhan_stock', 'company_stock_qty', 'warehouse', 'warehouse_qty',
]

FIELD_LABELS = {
    'sap_no': '转换后物料代码',
    'bundle': '捆绑',
    'config_description': '配置描述',
    'product_category2': '产品Ⅱ级分类',
    'product_category3': '产品Ⅲ级分类',
    'total_qty': '转换总数量',
    'wuhan_stock': '武汉库存量',
    'final_gap': '最终缺口',
    'service_lead_time': '服务时效',
    'whbj_num': 'WHBJ库存量',
    'transit_transfer': '转储在途',
    'transit_rma': 'RMA在途',
    'transit_purchase': '采购在途',
    'raw_material_wuhan_stock': '原料号武汉库存',
    'company_stock_qty': '公司库存数量',
    'warehouse': '库房',
    'warehouse_qty': '库存数量',
}

# BCM 查询 SQL（复制自 ProductionStock.sync_data）
_BCM_SQL = '''
WITH batches AS (
    SELECT id, batch_no, crm_no, quot_no, proj_name, process_status,
           production_batch_flowable_id, industry, delivery_date, sale, pre_sale
    FROM production_batch
),
configs AS (
    SELECT c.id AS config_id, c.batch_id, c.config_no, c.break_num, c.pro_name,
           c.sequence, c.pro_id, c.sap_no, c.parent_id, c.create_date
    FROM production_batch_config AS c
    JOIN batches AS b ON c.batch_id = b.id
    ORDER BY c.sequence ASC, c.pro_id ASC, c.sap_no ASC,
             c.parent_id DESC, c.create_date DESC, c.pro_name DESC, c.break_num DESC
),
max_transfer AS (
    SELECT pro_config_id, MAX(config_transfer_type) AS max_type
    FROM production_batch_config_detail GROUP BY pro_config_id
),
details AS (
    SELECT d.id, d.pro_config_id, d.config_sap_no, d.config_spec,
           d.config_transfer_sap_no, d.config_transfer_hw_pn, d.config_transfer_spec,
           d.config_transfer_num, d.config_transfer_total_num, d.config_sale_comment,
           d.specify_purchase, d.config_comment, d.config_number_sort, d.remark
    FROM production_batch_config_detail AS d
    JOIN max_transfer AS m ON d.pro_config_id = m.pro_config_id
                           AND d.config_transfer_type = m.max_type
    ORDER BY d.config_number_sort ASC
)
SELECT b.batch_no, b.crm_no, b.quot_no, b.proj_name,
       cfg.config_id, cfg.pro_name, cfg.config_no, cfg.break_num,
       det.config_sap_no, det.config_spec, det.config_transfer_sap_no,
       det.config_transfer_hw_pn, det.config_transfer_spec,
       det.config_transfer_num, det.config_transfer_total_num,
       det.specify_purchase, det.config_sale_comment, det.config_comment,
       CASE b.process_status
           WHEN '1' THEN '未开始' WHEN '2' THEN '流程中' WHEN '3' THEN '已完成'
           WHEN '4' THEN '已挂起' WHEN '5' THEN '已作废' ELSE '' END AS process_status,
       b.production_batch_flowable_id,
       NULL AS production_batch_flowable_name,
       det.id AS detail_id, b.industry, b.delivery_date, b.sale, b.pre_sale, det.remark
FROM configs AS cfg
JOIN batches AS b ON cfg.batch_id = b.id
JOIN details AS det ON det.pro_config_id = cfg.config_id
ORDER BY cfg.sequence ASC, cfg.pro_id ASC, cfg.sap_no ASC,
         cfg.parent_id DESC, cfg.create_date DESC, cfg.pro_name DESC,
         cfg.break_num DESC, det.config_number_sort ASC
'''


def refresh(conn, on_progress: ProgressCallback = None) -> dict:
    """从 BCM 数据库同步生产系统PO单和生产批次明细"""
    TOTAL_STEPS = 5
    try:
        # ── Step 1: 连接 BCM 数据库 ──
        report(on_progress, 1, TOTAL_STEPS, '连接 BCM 数据库...')
        bcm_cfg = get_bcm_config()
        bcm_conn = psycopg2.connect(**bcm_cfg)
        bcm_cur = bcm_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # ── Step 2: 拉取 BCM 数据 ──
        report(on_progress, 2, TOTAL_STEPS, '从 BCM 拉取生产批次数据...')
        bcm_cur.execute(_BCM_SQL)
        records = [dict(r) for r in bcm_cur.fetchall()]

        # 获取审批节点
        bcm_cur.execute('''
            SELECT DISTINCT business_flowable_id, business_no, name
            FROM bpmn_task
            WHERE business_no IN (SELECT DISTINCT batch_no FROM production_batch)
              AND audit_result = 'pending'
        ''')
        flowable_map = {(r['business_flowable_id'], r['business_no']): r['name']
                        for r in bcm_cur.fetchall()}
        bcm_conn.close()

        for rec in records:
            key = (rec['production_batch_flowable_id'], rec['batch_no'])
            rec['production_batch_flowable_name'] = flowable_map.get(key, '')

        report(on_progress, 2, TOTAL_STEPS, f'BCM 数据拉取完成，共 {len(records)} 条')

        # ── Step 3: 写入中间表 production_batch_config_view ──
        report(on_progress, 3, TOTAL_STEPS, '写入中间表...')
        with transaction(conn):
            cur = conn.cursor()
            cur.execute('DELETE FROM production_batch_config_view')
            if records:
                psycopg2.extras.execute_values(cur, '''
                    INSERT INTO production_batch_config_view (
                        batch_no, crm_no, quot_no, proj_name, config_id, pro_name, config_no, break_num,
                        config_sap_no, config_spec, config_transfer_sap_no, config_transfer_hw_pn,
                        config_transfer_spec, config_transfer_num, config_transfer_total_num,
                        specify_purchase, config_sale_comment, config_comment, process_status,
                        production_batch_flowable_id, production_batch_flowable_name,
                        detail_id, industry, delivery_date, sale, pre_sale, remark
                    ) VALUES %s
                ''', [tuple(r.values()) for r in records])

        # ── Step 4: 计算并写入 production_stock ──
        report(on_progress, 4, TOTAL_STEPS, '计算生产系统PO单数据...')
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # 读取辅助数据
            cur.execute('SELECT material_mode, bundling_number FROM bundling_part_number')
            bundling_dict = {r['material_mode']: r['bundling_number'] for r in cur.fetchall()}

            cur.execute('SELECT bundling_number, SUM(material_num) AS s FROM dump_transit WHERE bundling_number IS NOT NULL GROUP BY bundling_number')
            dump_data = {r['bundling_number']: r['s'] for r in cur.fetchall()}

            cur.execute('SELECT bundling_number, SUM(quantity) AS s FROM rma_transit WHERE bundling_number IS NOT NULL GROUP BY bundling_number')
            rma_data = {r['bundling_number']: r['s'] for r in cur.fetchall()}

            cur.execute('SELECT bundling_number, SUM(num) AS s FROM purchasing_transit WHERE bundling_number IS NOT NULL GROUP BY bundling_number')
            pur_data = {r['bundling_number']: r['s'] for r in cur.fetchall()}

            cur.execute('SELECT sap_69_no, sap_302_no FROM material_transformation WHERE sap_69_no IS NOT NULL')
            tran_data = {r['sap_69_no']: r['sap_302_no'] for r in cur.fetchall()}

            cur.execute('SELECT sap_no, city, num FROM reservoir_area_stock')
            res_sap = {}
            res_bind = {}
            for r in cur.fetchall():
                res_sap.setdefault(r['sap_no'], []).append(r)
            cur.execute('SELECT bundling_number, city, num FROM reservoir_area_stock ras LEFT JOIN bundling_part_number bn ON ras.sap_no = bn.material_mode')
            for r in cur.fetchall():
                res_bind.setdefault(r['bundling_number'], []).append(r)

            cur.execute("SELECT bundling_number, SUM(stock_quantity) AS s FROM kunpeng_daily WHERE stock_address IN ('JS02','JS09','KT01','KT02','KT09','KT16','KTLP','KT17','KTYF') GROUP BY bundling_number")
            stock_data = {r['bundling_number']: r['s'] for r in cur.fetchall()}

            # 获取服务时效
            cur.execute("SELECT DISTINCT proj_name, STRING_AGG(config_transfer_spec, ',') AS spec FROM production_batch_config_view WHERE config_sap_no LIKE '80-%' OR config_sap_no LIKE '690-%' GROUP BY proj_name")
            service_data = {r['proj_name']: r['spec'] for r in cur.fetchall()}

            # 获取产品分类
            cur.execute('SELECT sap_no, product_category2, product_category3 FROM xc_plm_material WHERE product_category2 IS NOT NULL')
            plm_map = {r['sap_no']: (r['product_category2'], r['product_category3']) for r in cur.fetchall()}

            # 展开 BOM
            cur.execute('SELECT material_code, assembly, bom_quantity FROM material_bom')
            bom_rows = cur.fetchall()
            bom_dict = {}
            for r in bom_rows:
                bom_dict.setdefault(r['material_code'], []).append(r)

            # 查询汇总结果
            cur.execute('''
                SELECT COALESCE(material_bom.assembly, config_transfer_sap_no) AS sap_no,
                       SUM(CASE WHEN material_bom.assembly IS NOT NULL THEN config_transfer_total_num * material_bom.bom_quantity
                                ELSE config_transfer_total_num END) AS num,
                       MAX(config_transfer_spec) AS des,
                       string_agg(config_transfer_spec, ',') AS service,
                       process_status, production_batch_flowable_name, batch_no,
                       MAX(config_transfer_sap_no) AS service_sap_no,
                       MAX(proj_name) AS proj_name
                FROM production_batch_config_view
                LEFT JOIN material_bom ON config_transfer_sap_no = material_bom.material_code
                WHERE config_transfer_sap_no IS NOT NULL
                GROUP BY sap_no, process_status, production_batch_flowable_name, batch_no
                ORDER BY sap_no
            ''')
            results = cur.fetchall()

            # 过滤非电子物料
            cur.execute('SELECT material_mode FROM non_electronic_materials')
            non_set = {r['material_mode'] for r in cur.fetchall()}
            results = [r for r in results if r['sap_no'] not in non_set]

        # 构建 production_stock 插入数据
        final_results = []
        for rec in results:
            rec = dict(rec)
            sap_no = rec['sap_no']
            if sap_no.startswith('69-') or sap_no.startswith('68-'):
                sap_no = tran_data.get(sap_no, sap_no)
            bind = bundling_dict.get(sap_no, sap_no)
            wuhan = sum(r.get('武汉', 0) for r in res_bind.get(bind, []))
            old_wuhan = sum(r.get('武汉', 0) for r in res_sap.get(sap_no, []))
            pro2, pro3 = plm_map.get(sap_no, ('', ''))
            service_lead = _get_service_level(service_data.get(rec['proj_name'], '基础保修'))
            final_results.append((
                sap_no, bind, rec['des'], pro2, pro3, rec['num'],
                wuhan, 0,  # final_gap 暂为0，需从备料总表获取
                service_lead, dump_data.get(bind, 0), rma_data.get(bind, 0),
                pur_data.get(bind, 0), old_wuhan, stock_data.get(sap_no, 0),
                None, None, rec['process_status'], rec['production_batch_flowable_name'],
                rec['batch_no'], rec['batch_no'][2:10] if len(rec['batch_no']) >= 10 else None,
            ))

        with transaction(conn):
            cur = conn.cursor()
            cur.execute('DELETE FROM production_stock')
            if final_results:
                psycopg2.extras.execute_values(cur, '''
                    INSERT INTO production_stock (
                        sap_no, bundle, config_description, product_category2, product_category3,
                        total_qty, wuhan_stock, final_gap, service_lead_time,
                        transit_transfer, transit_rma, transit_purchase,
                        raw_material_wuhan_stock, company_stock_qty,
                        warehouse, warehouse_qty, process_status,
                        production_batch_flowable_name, batch_no, batch_time
                    ) VALUES %s
                ''', final_results)

        count = len(final_results)
        report(on_progress, TOTAL_STEPS, TOTAL_STEPS, f'✅ 生产系统PO单刷新完成，共写入 {count} 条')
        return build_result(True, count)

    except Exception as e:
        _logger.error('[xc_spare_parts] 生产系统PO单刷新失败：%s', e, exc_info=True)
        return build_result(False, error=str(e))


def query(conn, limit: int = 20, offset: int = 0, filters: dict = None) -> dict:
    """查询生产系统PO单（按 sap_no 聚合）"""
    where_clauses = ['1=1']
    params = []

    if filters:
        allowed = {'sap_no', 'bundle', 'process_status', 'service_lead_time', 'product_category2'}
        for key, val in filters.items():
            if key in allowed and val:
                where_clauses.append(f'{key} ILIKE %s')
                params.append(f'%{val}%')

    where_sql = ' AND '.join(where_clauses)
    base_sql = f'''
        SELECT MAX(id) AS id, sap_no, bundle,
               MAX(config_description) AS config_description,
               MAX(product_category2) AS product_category2,
               MAX(product_category3) AS product_category3,
               SUM(total_qty) AS total_qty,
               wuhan_stock, final_gap,
               (ARRAY_AGG(service_lead_time ORDER BY
                   CASE WHEN service_lead_time = '2H/4H' THEN 1
                        WHEN service_lead_time = 'ND' THEN 2
                        WHEN service_lead_time = '基础保修' THEN 3 ELSE 4 END))[1] AS service_lead_time,
               0 AS whbj_num,
               transit_transfer, transit_rma, transit_purchase,
               raw_material_wuhan_stock, company_stock_qty,
               MAX(warehouse) AS warehouse, MAX(warehouse_qty) AS warehouse_qty
        FROM production_stock
        WHERE {where_sql}
        GROUP BY sap_no, bundle, wuhan_stock, final_gap,
                 transit_transfer, transit_rma, transit_purchase,
                 raw_material_wuhan_stock, company_stock_qty
        ORDER BY sap_no
    '''

    total = count_records(conn, f'SELECT COUNT(DISTINCT sap_no) FROM production_stock WHERE {where_sql}', params)
    records = fetch_records(conn, base_sql, params, limit, offset)

    # 补充 WHBJ 库存
    with conn.cursor() as cur:
        cur.execute("SELECT bundling_number, SUM(stock_quantity) AS s FROM kunpeng_daily WHERE stock_address = 'WHBJ' GROUP BY bundling_number")
        whbj = {r[0]: r[1] for r in cur.fetchall()}
    for rec in records:
        rec['whbj_num'] = whbj.get(rec.get('bundle'), 0)

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
    return get_service_level(config_desc, default='基础保修')
