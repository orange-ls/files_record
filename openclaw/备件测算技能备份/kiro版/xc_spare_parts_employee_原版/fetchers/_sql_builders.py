"""
共享 SQL 构建函数
备料总表和替代料备料总表的查询 SQL 被 summary_kanban 和 material_shortage 的 refresh 依赖，
同时也被 prepare_materials.query() 和 alternative_prepare_materials.query() 直接调用。

两种模式：
  - 存量表模式（information_sources='存量表'）：按 information_sources 分组，保留 information_sources 维度
  - PO与存量模式（information_sources='' 或 None，默认）：不按 information_sources 分组，通过字符串替换去掉相关维度

实现方式：
  与原始 Odoo 模型代码保持一致，先生成包含 information_sources 的完整 SQL（存量表模式），
  PO与存量模式下通过字符串替换去掉 information_sources 相关片段，确保结果与原始代码完全一致。
"""
from ._constants import CITY_FIELDS, STOCK_ADDRESSES


def _get_city_values_sql():
    """生成城市列表的 VALUES 子句（排除武汉）"""
    return ', '.join(f"('{c}')" for c in CITY_FIELDS if c != '武汉')


def _get_addr_case_sql():
    """生成 XC02/XC16/XC17 库存地 CASE 聚合子句"""
    return ', '.join(
        f"SUM(CASE WHEN factory_code='{a['stock']}' AND stock_address='{a['name']}' "
        f"THEN stock_quantity ELSE 0 END) AS {a['name']}_quantity"
        for a in STOCK_ADDRESSES
    )


def _get_addr_field_list():
    """生成 XC02_quantity, XC16_quantity, XC17_quantity 字段列表"""
    return ', '.join(f"{a['name']}_quantity" for a in STOCK_ADDRESSES)


def _get_addr_field_list_prefixed(prefix='H'):
    """生成带前缀的 XC02_quantity 等字段列表"""
    return ', '.join(f"{prefix}.{a['name']}_quantity" for a in STOCK_ADDRESSES)



def build_prepare_sql(information_sources: str = None) -> str:
    """
    构建备料总表查询 SQL。
    与原始 Odoo 模型 prepare.materials.search_sql() 完全一致。

    :param information_sources:
        - None 或 ''：PO与存量模式（默认），通过字符串替换去掉 information_sources 维度
        - '存量表'：存量表模式，保留 information_sources 维度
    """
    is_po_mode = (information_sources is None or information_sources == '')

    city_case = _get_city_values_sql()
    addr_case = _get_addr_case_sql()
    addr_fields = _get_addr_field_list()
    addr_fields_h = _get_addr_field_list_prefixed('H')

    # 与原始代码一致：先生成包含 information_sources 的完整 SQL（存量表模式）
    search_sql = f'''
    SELECT COALESCE(T.sales,0) as sales,reserve_quantity,T.information_sources,
        T.remark,bundling_number,T.material_code,material_desc,supplier_PN AS supplier_pn,
        name,product_category3,spare_parts_category,COALESCE(T.total_usage,0) as total_usage,
        theoretical_defect_rate::float AS theo_non_rate,city,
        COALESCE(T.stock_quantity,0) as stock_quantity,
        CASE WHEN theoretical_defect_rate IS NULL THEN NULL ELSE
        COALESCE( (T.stock_quantity - T.reserve_quantity),0 ) END AS gap_quantity,wuhan_stock_quantity,

        CASE WHEN theoretical_defect_rate IS NULL THEN NULL
        WHEN wuhan_stock_quantity>=ceil(total_usage*theoretical_defect_rate::float/6) AND wuhan_stock_quantity>0 THEN 'adequate'
        WHEN wuhan_stock_quantity>=ceil(total_usage*theoretical_defect_rate::float/6)/2
            AND wuhan_stock_quantity<ceil(total_usage*theoretical_defect_rate::float/6) THEN 'replenished'
        WHEN wuhan_stock_quantity>0 AND wuhan_stock_quantity<ceil(total_usage*theoretical_defect_rate::float/6)/2 THEN 'urgently_replenished'
        WHEN wuhan_stock_quantity<=0 THEN 'out_of_stock'
        ELSE 'out_of_stock' END as stock_alert_status,
        CASE WHEN theoretical_defect_rate IS NULL THEN NULL ELSE
        COALESCE(H.sum_each_gap,0) end as sum_each_gap,
        CASE WHEN theoretical_defect_rate IS NULL THEN NULL ELSE
        COALESCE( COALESCE(H.sum_each_gap,0) + COALESCE(XC17_quantity,0)
        + COALESCE(purchase_in_transit,0) + COALESCE(dump_in_transit,0) + COALESCE(rma_in_transit,0),0)
        end as final_gap, {addr_fields},
        COALESCE(T.purchase_in_transit,0) as purchase_in_transit,
        COALESCE(T.dump_in_transit,0) as dump_in_transit,
        COALESCE(T.rma_in_transit,0) as rma_in_transit
    '''

    base_sql = f'''FROM
        (SELECT C.remark,A.information_sources,A.material_mode material_code,
            COALESCE(B.bundling_number, A.material_mode) AS bundling_number,
            C.material_desc,C.supplier_PN,C.name,C.product_category3,C.spare_parts_category,
            total_usage,theoretical_defect_rate,E.city,F.sales,
            CASE
                WHEN theoretical_defect_rate IS NULL THEN NULL
                WHEN sales*theoretical_defect_rate::float>= 8 THEN ceil((sales*theoretical_defect_rate::float/4)::numeric)
                WHEN sales*theoretical_defect_rate::float<8 AND sales*theoretical_defect_rate::float>1 THEN 2
                WHEN sales*theoretical_defect_rate::float<=1 AND sales*theoretical_defect_rate::float>0 THEN 1
                WHEN sales*theoretical_defect_rate::float=0 THEN 0 ELSE 0
            END AS reserve_quantity,
            COALESCE(G.num,0) as stock_quantity,
            COALESCE(L.num,0) as wuhan_stock_quantity,
            {addr_fields_h},
            I.num purchase_in_transit,
            J.material_num dump_in_transit,
            K.quantity rma_in_transit
        FROM
        (
            SELECT A.information_sources,A.material_mode,COALESCE(C.total_usage,0) total_usage
            FROM (SELECT information_sources,
                CASE WHEN b2.bundling_number IS NOT NULL THEN b3.material_mode
                     WHEN b2.bundling_number IS NULL THEN b1.material_mode
                END AS material_mode,b2.bundling_number
                FROM bom_total_table b1 LEFT JOIN bundling_part_number b2
                ON b1.material_mode = b2.material_mode
                LEFT JOIN bundling_part_number b3 on b2.bundling_number=b3.bundling_number
                GROUP BY b1.material_mode,b3.material_mode,b2.bundling_number,information_sources) A
            LEFT JOIN (SELECT information_sources,material_mode,sum(sum_count) total_usage
                FROM bom_total_table
                GROUP BY material_mode,information_sources) C
                ON A.information_sources=C.information_sources and A.material_mode=C.material_mode
            GROUP BY A.material_mode,C.total_usage,A.information_sources
        ) A
        LEFT JOIN bundling_part_number B ON B.material_mode=A.material_mode
        LEFT JOIN base_material C ON C.material_code=A.material_mode
        LEFT JOIN reject_ratio D ON D.sap_no=A.material_mode
        LEFT JOIN (SELECT * FROM (VALUES {city_case}) as t(city)) E ON 1=1
        LEFT JOIN (
            SELECT material_mode,sum(sum_count) sales,stock_location,information_sources
            FROM (
                SELECT material_mode,sum_count,
                CASE WHEN stock_location like '武汉' THEN '武汉项目'
                ELSE stock_location
                END AS stock_location,information_sources FROM bom_total_table)
            T GROUP BY material_mode,stock_location,information_sources
            ORDER BY material_mode) F ON A.material_mode=F.material_mode AND F.stock_location=E.city
            AND A.information_sources=F.information_sources
        LEFT JOIN reservoir_area_stock G ON G.sap_no=A.material_mode AND G.city=E.city
        LEFT JOIN (SELECT bom_total_table.material_mode,{addr_case}
            FROM (SELECT * FROM (SELECT
                CASE WHEN b2.bundling_number IS NOT NULL THEN b3.material_mode
                     WHEN b2.bundling_number IS NULL THEN b1.material_mode
                END AS material_mode
                FROM bom_total_table b1 LEFT JOIN bundling_part_number b2
                ON b1.material_mode = b2.material_mode
                LEFT JOIN bundling_part_number b3 on b2.bundling_number=b3.bundling_number
                GROUP BY b1.material_mode,b3.material_mode,b2.bundling_number) T GROUP BY material_mode) bom_total_table
            LEFT JOIN kunpeng_daily ON kunpeng_daily.material_code=bom_total_table.material_mode
                AND stock_category!='借用在途库'
            GROUP BY material_mode) H ON H.material_mode=A.material_mode
        LEFT JOIN purchasing_transit I ON I.material_mode=A.material_mode
        LEFT JOIN dump_transit J ON J.sap_no=A.material_mode
        LEFT JOIN rma_transit K ON K.material_code=A.material_mode
        LEFT JOIN reservoir_area_stock L ON L.sap_no=A.material_mode AND L.city='武汉') T
    LEFT JOIN
        (SELECT information_sources,material_code,sum(gap_quantity) sum_each_gap FROM (
        SELECT information_sources,material_code,city,(T.stock_quantity-T.reserve_quantity) as gap_quantity
        FROM
        (SELECT A.information_sources,A.material_mode material_code,theoretical_defect_rate,E.city,F.sales,
            CASE
                WHEN sales*theoretical_defect_rate::float>= 8 THEN ceil((sales*theoretical_defect_rate::float/4)::numeric)
                WHEN sales*theoretical_defect_rate::float<8 AND sales*theoretical_defect_rate::float>1 THEN 2
                WHEN sales*theoretical_defect_rate::float<=1 AND sales*theoretical_defect_rate::float>0 THEN 1
                WHEN sales*theoretical_defect_rate::float=0 THEN 0 ELSE 0
            END AS reserve_quantity,COALESCE(G.num,0) as stock_quantity
        FROM
        (
            SELECT A.information_sources,A.material_mode,COALESCE(C.total_usage,0) total_usage
            FROM (SELECT information_sources,
                CASE WHEN b2.bundling_number IS NOT NULL THEN b3.material_mode
                     WHEN b2.bundling_number IS NULL THEN b1.material_mode
                END AS material_mode,b2.bundling_number
                FROM bom_total_table b1 LEFT JOIN bundling_part_number b2
                ON b1.material_mode = b2.material_mode
                LEFT JOIN bundling_part_number b3 on b2.bundling_number=b3.bundling_number
                GROUP BY b1.material_mode,b3.material_mode,b2.bundling_number,information_sources) A
            LEFT JOIN (SELECT information_sources,material_mode,sum(sum_count) total_usage
                FROM bom_total_table
                GROUP BY material_mode,information_sources) C
                ON A.information_sources=C.information_sources and A.material_mode=C.material_mode
            GROUP BY A.material_mode,C.total_usage,A.information_sources
        ) A
        LEFT JOIN reject_ratio D ON D.sap_no=A.material_mode
        LEFT JOIN (SELECT * FROM (VALUES {city_case}) as t(city)) E ON 1=1
        LEFT JOIN (
            SELECT material_mode, sum(sum_count) sales,stock_location,information_sources
            FROM (
                SELECT material_mode,sum_count,
                CASE WHEN stock_location like '武汉' THEN '武汉项目'
                ELSE stock_location
                END AS stock_location,information_sources FROM bom_total_table)
            T GROUP BY material_mode,stock_location,information_sources
            ORDER BY material_mode) F ON A.material_mode=F.material_mode AND F.stock_location=E.city
            AND A.information_sources=F.information_sources
        LEFT JOIN reservoir_area_stock G ON G.sap_no=A.material_mode AND G.city=E.city) T) T
        GROUP BY material_code,information_sources) H
    ON T.material_code=H.material_code AND T.information_sources=H.information_sources
    '''

    sql = search_sql + base_sql

    # PO与存量模式：通过字符串替换去掉 information_sources 维度（与原始代码替换逻辑完全一致）
    if is_po_mode:
        sql = sql.replace('T.information_sources,', '')
        sql = sql.replace('A.information_sources,', '')
        sql = sql.replace('AND A.information_sources=F.information_sources', '')
        sql = sql.replace('AND T.information_sources=H.information_sources', '')
        sql = sql.replace('A.information_sources=C.information_sources and ', '')
        sql = sql.replace(',information_sources', '')
        sql = sql.replace('information_sources,', '')
        sql = sql.replace(',A.information_sources', '')
        sql = sql.replace(
            'SELECT information_sources,material_mode,sum(sum_count) total_usage FROM bom_total_table GROUP BY material_mode,information_sources',
            'SELECT material_mode,sum(sum_count) total_usage FROM bom_total_table GROUP BY material_mode'
        )

    return sql


def build_alternative_sql(information_sources: str = None) -> str:
    """
    构建替代料备料总表查询 SQL。
    与原始 Odoo 模型 alternative.prepare.materials.search_sql() 完全一致。

    :param information_sources:
        - None 或 ''：PO与存量模式（默认），通过字符串替换去掉 information_sources 维度
        - '存量表'：存量表模式，保留 information_sources 维度
    """
    is_po_mode = (information_sources is None or information_sources == '')

    city_case = _get_city_values_sql()
    addr_case = _get_addr_case_sql()
    addr_fields = _get_addr_field_list()

    # 生成 sum(H.XC02_quantity) XC02_quantity, sum(H.XC16_quantity) XC16_quantity, sum(H.XC17_quantity) as XC17_quantity,
    # 与原始代码一致：XC17 用 'as' 关键字，其他不用；XC17 后面有逗号
    addr_sum_fields_parts = []
    for a in STOCK_ADDRESSES:
        if a['name'] == 'XC17':
            addr_sum_fields_parts.append(f"sum(H.{a['name']}_quantity) as {a['name']}_quantity,")
        else:
            addr_sum_fields_parts.append(f"sum(H.{a['name']}_quantity) {a['name']}_quantity")
    addr_sum_fields = ', '.join(addr_sum_fields_parts)

    # 与原始代码一致：先生成包含 information_sources 的完整 SQL（存量表模式）
    search_sql = f'''
    SELECT T.information_sources,T.bundling_number,NAME,product_category3,spare_parts_category,
        COALESCE(T.total_usage,0) as total_usage,
        theoretical_defect_rate::FLOAT AS theo_non_rate,city,
        COALESCE(T.sales,0) as sales,reserve_quantity,
        COALESCE(T.stock_quantity,0) as stock_quantity,
        CASE WHEN theoretical_defect_rate IS NULL THEN NULL ELSE
        COALESCE( (T.stock_quantity - T.reserve_quantity),0 ) END AS gap_quantity,wuhan_stock_quantity,
        CASE
            WHEN theoretical_defect_rate IS NULL THEN NULL
            WHEN wuhan_stock_quantity >= ceil(total_usage*theoretical_defect_rate::float/6) AND wuhan_stock_quantity>0 THEN 'adequate'
            WHEN wuhan_stock_quantity >= ceil(total_usage*theoretical_defect_rate::float/6) / 2
                AND wuhan_stock_quantity < ceil(total_usage*theoretical_defect_rate::float/6) THEN 'replenished'
            WHEN wuhan_stock_quantity > 0
                AND wuhan_stock_quantity < ceil(total_usage*theoretical_defect_rate::float/6) / 2 THEN 'urgently_replenished'
            WHEN wuhan_stock_quantity <= 0 THEN 'out_of_stock'
            ELSE 'out_of_stock'
        END AS stock_alert_status,
        CASE WHEN theoretical_defect_rate IS NULL THEN NULL ELSE
        COALESCE(H.sum_each_gap,0) end as sum_each_gap,
        CASE WHEN theoretical_defect_rate IS NULL THEN NULL ELSE
        COALESCE( COALESCE(H.sum_each_gap,0) + COALESCE(XC17_quantity,0)
         + COALESCE(purchase_in_transit,0) + COALESCE(dump_in_transit,0) + COALESCE(rma_in_transit,0),0)
        END AS final_gap, {addr_fields},
        COALESCE(T.purchase_in_transit,0) as purchase_in_transit,
        COALESCE(T.dump_in_transit,0) as dump_in_transit,
        COALESCE(T.rma_in_transit,0) as rma_in_transit
    '''

    base_sql = f''' FROM
        (SELECT A.information_sources, A.bundling_number,E.city,
            B.NAME,B.product_category3,B.spare_parts_category,C.total_usage,
            round(sum(COALESCE(M.theoretical_defect_rate,0))::numeric
                / NULLIF(count(A.bundling_number), 0)::numeric, 8) AS theoretical_defect_rate,
            F.sales sales,
            CASE
                WHEN round(sum(COALESCE(M.theoretical_defect_rate,0))::numeric
                    / NULLIF(count(A.bundling_number), 0)::numeric, 8) IS NULL THEN NULL
                WHEN sales * round(sum(COALESCE(M.theoretical_defect_rate,0))::numeric
                    / NULLIF(count(A.bundling_number), 0)::numeric, 8)::FLOAT >= 8 THEN
                    ceil(( sales * round(sum(COALESCE(M.theoretical_defect_rate,0))::numeric
                    / NULLIF(count(A.bundling_number), 0)::numeric, 8)::FLOAT / 4)::numeric)
                WHEN sales * round(sum(COALESCE(M.theoretical_defect_rate,0))::numeric
                    / NULLIF(count(A.bundling_number), 0)::numeric, 8)::FLOAT < 8
                    AND sales * round(sum(COALESCE(M.theoretical_defect_rate,0))::numeric
                    / NULLIF(count(A.bundling_number), 0)::numeric, 8)::FLOAT > 1 THEN 2
                WHEN sales * round(sum(COALESCE(M.theoretical_defect_rate,0))::numeric
                    / NULLIF(count(A.bundling_number), 0)::numeric, 8)::FLOAT <= 1
                    AND sales * round(sum(COALESCE(M.theoretical_defect_rate,0))::numeric
                    / NULLIF(count(A.bundling_number), 0)::numeric, 8)::FLOAT > 0 THEN 1
                WHEN sales * round(sum(COALESCE(M.theoretical_defect_rate,0))::numeric
                    / NULLIF(count(A.bundling_number), 0)::numeric, 8)::FLOAT = 0 THEN 0
                ELSE 0
            END AS reserve_quantity,
            COALESCE(sum(G.num),0) as stock_quantity,
            COALESCE(sum(L.num),0) as wuhan_stock_quantity,
            {addr_sum_fields}
            COALESCE(sum(I.num::int),0) purchase_in_transit,
            COALESCE(sum(J.material_num),0) dump_in_transit,
            COALESCE(sum(K.quantity),0) rma_in_transit
        FROM
        (
            SELECT A.information_sources,B.material_mode,B.bundling_number
            FROM (SELECT bom_total_table.* FROM
                bom_total_table INNER JOIN bundling_part_number
                ON bom_total_table.material_mode=bundling_part_number.material_mode) A
            LEFT JOIN bundling_part_number B on A.bundling_number=B.bundling_number
            GROUP BY A.information_sources,B.material_mode,B.bundling_number
        ) A
        LEFT JOIN
        (
            SELECT bundling_number,name,product_category3,spare_parts_category FROM(
            SELECT b1.bundling_number,name,b2.product_category3,b2.spare_parts_category,
                ROW_NUMBER() OVER (PARTITION BY b1.bundling_number ORDER BY b1.bundling_number DESC) AS group_idx
            FROM bundling_part_number b1 LEFT JOIN base_material b2
            on b1.material_mode=b2.material_code) B WHERE group_idx=1
        ) B ON A.bundling_number = B.bundling_number
        LEFT JOIN ( SELECT T.bundling_number,SUM(T.total_usage) total_usage,T.information_sources FROM
            (SELECT A.bundling_number,A.material_mode,SUM(sum_count) total_usage,information_sources FROM
            bundling_part_number A,bom_total_table B WHERE A.material_mode=B.material_mode
            GROUP BY A.bundling_number,A.material_mode,B.information_sources) T
            GROUP BY bundling_number,information_sources ) C
            ON A.bundling_number=C.bundling_number AND A.information_sources=C.information_sources
        LEFT JOIN ( SELECT * FROM (VALUES {city_case}) as t(city)) E ON 1 = 1
        LEFT JOIN (
            SELECT T1.* FROM (SELECT T.bundling_number, sum(sales) sales, stock_location,information_sources FROM (
            SELECT A.bundling_number,sum_count sales,
            CASE WHEN stock_location like '武汉' THEN '武汉项目'
            ELSE stock_location
            END AS stock_location,information_sources
            FROM bundling_part_number A INNER JOIN bom_total_table B
            ON A.material_mode=B.material_mode
            ) T GROUP BY bundling_number,stock_location,information_sources ) T1
        ) F ON A.bundling_number = F.bundling_number
            AND F.stock_location = E.city AND A.information_sources=F.information_sources
        LEFT JOIN reservoir_area_stock G ON A.material_mode = G.sap_no
            AND G.city = E.city
        LEFT JOIN (
            SELECT bom_total_table.material_mode,{addr_case}
            FROM (SELECT * FROM (SELECT
                CASE WHEN b2.bundling_number IS NOT NULL THEN b3.material_mode
                     WHEN b2.bundling_number IS NULL THEN b1.material_mode
                END AS material_mode
                FROM bom_total_table b1 LEFT JOIN bundling_part_number b2
                ON b1.material_mode = b2.material_mode
                LEFT JOIN bundling_part_number b3 on b2.bundling_number=b3.bundling_number
                GROUP BY b1.material_mode,b3.material_mode,b2.bundling_number) T GROUP BY material_mode) bom_total_table
            LEFT JOIN kunpeng_daily ON kunpeng_daily.material_code=bom_total_table.material_mode
                AND stock_category!='借用在途库'
            GROUP BY material_mode ) H ON A.material_mode = H.material_mode
        LEFT JOIN purchasing_transit I ON A.material_mode = I.material_mode
        LEFT JOIN dump_transit J ON A.material_mode = J.sap_no
        LEFT JOIN rma_transit K ON A.material_mode = K.material_code
        LEFT JOIN reject_ratio M ON A.material_mode = M.sap_no
        LEFT JOIN reservoir_area_stock L ON A.material_mode = L.sap_no AND L.city='武汉'
        GROUP BY A.information_sources,A.bundling_number,B.NAME,B.product_category3,B.spare_parts_category,C.total_usage
            ,E.city,F.sales) T
    LEFT JOIN
        (SELECT information_sources,bundling_number,sum(gap_quantity) sum_each_gap
        FROM
        (SELECT T.information_sources,bundling_number,city,
            (T.stock_quantity-T.reserve_quantity) AS gap_quantity FROM
        (SELECT A.information_sources,A.bundling_number,E.city,
            round(sum(COALESCE(theoretical_defect_rate,0))::numeric
                / NULLIF(count(A.bundling_number), 0)::numeric, 8) AS theoretical_defect_rate, F.sales,
            CASE
                WHEN round(sum(COALESCE(theoretical_defect_rate,0))::numeric
                    / NULLIF(count(A.bundling_number), 0)::numeric, 8) IS NULL THEN NULL
                WHEN sales * round(sum(COALESCE(theoretical_defect_rate,0))::numeric
                    / NULLIF(count(A.bundling_number), 0)::numeric, 8)::FLOAT >= 8 THEN
                    ceil(( sales * round(sum(COALESCE(theoretical_defect_rate,0))::numeric
                    / NULLIF(count(A.bundling_number), 0)::numeric, 8)::FLOAT / 4)::numeric)
                WHEN sales * round(sum(COALESCE(theoretical_defect_rate,0))::numeric
                    / NULLIF(count(A.bundling_number), 0)::numeric, 8)::FLOAT < 8
                    AND sales * round(sum(COALESCE(theoretical_defect_rate,0))::numeric
                    / NULLIF(count(A.bundling_number), 0)::numeric, 8)::FLOAT > 1 THEN 2
                WHEN sales * round(sum(COALESCE(theoretical_defect_rate,0))::numeric
                    / NULLIF(count(A.bundling_number), 0)::numeric, 8)::FLOAT <= 1
                    AND sales * round(sum(COALESCE(theoretical_defect_rate,0))::numeric
                    / NULLIF(count(A.bundling_number), 0)::numeric, 8)::FLOAT > 0 THEN 1
                WHEN sales * round(sum(COALESCE(theoretical_defect_rate,0))::numeric
                    / NULLIF(count(A.bundling_number), 0)::numeric, 8)::FLOAT = 0 THEN 0
                ELSE 0
            END AS reserve_quantity,
            COALESCE(sum(G.num),0) as stock_quantity
        FROM
        (
            SELECT A.information_sources,B.material_mode,B.bundling_number
            FROM (SELECT bom_total_table.* FROM
                bom_total_table INNER JOIN bundling_part_number
                ON bom_total_table.material_mode=bundling_part_number.material_mode) A
            LEFT JOIN bundling_part_number B on A.bundling_number=B.bundling_number
            GROUP BY A.information_sources,B.material_mode,B.bundling_number
        ) A
        LEFT JOIN reject_ratio D ON A.material_mode = D.sap_no
        LEFT JOIN (SELECT * FROM (VALUES {city_case}) as t(city)) E ON 1 = 1
        LEFT JOIN (
            SELECT T1.* FROM (SELECT T.bundling_number, sum(sales) sales, stock_location,information_sources FROM (
            SELECT A.bundling_number,sum_count sales,
            CASE WHEN stock_location like '武汉' THEN '武汉项目'
            ELSE stock_location
            END AS stock_location,information_sources
            FROM bundling_part_number A INNER JOIN bom_total_table B
            ON A.material_mode=B.material_mode
            ) T GROUP BY bundling_number,stock_location,information_sources ) T1
        ) F ON A.bundling_number = F.bundling_number
            AND F.stock_location = E.city AND A.information_sources=F.information_sources
        LEFT JOIN reservoir_area_stock G ON A.material_mode = G.sap_no
            AND G.city = E.city
        GROUP BY A.bundling_number,E.city,F.sales,A.information_sources) T)
        T GROUP BY bundling_number,information_sources) H
    ON T.bundling_number=H.bundling_number AND T.information_sources=H.information_sources
    '''

    sql = search_sql + base_sql

    # PO与存量模式：通过字符串替换去掉 information_sources 维度（与原始代码替换逻辑完全一致）
    if is_po_mode:
        sql = sql.replace('T.information_sources,', '')
        sql = sql.replace('A.information_sources,', '')
        sql = sql.replace(',A.information_sources', '')
        sql = sql.replace('AND A.information_sources=C.information_sources', '')
        sql = sql.replace('AND A.information_sources=F.information_sources', '')
        sql = sql.replace('AND T.information_sources=H.information_sources', '')
        sql = sql.replace(',information_sources', '')
        sql = sql.replace('information_sources,', '')
        sql = sql.replace(',B.information_sources', '')
        sql = sql.replace(',T.information_sources', '')

    return sql
