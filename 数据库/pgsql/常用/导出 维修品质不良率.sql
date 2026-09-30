SELECT
	proj_name_sn AS "项目名称_溯源",
	crm_no_sn AS "CRM立项编号",
	wldm AS "故障件物料号",
	wlms AS "物料描述",
	wlmc AS "故障件名称",
	xsnf AS "销售年份",
	xl AS "销量",
	bxsl AS "报修数量",
	sjgh AS "实际更换",
	sjfc AS "实际返厂",
	jzbl AS "介质保留",
	wfxgz AS "未复现故障",
	sjgz AS "实际故障",
	sjbll AS "实际不良率",
	hardware_rate AS "硬件更换不良率",
	gysllbll AS "供应商理论不良率",
	blbd AS "不良比对"
from supply_defect_rate
WHERE 
	crm_no_sn IN ()
	AND wldm IN ()
AND xsnf != '汇总'

UNION ALL

SELECT
	proj_name_sn AS "项目名称_溯源",
	crm_no_sn AS "CRM立项编号",
	wldm AS "故障件物料号",
	wlms AS "物料描述",
	wlmc AS "故障件名称",
	xsnf AS "销售年份",
	xl AS "销量",
	bxsl AS "报修数量",
	sjgh AS "实际更换",
	sjfc AS "实际返厂",
	jzbl AS "介质保留",
	wfxgz AS "未复现故障",
	sjgz AS "实际故障",
	sjbll AS "实际不良率",
	hardware_rate AS "硬件更换不良率",
	gysllbll AS "供应商理论不良率",
	blbd AS "不良比对"
from supply_defect_rate
WHERE 
	crm_no_sn is NULL
	and flag = '1'
	AND wldm IN ('302-000543', '302-000793', '302-001631', '302-001644')
	AND xsnf is NULL
ORDER BY "CRM立项编号"

