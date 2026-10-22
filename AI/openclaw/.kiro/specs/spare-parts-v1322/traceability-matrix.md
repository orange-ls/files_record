# 需求 → 代码追溯矩阵

## 模块信息
- 模块名称：xc_spare_parts
- Spec目录：spare-parts-v1322
- 更新日期：2025-07-14

## 追溯记录

| 需求ID | 任务ID | 实现文件 | 函数/类 | 变更类型 | 说明 |
|--------|--------|----------|---------|----------|------|
| REQ-1.1 | TASK-2.1 | models/purchase_order_inventory.py | PurchaseOrdersInventory.industry_area | 新增 | 新增"项目所属行业/区域"ORM字段 |
| REQ-1.1, REQ-1.2 | TASK-2.2 | models/purchase_order_inventory.py | PurchaseOrdersInventory.excel_import | 修改 | 列数校验从16改为17 |
| REQ-1.1 | TASK-2.3 | models/purchase_order_inventory.py | PurchaseOrdersInventory.get_excel_data | 修改 | 处理第17列（索引16）industry_area，允许为空 |
| REQ-1.1 | TASK-2.4 | models/purchase_order_inventory.py | PurchaseOrdersInventory.excel_import | 修改 | INSERT SQL新增industry_area字段及ON CONFLICT更新 |
| REQ-1.1 | TASK-2.5 | models/purchase_order_inventory.py | PurchaseOrdersInventory.excel_export | 修改 | sheet_fields和导出数据新增"项目所属行业/区域" |
| REQ-1.1 | TASK-2.6 | views/purchasing_order_inventory_views.xml | tree视图 + search视图 | 修改 | 新增industry_area字段展示和搜索 |
| REQ-1.3 | TASK-3.1 | models/bom_total_table.py | BomTotalTable.industry_area | 新增 | BOM总表新增"项目所属行业/区域"ORM字段 |
| REQ-1.4 | TASK-3.2 | models/bom_total_table.py | BomTotalTable.refresh_bom_total | 修改 | sql_v2查询追加industry_area字段 |
| REQ-1.4, REQ-1.5, REQ-1.6 | TASK-3.3 | models/bom_total_table.py | BomTotalTable.refresh_bom_total | 修改 | industry_area三级回退逻辑：溯源系统→PO与存量表→空字符串 |
| REQ-5.1, REQ-5.2, REQ-5.3, REQ-5.4 | TASK-3.4 | models/bom_total_table.py | BomTotalTable.refresh_bom_total | 修改 | CRM立项编号三级回退策略替换原有逻辑 |
| REQ-1.3 | TASK-3.5 | models/bom_total_table.py | BomTotalTable.refresh_bom_total | 修改 | INSERT SQL及bins_dict/result_list新增industry_area |
| REQ-1.3 | TASK-3.6 | views/bom_total_table_views.xml | tree视图 + search视图 | 修改 | 新增industry_area字段展示和搜索 |
| REQ-1.3 | TASK-3.7 | models/bom_total_table.py | BomTotalTable.excel_export | 修改 | sheet_fields和导出数据新增"项目所属行业/区域" |
| REQ-2.1, REQ-2.2, REQ-2.3 | TASK-5.1 | models/prepare_materials.py | PrepareMaterials.search_sql | 修改 | addr_case移除factory_code限定，仅按stock_address汇总所有工厂库存 |
| REQ-2.4 | TASK-5.2 | models/alternative_prepare_materials.py | AternativePrepareMaterials.search_sql | 修改 | addr_case移除factory_code限定，仅按stock_address汇总所有工厂库存 |
| REQ-3.1, REQ-3.3 | TASK-6.1 | models/prepare_materials.py | PrepareMaterials.search_sql | 修改 | city_case构建增加whbj过滤条件 |
| REQ-3.2, REQ-3.4 | TASK-6.2 | models/alternative_prepare_materials.py | AternativePrepareMaterials.search_sql | 修改 | city_case构建增加whbj过滤条件 |
| REQ-6.1, REQ-6.2, REQ-6.3 | TASK-8.1 | models/inventory_query.py | InventoryQuery.sync_inventory | 修改 | conn初始化为None，增加连接安全检查，finally块条件关闭 |
| REQ-4.1~4.9 | TASK-7.1 | models/other_reservoir_area_stock.py | stock_params（模块级配置） | 修改 | 删除5条旧映射，保留武汉测试仓，新增8条库区映射 |
| REQ-4.10 | TASK-7.2 | models/other_reservoir_area_stock.py | sheet_fields, city_fields（模块级配置） | 修改 | 同步更新城市名称列表，与stock_params保持一致 |
