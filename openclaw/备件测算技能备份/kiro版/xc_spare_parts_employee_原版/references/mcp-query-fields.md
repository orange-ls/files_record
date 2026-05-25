# MCP SQL 查询各表返回字段定义

查询每个表时，SELECT 的字段和顺序必须严格按照以下定义，不要自己选字段、不要改顺序、不要省略。
格式：`数据库字段名 → 中文列名`，按顺序排列。

---

## bom_total_table（BOM总表）

proj_name→项目名, server_desc→服务描述, server_aging→服务时效, delivery_location→交付地点, stock_location→库存地点, material_mode→物料代码, material_desc→物料描述, sum_count→总数量, spare_parts_type→产品Ⅱ级分类, information_sources→信息来源, proj_number→CRM立项编号, sale→销售员, remark→备注, write_time→更新日期, bundling_number→捆绑料号, server_stare_time→服务开始时间, server_end_time→服务结束时间, product_category3→产品Ⅲ级分类, spare_parts_category→备件大类

## base_material（物料基础数据）

material_code→物料代码, material_desc→物料描述, supplier_pn→供应商PN码, name→产品Ⅱ级分类, product_category3→产品Ⅲ级分类, bundling_number→捆绑料号, remark→备注, spare_parts_category→备件大类

## purchasing_transit（采购在途）

material_mode→物料代码, material_desc→物料描述, "supplier_PN"→供应商PN码, name→产品Ⅱ级分类, product_category3→产品Ⅲ级分类, num→数量, bundling_number→捆绑料号

## dump_transit（转储在途）

sap_no→物料代码, material_desc→物料描述, supplier_pn→供应商PN码, material_type→产品Ⅱ级分类, product_category3→产品Ⅲ级分类, material_num→数量, bundling_number→捆绑料号

## rma_transit（RMA在途）

material_code→物料代码, material_desc→物料描述, supplier_pn→供应商PN码, name→产品Ⅱ级分类, product_category3→产品Ⅲ级分类, quantity→数量, bundling_number→捆绑料号

## reject_ratio（不良率）

sap_no→物料代码, material_desc→物料描述, material_type→产品Ⅱ级分类, product_category3→产品Ⅲ级分类, theoretical_defect_rate→理论不良率, bundling_number→捆绑料号

## kunpeng_daily（鲲鹏日报）

service_scope_code→业务范围代码, service_category→业务类型, factory_code→工厂代码, factory_category→工厂类型, bundling_number→捆绑料号, material_code→物料代码, material_desc→中文物料名称, batch_code→批次代码, material_category_name→物料类型名称, material_group_name→物料组名称, stock_category→库存地分类, stock_address→库存地代码, stock_name→库存地名称, stock_quantity→实际库存数量

## material_bom（物料BOM）

material_code→物料代码, assembly→下级组件, bom_assembly→下级BOM组件描述, product_category2→产品Ⅱ级分类, product_category3→产品Ⅲ级分类, bom_quantity→BOM数量

## bundling_part_number（捆绑料号）

bundling_number→捆绑料号, material_mode→物料代码, material_desc→物料描述, product_category2→产品Ⅱ级分类, product_category3→产品Ⅲ级分类

## non_electronic_materials（非电子物料）

material_mode→物料代码, material_desc→物料描述, product_category2→产品Ⅱ级分类, product_category3→产品Ⅲ级分类

## material_transformation（物料转换）

sap_69_no→转换前物料代码, sap_302_no→转换后物料代码, material_desc→物料描述, product_category2→产品Ⅱ级分类, product_category3→产品Ⅲ级分类

## purchase_order_inventory（PO单与存量）

proj_name→项目名, server_desc→服务描述, server_aging→服务时效, delivery_location→交付地点, stock_location→库存地点, material_mode→物料代码, material_desc→物料描述, sum→总数量, spare_parts_category→备件大类, spare_parts_type→产品Ⅱ级分类, information_sources→信息来源, proj_number→立项编号, sale→销售员, remark→备注, write_date→更新日期, product_category3→产品Ⅲ级分类

## material_stock_order（400派件补库单）

is_replenished→是否补库(CASE:'0'→否,'1'→是), cust_num→WMS外部单据号, dispatch_date→派件日期, material_code→料号, description→描述, name→产品Ⅱ级分类, product_category3→产品Ⅲ级分类, material_attribute→物料属性, outgoing_warehouse→出库库房简称, dispatch_quantity→发货数量, bundled_material_code→捆绑料号, replenishment_status→补库单状态(CASE:'0'→Closed,'1'→Ongoing,'2'→Cancel,'3'→Dely), replenishment_date→补库日期, today_material_stock→今日补料库存数量, remaining_stock_quantity→出库库房剩余库存数量, wuhan_stock_quantity_today→今日武汉库存数量, recommended_replenishment_code→推荐补库料号, remark→备注, project→项目, crm_project_code→CRM立项编号, crm_work_order→CRM工单号, replacement_order→换件单号

## compute_proj_apply（计算产品备货申请）

proj_name→项目名, service_desc→服务描述, service_time→服务时效, del_address→交付地点, stock_address→库存地点, material_code→物料代码, material_desc→物料描述, number→总数量, from_info→信息来源, crm_no→立项编号, sales→销售员, remark→备注, update_date→更新日期, bundling_code→捆绑料号, stock_gs→公司库存数量, stock_wh→WHBJ库存数量

## warehouse_allocation（库区分配表）

prod_line→产品线, deliver_addr→交付地点, proj_ageing→项目时效, dispatch_spare_parts→派单备件库

## replenishment_order（本地库存查询）

import_date→导入日期, material_code→料号, description→描述, spare_parts_category→备件大类, remark→备注, warehouse→库房, quantity→数量, bundling_code→捆绑料号, replenishment_status→补库状态, issue_date→发料日期, remaining_stock_quantity→库房剩余数量, gap_quantity→缺口, wuhan_stock_quantity_today→当前武汉库存, today_material_stock→原料号武汉库存, recommended_replenishment_code→推荐补料料号, part_category→产品Ⅱ级分类, product_category3→产品Ⅲ级分类, proj_name→项目名称, crm_number→CRM立项编号, verify_stock→校验库房, verify_bundling→校验捆绑料号

## reservoir_area_stock（各库区库存）

需要行转列，字段顺序：sap_no→物料代码, bundling_number→捆绑料号, material_desc→物料描述, supplier_pn→供应商PN码, spare_parts_category→备件大类, material_type→产品Ⅱ级分类, product_category3→产品Ⅲ级分类, 然后是45个城市列。
具体行转列 SQL 生成规则见 sql-generation-rules.md。

## other_reservoir_area_stock（其他库区库存）

结构同 reservoir_area_stock，但城市列为60+个特殊库区（如"北京民生银行"、"武汉借用仓"等）。
行转列方式相同。

## prepare_materials（备料总表）

实时计算表，字段顺序：bundling_number→捆绑料号, material_code→物料代码, material_desc→物料描述, supplier_pn→供应商PN码, name→产品Ⅱ级分类, total_usage→总使用量, theo_non_rate→理论不良率, city→城市, sales→销量, reserve_quantity→备货量, stock_quantity→库存量, gap_quantity→缺口, wuhan_stock_quantity→武汉库存量, stock_alert_status→库存预警, sum_each_gap→各库区总缺口, final_gap→最终缺口, XC02_quantity→XC02库存, XC16_quantity→XC16库存, XC17_quantity→XC17库存, purchase_in_transit→采购在途, dump_in_transit→转储在途, rma_in_transit→RMA在途, product_category3→产品Ⅲ级分类。
具体计算 SQL 生成规则见 sql-generation-rules.md 和 business-formulas.md。

## alternative_prepare_materials（替代料备料总表）

实时计算表，字段顺序：bundling_number→捆绑料号, name→产品Ⅱ级分类, total_usage→总使用量, theo_non_rate→理论不良率, city→城市, sales→销量, reserve_quantity→备货量, stock_quantity→库存量, gap_quantity→缺口, wuhan_stock_quantity→武汉库存量, stock_alert_status→库存预警, sum_each_gap→各库区总缺口, final_gap→最终缺口, purchase_in_transit→采购在途, dump_in_transit→转储在途, rma_in_transit→RMA在途, product_category3→产品Ⅲ级分类。
计算逻辑与 prepare_materials 类似，但以捆绑料号为维度聚合。

## summary_kanban（汇总看板）

proj_name→项目名, server_aging→服务时效, delivery_location→交付地点, stock_location→库存地点, material_code→物料代码, bundling_number→捆绑料号, material_desc→物料描述, spare_parts_category→备件大类, material_name→产品Ⅱ级分类, product_category3→产品Ⅲ级分类, sum_count→总数量, reserve_quantity→备货量, stock_total→库存量, gap_quantity→缺口, wuhan_stock_quantity→武汉库存量, gap_total→最终缺口, purchase_in_transit→采购在途, dump_in_transit→转储在途, rma_in_transit→RMA在途, xc_02→XC02, xc_16→XC16, xc_17→XC17, has_media_retention→是否介质保留, information_sources→信息来源, proj_number→CRM立项编号, server_stare_time→服务开始时间, server_end_time→服务结束时间, sale→销售员, remark→备注

## material_shortage（欠料调拨总表）

material_code→物料代码, bundling_number→捆绑料号, material_description→物料描述, spare_parts_category→备件大类, name→产品Ⅱ级分类, shortage_city→欠料城市, shortage_qty→欠料数量, transfer_city→调拨城市, transfer_city_stock→调拨城市库存, service_lead_time→服务时效, sales_qty→销售数量, wuhan_main_stock→武汉总库库存, region_l1_stock→区域L1库, region_first_level_stock→区域一级库库存, planner_remark→计划员备注, product_category3→产品Ⅲ级分类, import_flag→导入标记

## production_stock（生产系统PO单）

sap_no→转换后物料代码, bundle→捆绑, config_description→配置描述, product_category2→产品Ⅱ级分类, product_category3→产品Ⅲ级分类, total_qty→转换总数量, wuhan_stock→武汉库存量, final_gap→最终缺口, service_lead_time→服务时效, whbj_num→WHBJ库存量, transit_transfer→转储在途, transit_rma→RMA在途, transit_purchase→采购在途, raw_material_wuhan_stock→原料号武汉库存, company_stock_qty→公司库存数量, warehouse→库房, warehouse_qty→库存数量

## production_batch_detail（生产批次明细）

batch_time→批次时间, batch_no→触发生产批次号, crm_no→CRM立项编号, proj_name→项目名称, config_transfer_sap_no→转换后物料代码, config_transfer_spec→转换后描述, product_category2→产品Ⅱ级分类, product_category3→产品Ⅲ级分类, config_transfer_num→数量, bundle→捆绑, service_lead_time→服务时效, config_no→ConfigNO, industry→行业, delivery_date→预计交货日期, process_status→流程状态, sale→销售, pre_sale→售前, remark→备注

## week_estimates（本周项目测算）

实时计算表，字段顺序：material_code→物料代码, bundling_number→捆绑料号, material_desc→描述, spare_parts_category→备件大类, name→产品Ⅱ级分类, product_category3→产品Ⅲ级分类, city→城市, sales→销量, reserve_quantity→备货量, stock_quantity→库存量, gap_quantity→缺口, wuhan_stock_quantity→武汉库存量, final_gap→总缺口, purchase_in_transit→采购在途, dump_in_transit→转储在途, rma_in_transit→RMA在途, write_date→更新日期

## network_spare_trs（网络产品测算）

实时计算表，字段顺序：material_code→物料代码, material_desc→中文描述, material_team→物料组描述, sales_num→销量, one_three_rate→预估第1-3年不良率, apply_num→预估备货量, service_stock→服务中心库存, dcn_stock→DCN库存

## factory_material_list（工厂物料清单）

sap_no→物料代码, industry_standard_desc→工业标准描述, material_desc→物料描述, product_category2→产品Ⅱ级分类, product_category3→产品Ⅲ级分类

## scene_project_table（现场备件项目对应表）

scene_name→现场名称, project_name→项目名称, city→城市

## crm_city_id（CRM市级ID）

city_name→城市名称, city_id→城市ID

## crm_table（crm数据表）

字段结构同 bom_total_table，额外包含 WMS 对接字段（preferred_store→首选库, address_code→首选库存地编码, storeroom_code→首选库房编码, wms_alternative_store→备选库, alternative_store_code→备选库编码, alternative_store_area_code→备选库存地编码, stock_location_id→库存地ID, wms_storeroom_id→WMS库房ID）

## extend_warranty_bom_table（延保项目BOM总表）

字段结构同 bom_total_table

## spare_parts_labor_cost（备件&ASP上门成本）

查询时参考 database-schema.md 中的字段定义

## version_ctrl_customization（版本管控&定制化）

查询时参考 database-schema.md 中的字段定义

## wms_storeroom_table（WMS库房分配表）

address→库存地, alternative_store→备选库, regional_first_store→区域一级库

## purchase_order_inventory_new（溯源PO单）

字段结构同 purchase_order_inventory

## inventory_query（SAP库存查询）

material_code→物料代码, material_desc→物料描述, supplier_pn→供应商PN码, material_name→产品Ⅱ级分类, apply_factory→申请工厂, apply_location→申请库位, stock_num→库存数量, apply_num→申请转储数量, estimate_price→预估单价, estimate_spare_price→预估备件金额, advice→批复建议, project_name→项目名, bind_material_code→捆绑料号, wuhan_stock_quantity→武汉库存数量, final_gap→最终缺口, dump_in_transit→转储在途, rma→RMA在途, pur→采购在途
