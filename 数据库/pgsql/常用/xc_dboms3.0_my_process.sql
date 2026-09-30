						WITH my_pro_info AS(
                SELECT
                    dis.id as jump_id,
                    dis.distribution_no AS business_no,
                    inf.price_apply_no,
                    inf.price_apply_type,
                    inf.crm_project_no,
                    inf.project_no,
                    inf.project_name,
                    inf.sales,
                    inf.industry
                FROM
                    xc_project_distribution dis
                    LEFT JOIN xc_project_info inf ON dis.project_id = inf.ID
                UNION
                SELECT
                    ord.id as jump_id,
                    ord.sales_order_no AS business_no,
                    inf.price_apply_no,
                    inf.price_apply_type,
                    inf.crm_project_no,
                    inf.project_no,
                    inf.project_name,
                    inf.sales,
                    inf.industry 
                FROM
                    xc_sales_order ord
                    LEFT JOIN xc_project_info inf ON ord.project_id = inf.ID
                UNION
                SELECT
                    xsdn.sales_order_id as jump_id,
                    xsdn.delivery_note_no AS business_no,
                    inf.price_apply_no,
                    inf.price_apply_type,
                    inf.crm_project_no,
                    inf.project_no,
                    inf.project_name,
                    inf.sales,
                    inf.industry 
                FROM
                    xc_sales_delivery_note xsdn
                    LEFT JOIN xc_project_info inf ON xsdn.project_id = inf.ID
            ),
            xdf AS(
            SELECT
                CASE dboms_flowable_type
                    WHEN 'distribution_audit' THEN '分货审批'
                    WHEN 'zke_sales_order_audit' THEN 'ZKE-售出确收订单审批'
                    WHEN 'zkey_delivery_note_audit' THEN 'ZKEY-触发交货单审批'
										WHEN 'sales_order_audit' THEN '创建销售订单'
										WHEN 'zkaa_sales_order_audit' THEN '回货审批'
                    ELSE ''
                END AS flowable_type,
                CASE business_type
                    WHEN 'project_distribution' THEN project_distribution_no
                    WHEN 'sales_order' THEN sales_order_no
                    ELSE sales_delivery_note_no
                END AS business_no,
                current_spr,
                approved_spr,
                xc_dboms_flowable.create_uid,
                is_delete,
								bpmn_task.write_date
            FROM
                xc_dboms_flowable
								LEFT JOIN bpmn_task ON xc_dboms_flowable.id = bpmn_task.business_flowable_id
            )
            
            SELECT
                ROW_NUMBER() OVER (ORDER BY 1) AS id,
                mpi.jump_id,
                xdf.flowable_type,
                xdf.business_no AS no,
                xdf.current_spr,
                xdf.approved_spr,
                ru.login,
                rp.name AS submit_spr,
                mpi.price_apply_no,
                mpi.price_apply_type,
                mpi.crm_project_no,
                mpi.project_no,
                mpi.project_name,
                mpi.sales,
                mpi.industry
            FROM
                xdf
                JOIN res_users ru ON xdf.create_uid = ru.id
                JOIN res_partner rp ON ru.partner_id = rp.id
                JOIN my_pro_info mpi ON xdf.business_no = mpi.business_no
            WHERE
                xdf.is_delete = 0
						ORDER BY
								xdf.write_date DESC







SELECT
	CASE business_type
			WHEN 'project_distribution' THEN '分货审批'
			WHEN 'sales_order' THEN '确收审批'
			WHEN 'sales_delivery_note' THEN '销售交货单'
			ELSE ''
	END AS flowable_type,
	CASE business_type
		WHEN 'project_distribution' THEN project_distribution_no
		WHEN 'sales_order' THEN sales_order_no
		ELSE sales_delivery_note_no
	END AS business_no,
	current_spr,
	approved_spr
FROM
	xc_dboms_flowable
	


SELECT
	CASE 
		WHEN business_type='0' THEN project_distribution
		WHEN business_type='1' THEN sales_order
		WHEN business_type='3' THEN sales_delivery_note
		ELSE ''
	END AS business_no
FROM
	xc_dboms_flowable







WITH my_pro_info AS(
	SELECT
		dis.distribution_no AS business_no,
		inf.price_apply_no,
		inf.price_apply_type,
		inf.crm_project_no,
		inf.project_no,
		inf.project_name,
		inf.sales,
		inf.industry 
	FROM
		xc_project_distribution dis
		LEFT JOIN xc_project_info inf ON dis.project_id = inf.ID
	UNION
	SELECT
		ord.sales_order_no AS business_no,
		inf.price_apply_no,
		inf.price_apply_type,
		inf.crm_project_no,
		inf.project_no,
		inf.project_name,
		inf.sales,
		inf.industry 
	FROM
		xc_sales_order ord
		LEFT JOIN xc_project_info inf ON ord.project_id = inf.ID
)

SELECT
	CASE 
			WHEN xdf.name LIKE 'XMFH%' THEN '分货审批'
			WHEN xdf.name LIKE 'XSDD%' THEN '确收审批'
			ELSE '其他'
		END AS flowable_type,
	xdf.business_no AS NO,
	xdf.audit_status,
	xdf.current_spr,
	xdf.approved_spr,
	ru.login,
	rp.NAME AS submit_spr,
	mpi.price_apply_no,
	mpi.price_apply_type,
	mpi.crm_project_no,
	mpi.project_no,
	mpi.project_name,
	mpi.sales,
	mpi.industry
FROM
	xc_dboms_flowable xdf
	JOIN res_users ru ON xdf.create_uid = ru.ID
	JOIN res_partner rp ON ru.partner_id = rp.ID
	JOIN my_pro_info mpi ON xdf.business_no = mpi.business_no
WHERE
	is_delete = 0



	
	
	

	