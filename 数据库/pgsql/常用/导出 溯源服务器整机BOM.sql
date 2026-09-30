SELECT
    unique_id            AS "系统编号",
    delivery_no          AS "交货单号",
    complete_sn          AS "整机SN",
    service_start_time   AS "服务开始时间",
    service_end_time     AS "服务结束时间",
    service_product_type AS "服务产品类别",
    customer_name        AS "签约客户名称",
    proj_name            AS "项目名称",
    crm_no               AS "CRM立项编号",
    customer_level       AS "客户等级",
    material_supplier    AS "物料供应商",
    material_code        AS "物料代码",
    material_desc        AS "物料描述",
    bom_sn               AS "BOM组件SN",
    sale                 AS "销售员",
    purchase_time        AS "采购时间",
    province             AS "所在省份",
    city                 AS "所在城市",
    delivery_address     AS "交付地址",
    deliver_time         AS "产品交付时间",
    material_num         AS "物料数量",
    is_add               AS "是否项目增配",
    add_proj_name        AS "增配整机项目名",
    model                AS "机型",
    add_crm_no           AS "增配整机CRM立项编号",
    remark               AS "备注",
    sales_order_type     AS "销售单类型",
    del_flag             AS "删除标识",
    push_flag            AS "推送标识",
    sales                AS "项目审批一线工程师",
    write_flag           AS "数据来源标识",
    complete_unique_id   AS "关联整机编号",
    create_uid           AS "创建人",
    create_date          AS "创建时间",
    write_uid            AS "最后修改人",
    write_date           AS "修改时间"
FROM
    sn_service_bom_info
WHERE 
	complete_sn IN (
'KS001410Q822000006', 'KS001410Q822000022', 'KS001410QA31100004', 'KS001410Q822000017', 'KS001410Q822000012', 'KS001410Q822000021', 'KS001410Q822000013', 'KS001410Q822000005', 'KS001410QA31100001', 'KS001410Q822000009', 'KS001410Q822000020', 'KS001410Q822000023', 'KS001410Q822000011', 'KS001410Q822000028', 'KS001410QA31100002', 'KS001410Q822000016', 'KS001410Q822000007', 'KS001410Q822000003', 'KS001410Q822000014', 'KS001410Q822000015', 'KS001410Q822000018', 'KS001410Q822000025', 'KS001410Q822000024', 'KS001410QA31100003', 'KS001410Q822000029', 'KS001410Q822000010', 'KS001410Q822000008', 'KS001410Q822000019', 'KS001410Q822000004', 'KS001410Q822000001', 'KS001410Q822000002'
	)




