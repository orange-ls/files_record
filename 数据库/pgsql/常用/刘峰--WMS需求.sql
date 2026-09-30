-- K3_im
SELECT 
	'出库单' AS type,
	cust_order_id_list,
	house_name,
	CASE post_status
		WHEN '0010' THEN '未过账'
		WHEN '0015' THEN '待过账'
		WHEN '0020' THEN '部分过账'
		ELSE post_status
	END post_status,
	create_time
FROM `wm_do`
WHERE create_time BETWEEN '2026-07-04' AND '2026-08-04'
	AND post_status IN ('0010', '0015', '0020')
	AND status = '0'
	AND ordertype_name = '备件库间转储出库单'


-- K3_im
SELECT 
	'入库单' AS type,
	cust_order_id,
	house_name,
	CASE post_status
		WHEN '0010' THEN '未过账'
		WHEN '0015' THEN '待过账'
		WHEN '0020' THEN '部分过账'
		ELSE post_status
	END post_status,
	create_time
FROM `wm_po`
WHERE create_time BETWEEN '2026-07-01' AND '2026-08-01'
	AND post_status IN ('0010', '0015', '0020')
	AND status = '0'
	AND type_name = '备件库间转储入库单'
	

-- k3_repair
SELECT 
	'申请单' AS type,
	ref_order_no,
	house_name,
	'已创建' order_status,
	create_time
FROM `od_apply`
WHERE create_time BETWEEN '2026-02-04' AND '2026-08-04'
	AND order_status = 'create'
	AND ynflag  = '1'


-- k3_repair
SELECT 
	'换件单' AS type,
	ref_order_no,
	house_name,
	CASE status
		WHEN 'create' THEN '已创建'
		WHEN 'readyToSend' THEN '备件待发货'
		ELSE status
	END status,
	create_time
FROM `od_replace`
WHERE create_time BETWEEN '2026-02-04' AND '2026-08-04'
	AND `status` IN ('create', 'readyToSend')
	AND ynflag  = '1'
UNION ALL
SELECT 
	'换件单' AS type,
	ref_order_no,
	house_name,
	'备件已发货' status,
	create_time
FROM `od_replace`
WHERE create_time BETWEEN '2026-02-03' AND '2026-08-03'
	AND `status` = 'alreadySend'
	AND ynflag  = '1'
UNION ALL
SELECT 
	'换件单' AS type,
	ref_order_no,
	house_name,
	'备件已发货' status,
	create_time
FROM `od_replace`
WHERE create_time BETWEEN '2026-02-04' AND '2026-08-04'
	AND `status` = 'replacing'
	AND signed_time is NULL
	AND ynflag  = '1'