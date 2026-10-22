# 数据库表结构完整定义

本文件定义了备件测算系统所有数据表的结构、字段含义、表间关系。
表的中文名来自源码 `_description`，字段中文名来自 `fields.Char(string='xxx')`。
生成任何 SQL 前必须先查阅本文件，确认涉及的表名、字段名、数据类型。

---

## 一、表清单与数据量

| 表名 | 中文名（源码_description） | 数据量 | 说明 |
|---|---|---|---|
| base_material | 物料基础数据 | ~7200 | 所有物料的主数据，其他表通过物料代码关联到此表获取描述和分类 |
| bom_total_table | BOM总表 | ~14.4万 | 核心业务表，记录每个项目在每个城市需要的每种物料的BOM展开后数量 |
| bundling_part_number | 捆绑料号 | ~1250 | 物料代码→捆绑料号映射，一个捆绑料号可对应多个物料代码 |
| purchasing_transit | 采购在途 | ~80 | 已下采购订单但尚未到货入库的物料及数量 |
| dump_transit | 转储在途 | ~190 | 已发起库间转储但尚未到达目标库的物料及数量 |
| rma_transit | RMA在途 | ~120 | 已送修但尚未返回的物料及数量，数据来自WMS的RMA库存地 |
| reject_ratio | 不良率 | ~1940 | 每种物料的理论故障率，用于计算备货量和库存预警 |
| reservoir_area_stock | 各库区库存 | ~1.3万 | 每行=一个物料在一个城市的库存数量（行存储），系统展示时行转列为45城市列 |
| kunpeng_daily | 鲲鹏日报 | ~1.3万 | 从Oracle BI视图同步的库存明细，按工厂+库存地+物料+批次粒度存储 |
| material_bom | 物料BOM | ~2270 | BOM父子结构表，material_code是父物料，assembly是子物料，支持递归展开 |
| material_stock_order | 400派件补库单 | ~1.6万 | WMS备件出库后的派件记录和补库状态跟踪 |
| compute_proj_apply | 计算产品备货申请 | 动态 | 从PO通知单计算的备货申请，只保留库存不足需要备货的记录 |
| inventory_query | SAP库存查询 | 少量 | SAP库存查询结果缓存，包含预估单价和备件金额 |
| non_electronic_materials | 非电子物料 | ~1140 | 非电子物料清单，BOM展开时需要过滤掉这些物料 |
| material_transformation | 物料转换 | ~260 | 69码→302码的物料代码映射，BOM展开时用于替换旧物料代码 |
| other_reservoir_area_stock | 其他库区库存 | ~2240 | 项目现场仓等其他库区的库存，结构同reservoir_area_stock |
| purchase_order_inventory | PO单与存量 | ~10万 | PO单与存量原始数据，是BOM总表的数据源 |
| warehouse_allocation | 库区分配表 | ~710 | 交付地点+项目时效→派单备件库城市的映射规则 |
| prepare_materials | 备料总表 | 0（实时计算） | 空表，数据由200+行SQL实时关联8张表计算，含备货量/缺口/预警 |
| alternative_prepare_materials | 替代料备料总表 | 0（实时计算） | 空表，按捆绑料号聚合的备料数据，不良率取捆绑料号下所有物料平均值 |
| week_estimates | 本周项目测算 | 0（实时计算） | 空表，筛选本周新增项目（write_time在本周范围内且销量>0）的测算数据 |
| summary_kanban | 汇总看板 | ~13.7万 | 按项目+物料+城市维度汇总BOM数量和备料信息的看板数据，刷新时从BOM总表聚合并关联备料计算 |
| network_spare_trs | 网络产品测算 | 少量 | 网络产品（交换机等）的备件测算，数据来源为sn_network_pro_info |
| factory_material_list | 工厂物料清单 | ~18.4万 | 从WMS同步的工厂物料PN码清单，含工业标准描述 |
| scene_project_table | 现场备件项目对应表 | ~29 | 现场备件项目与CRM编号、库存城市、首选库的映射 |
| wms_storeroom_table | WMS库房分配表 | 少量 | WMS库房名称、库存地编码、库房编码的映射配置 |
| crm_table | crm数据表 | ~14.4万 | 从BOM总表同步到CRM系统的数据副本 |
| production_stock | 生产系统PO单 | ~6.9万 | 生产系统的PO单数据 |
| material_shortage | 欠料调拨总表 | ~1120 | 欠料调拨记录 |

---

## 二、核心表字段定义

### base_material（物料基础数据）

所有物料的主数据表，是其他表获取物料描述、分类信息的基础。

| 字段名 | 中文名 | 类型 | 说明 |
|---|---|---|---|
| material_code | 物料代码 | varchar | 唯一键，格式如 302-001115，302开头为标准物料，69开头为旧码 |
| material_desc | 物料描述 | varchar | 物料的中文全称，如"S内存DDR4-32G-3200-2Rx4-RD SX V1.1" |
| supplier_pn | 供应商PN码 | varchar | 供应商的产品编号，用于对外采购和供应商沟通 |
| name | 产品Ⅱ级分类 | varchar | 产品二级分类，如：主板、内存、硬盘、服务器、PC、交换机、风扇 |
| product_category3 | 产品Ⅲ级分类 | varchar | 产品三级分类，比二级分类更细，如具体型号系列 |
| bundling_number | 捆绑料号 | varchar | 该物料对应的捆绑料号，如99-000708，没有捆绑则等于物料代码本身 |
| remark | 备注 | varchar | 备注信息，如特殊用途说明 |
| spare_parts_category | 备件大类 | varchar | 备件大类分类，如：服务器、非电子料、硬盘、内存、主板、线缆、包材 |

### bom_total_table（BOM总表）

核心业务表，记录每个项目在每个城市需要的每种物料的数量（BOM展开后）。

| 字段名 | 中文名 | 类型 | 说明 |
|---|---|---|---|
| material_mode | 物料代码 | varchar | 注意此表用 material_mode 而非 material_code |
| material_desc | 物料描述 | varchar | BOM展开后的物料描述 |
| sum_count | 总数量 | integer | 该项目在该城市需要的该物料数量（BOM展开后累加） |
| proj_name | 项目名 | varchar | 项目名称，如"国网二批物资生产管理系统网安平台可靠性提升项目" |
| delivery_location | 交付地点 | varchar | 项目交付的城市 |
| stock_location | 库存地点 | varchar | 备件库存所在城市，如武汉、北京、上海。注意"武汉"在备料总表中映射为"武汉项目" |
| spare_parts_type | 产品Ⅱ级分类 | varchar | 注意此表用 spare_parts_type 而非 name |
| product_category3 | 产品Ⅲ级分类 | varchar | 产品三级分类 |
| information_sources | 信息来源 | varchar | 只有两个值："存量表"（在保项目）或"过保"（已过保项目） |
| server_desc | 服务描述 | varchar | 维保服务产品类型描述，如"3年白金+"、"5年金牌+" |
| server_aging | 服务时效 | varchar | 服务响应时效，如 7*24*2H（白金）、7*24*4H（金牌）、7*24*ND（标准） |
| proj_number | CRM立项编号 | varchar | CRM系统中的项目立项编号 |
| sale | 销售员 | varchar | 负责该项目的销售员姓名 |
| remark | 备注 | varchar | 备注信息 |
| write_time | 更新日期 | date | 该条BOM数据的更新日期 |
| bundling_number | 捆绑料号 | varchar | 该物料对应的捆绑料号 |
| server_stare_time | 服务开始时间 | date | 维保服务开始日期，从溯源系统获取 |
| server_end_time | 服务结束时间 | date | 维保服务结束日期，用于判断是否过保 |
| spare_parts_category | 备件大类 | varchar | 备件大类分类 |
| preferred_store | 首选库 | varchar | WMS首选库名称 |
| address_code | 首选库存地编码 | varchar | WMS首选库存地编码 |
| storeroom_code | 首选库房编码 | varchar | WMS首选库房编码 |

### bundling_part_number（捆绑料号）

物料代码与捆绑料号的映射关系。一个捆绑料号可对应多个物料代码（同类可替代物料）。

| 字段名 | 中文名 | 类型 | 说明 |
|---|---|---|---|
| bundling_number | 捆绑料号 | varchar | 捆绑料号，如 99-000708，用于聚合同类可替代物料 |
| material_mode | 物料代码 | varchar | 唯一键，一个物料代码只属于一个捆绑料号 |
| material_desc | 物料描述 | varchar | 该物料的中文描述 |
| product_category2 | 产品Ⅱ级分类 | varchar | 注意此表用 product_category2 而非 name 或 spare_parts_type |
| product_category3 | 产品Ⅲ级分类 | varchar | 产品三级分类 |

### purchasing_transit（采购在途）

已下采购订单但尚未到货入库的物料清单。

| 字段名 | 中文名 | 类型 | 说明 |
|---|---|---|---|
| material_mode | 物料代码 | varchar | 唯一键，每种物料只有一条采购在途记录 |
| material_desc | 物料描述 | varchar | 物料中文描述 |
| "supplier_PN" | 供应商PN码 | varchar | 注意字段名带双引号且PN大写，SQL中必须写 "supplier_PN" |
| name | 产品Ⅱ级分类 | varchar | 产品二级分类 |
| product_category3 | 产品Ⅲ级分类 | varchar | 产品三级分类 |
| num | 数量 | integer | 采购在途的数量 |
| bundling_number | 捆绑料号 | varchar | 该物料对应的捆绑料号 |

### dump_transit（转储在途）

已发起库间转储但尚未到达目标库的物料清单。

| 字段名 | 中文名 | 类型 | 说明 |
|---|---|---|---|
| sap_no | 物料代码 | varchar | 唯一键，注意此表用 sap_no 而非 material_mode |
| material_desc | 物料描述 | varchar | 物料中文描述 |
| supplier_pn | 供应商PN码 | varchar | 供应商产品编号 |
| material_type | 产品Ⅱ级分类 | varchar | 注意此表用 material_type 而非 name |
| product_category3 | 产品Ⅲ级分类 | varchar | 产品三级分类 |
| material_num | 数量 | integer | 转储在途数量，注意此表用 material_num 而非 num |
| bundling_number | 捆绑料号 | varchar | 该物料对应的捆绑料号 |

### rma_transit（RMA在途）

已送修但尚未返回的物料清单，数据来自WMS的RMA库存地（WHWXC-FCZT）。

| 字段名 | 中文名 | 类型 | 说明 |
|---|---|---|---|
| material_code | 物料代码 | varchar | 唯一键，此表用 material_code |
| material_desc | 物料描述 | varchar | 物料中文描述 |
| supplier_pn | 供应商PN码 | varchar | 供应商产品编号 |
| name | 产品Ⅱ级分类 | varchar | 产品二级分类 |
| product_category3 | 产品Ⅲ级分类 | varchar | 产品三级分类 |
| quantity | 数量 | integer | RMA在途数量，注意此表用 quantity，默认值0 |
| bundling_number | 捆绑料号 | varchar | 该物料对应的捆绑料号 |

### reject_ratio（不良率）

每种物料的理论故障率，是计算备货量和库存预警的核心参数。

| 字段名 | 中文名 | 类型 | 说明 |
|---|---|---|---|
| sap_no | 物料代码 | varchar | 唯一键，注意此表用 sap_no |
| material_desc | 物料描述 | varchar | 物料中文描述 |
| material_type | 产品Ⅱ级分类 | varchar | 注意此表用 material_type |
| product_category3 | 产品Ⅲ级分类 | varchar | 产品三级分类 |
| theoretical_defect_rate | 理论不良率 | numeric(16,8) | 小数形式，如0.002表示0.2%，0.0085表示0.85% |
| bundling_number | 捆绑料号 | varchar | 该物料对应的捆绑料号 |

### reservoir_area_stock（各库区库存）

从WMS同步的45个城市备件仓库存数据。行存储：每行=一个物料在一个城市的库存。系统展示时行转列为一行45列。

| 字段名 | 中文名 | 类型 | 说明 |
|---|---|---|---|
| sap_no | 物料代码 | varchar | 联合唯一键(sap_no, city)，注意此表用 sap_no |
| bundling_number | 捆绑料号 | varchar | 可能为空，为空时系统用sap_no代替显示 |
| material_desc | 物料描述 | varchar | 物料中文描述 |
| supplier_pn | 供应商PN码 | varchar | 供应商产品编号 |
| spare_parts_category | 备件大类 | varchar | 备件大类分类 |
| material_type | 产品Ⅱ级分类 | varchar | 注意此表用 material_type |
| product_category3 | 产品Ⅲ级分类 | varchar | 产品三级分类 |
| num | 数量 | integer | 该物料在该城市的可用库存数量 |
| city | 城市 | varchar | 库存所在城市名称，共45个可能值（见关键常量） |

### kunpeng_daily（鲲鹏日报）

从Oracle BI视图（DCDWS.VW_DCN_DIKCMX）同步的库存明细数据。

| 字段名 | 中文名 | 类型 | 说明 |
|---|---|---|---|
| bundling_number | 捆绑料号 | varchar | 关联bundling_part_number后填充的捆绑料号 |
| division_name | 事业部名称 | varchar | 所属事业部 |
| service_scope_code | 业务范围代码 | varchar | 业务范围编码，如4801、QF01 |
| service_category | 业务类型 | varchar | 业务类型描述 |
| factory_code | 工厂代码 | varchar | 工厂编码，如MHMU（民和制造）、MH48、MTMU（民和材料） |
| factory_category | 工厂类型 | varchar | 工厂类型描述 |
| is_kt_factory | 是否鲲泰工厂 | varchar | 是否属于鲲泰工厂 |
| is_sale | 是否可售 | varchar | 该库存是否可售 |
| invented_material_code | 虚拟物料号 | varchar | 虚拟物料编号 |
| prod_line | 产品线 | varchar | 产品线名称 |
| prod_category | 产品分类 | varchar | 产品分类 |
| prod_range | 产品系列 | varchar | 产品系列 |
| board_category | 主板类型 | varchar | 主板类型描述 |
| is_xc_board | 是否信创主板 | varchar | 是否为信创主板 |
| board_core | 主板核数 | varchar | 主板CPU核数 |
| material_code | 物料代码 | varchar | 物料代码，格式xxx-xxxxxx |
| material_desc | 中文物料名称 | varchar | 物料的中文名称 |
| batch_code | 批次代码 | varchar | 生产批次编码 |
| material_category_name | 物料类型名称 | varchar | 物料类型的中文名称 |
| material_group_name | 物料组名称 | varchar | 物料组的中文名称 |
| stock_category | 库存地分类 | varchar | 库存地分类，如"借用在途库"（计算XC库存时需排除） |
| stock_address | 库存地代码 | varchar | 库存地编码，如XC02、XC16、XC17、WHBJ等 |
| stock_name | 库存地名称 | varchar | 库存地的中文名称，如"信创材料库" |
| stock_quantity | 实际库存数量 | integer | 该物料在该库存地的实际库存数量 |
| avg_price | 移动平均单价 | float | 物料的移动平均单价（元） |
| real_amount | 实存金额 | float | 实际库存金额（元） |
| dos | DOS | float | 库存周转天数 |
| sale_stock_quantity | 可售库存数量 | integer | 可售的库存数量 |

### material_bom（物料BOM）

BOM结构表，定义物料的父子关系。material_code是父物料，assembly是子物料。支持递归展开。

| 字段名 | 中文名 | 类型 | 说明 |
|---|---|---|---|
| material_code | 物料代码 | varchar | 父物料代码，联合唯一键(material_code, assembly) |
| assembly | 下级组件 | varchar | 子物料代码，即父物料包含的组件 |
| bom_assembly | 下级BOM组件描述 | varchar | 子物料的中文描述 |
| product_category2 | 产品Ⅱ级分类 | varchar | 子物料的产品二级分类 |
| product_category3 | 产品Ⅲ级分类 | varchar | 子物料的产品三级分类 |
| bom_quantity | BOM数量 | integer | 一个父物料包含多少个该子物料 |

### material_stock_order（400派件补库单）

WMS备件出库后的派件记录和补库状态跟踪。

| 字段名 | 中文名 | 类型 | 说明 |
|---|---|---|---|
| is_replenished | 是否补库 | varchar | '0'=否（未补库），'1'=是（已补库） |
| cust_num | WMS外部单据号 | varchar | WMS系统中的外部单据编号 |
| dispatch_date | 派件日期 | date | 备件派出的日期 |
| material_code | 料号 | varchar | 派件的物料代码 |
| description | 描述 | varchar | 物料描述 |
| name | 产品Ⅱ级分类 | varchar | 产品二级分类 |
| product_category3 | 产品Ⅲ级分类 | varchar | 产品三级分类 |
| material_attribute | 物料属性 | varchar | 物料属性描述 |
| outgoing_warehouse | 出库库房简称 | varchar | 出库的库房简称，如"武汉"、"北京" |
| dispatch_quantity | 发货数量 | integer | 本次派件的发货数量 |
| bundled_material_code | 捆绑料号 | varchar | 该物料对应的捆绑料号 |
| replenishment_status | 补库单状态 | varchar | '0'=Closed, '1'=Ongoing, '2'=Cancel, '3'=Dely |
| replenishment_date | 补库日期 | date | 补库操作的日期 |
| today_material_stock | 今日补料库存数量 | varchar | 当日该物料在武汉的库存数量 |
| remaining_stock_quantity | 出库库房剩余库存数量 | integer | 出库库房中该物料的剩余库存 |
| wuhan_stock_quantity_today | 今日武汉库存数量 | integer | 当日武汉库区的库存数量 |
| recommended_replenishment_code | 推荐补库料号 | varchar | 系统推荐的补库物料代码（武汉库存最多的同捆绑料号物料） |
| remark | 备注 | text | 备注信息 |
| project | 项目 | varchar | 关联的项目名称 |
| crm_project_code | CRM立项编号 | varchar | CRM系统的立项编号 |
| crm_work_order | CRM工单号 | varchar | CRM系统的工单编号 |
| replacement_order | 换件单号 | varchar | 换件单编号 |
| push_status | 推送状态 | varchar | '0'=未推送WMS, '1'=已推送WMS |
| external_document_number | 外部单据号 | varchar | 补库单的外部单据号，格式KJ+日期+序号 |

### compute_proj_apply（计算产品备货申请）

从PO通知单计算的备货申请，只保留库存不足需要备货的记录。

| 字段名 | 中文名 | 类型 | 说明 |
|---|---|---|---|
| proj_name | 项目名 | varchar | 项目名称 |
| service_desc | 服务描述 | varchar | 维保服务描述 |
| service_time | 服务时效 | varchar | 如 7*24*2H、7*24*4H、7*24*ND、基础保修 |
| del_address | 交付地点 | varchar | 默认"待定" |
| stock_address | 库存地点 | varchar | 默认"待定" |
| material_code | 物料代码 | varchar | 物料代码 |
| material_desc | 物料描述 | varchar | 物料中文描述 |
| number | 总数量 | varchar | 需要备货的数量，注意类型是varchar不是integer |
| from_info | 信息来源 | varchar | 固定为"PO通知单" |
| crm_no | 立项编号 | varchar | CRM立项编号 |
| sales | 销售员 | varchar | 格式为"姓名-工号" |
| remark | 备注 | varchar | 备注信息 |
| update_date | 更新日期 | date | 数据更新日期 |
| bundling_code | 捆绑料号 | varchar | 该物料对应的捆绑料号 |
| stock_gs | 公司库存数量 | varchar | 公司库存（鲲鹏日报中特定库存地的汇总） |
| stock_wh | WHBJ库存数量 | varchar | WHBJ库存地的库存数量 |

### non_electronic_materials（非电子物料）

非电子物料清单，BOM展开时需要过滤掉这些物料（如包材、标签等）。

| 字段名 | 中文名 | 类型 | 说明 |
|---|---|---|---|
| material_mode | 物料代码 | varchar | 唯一键，非电子物料的物料代码 |
| material_desc | 物料描述 | varchar | 物料中文描述 |
| product_category2 | 产品Ⅱ级分类 | varchar | 产品二级分类 |
| product_category3 | 产品Ⅲ级分类 | varchar | 产品三级分类 |

### material_transformation（物料转换）

69码→302码的物料代码映射，BOM展开时用于将旧物料代码替换为新代码。

| 字段名 | 中文名 | 类型 | 说明 |
|---|---|---|---|
| sap_69_no | 转换前物料代码 | varchar | 69开头的旧物料代码 |
| sap_302_no | 转换后物料代码 | varchar | 302开头的新物料代码 |
| material_desc | 物料描述 | varchar | 转换后物料的中文描述 |
| product_category2 | 产品Ⅱ级分类 | varchar | 产品二级分类 |
| product_category3 | 产品Ⅲ级分类 | varchar | 产品三级分类 |

### inventory_query（SAP库存查询）

SAP库存查询结果缓存，包含预估单价和备件金额。

| 字段名 | 中文名 | 类型 | 说明 |
|---|---|---|---|
| material_code | 物料代码 | varchar | 唯一键 |
| material_desc | 物料描述 | varchar | 物料中文描述 |
| supplier_pn | 供应商PN码 | varchar | 供应商产品编号 |
| material_name | 产品Ⅱ级分类 | varchar | 产品二级分类 |
| apply_factory | 申请工厂 | varchar | 申请转储的工厂代码，如MHMU |
| apply_location | 申请库位 | varchar | 申请转储的库位代码，如XC02 |
| stock_num | 库存数量 | integer | SAP中该工厂+库位的库存数量 |
| apply_num | 申请转储数量 | integer | 用户填写的申请转储数量 |
| estimate_price | 预估单价 | varchar | SAP移动平均价格 |
| estimate_spare_price | 预估备件金额 | float | 预估单价×申请数量 |
| bind_material_code | 捆绑料号 | varchar | 该物料对应的捆绑料号 |
| wuhan_stock_quantity | 武汉库存数量 | integer | 武汉库区的库存数量 |
| final_gap | 最终缺口 | integer | 备料总表中计算的最终缺口 |
| dump_in_transit | 转储在途 | integer | 转储在途数量 |
| rma | RMA在途 | integer | RMA在途数量 |
| pur | 采购在途 | integer | 采购在途数量 |
| obl_flag | 是否预留 | varchar | SAP中是否有预留，"是"或"否" |

### purchase_order_inventory（PO单与存量）

PO单与存量原始数据，是BOM总表的数据源。通过BOM展开后写入bom_total_table。

| 字段名 | 中文名 | 类型 | 说明 |
|---|---|---|---|
| material_mode | 物料代码 | varchar | 物料代码 |
| material_desc | 物料描述 | varchar | 物料中文描述 |
| sum | 总数量 | integer | 该项目在该城市需要的物料数量（BOM展开前） |
| spare_parts_category | 备件大类 | varchar | 备件大类分类 |
| spare_parts_type | 产品Ⅱ级分类 | varchar | 产品二级分类 |
| product_category3 | 产品Ⅲ级分类 | varchar | 产品三级分类 |
| proj_name | 项目名 | varchar | 项目名称 |
| delivery_location | 交付地点 | varchar | 交付城市 |
| stock_location | 库存地点 | varchar | 库存城市 |
| information_sources | 信息来源 | varchar | 数据来源标识 |
| server_desc | 服务描述 | varchar | 维保服务描述 |
| server_aging | 服务时效 | varchar | 服务响应时效 |
| proj_number | 立项编号 | varchar | CRM立项编号 |
| sale | 销售员 | varchar | 销售员姓名 |
| remark | 备注 | varchar | 备注信息 |
| write_date | 更新日期 | date | 数据更新日期 |

### warehouse_allocation（库区分配表）

交付地点+项目时效→派单备件库城市的映射规则。

| 字段名 | 中文名 | 类型 | 说明 |
|---|---|---|---|
| prod_line | 产品线 | varchar | 产品线，如"服务器"、"pc" |
| deliver_addr | 交付地点 | varchar | 项目交付的城市 |
| proj_ageing | 项目时效 | varchar | 项目的服务时效要求 |
| dispatch_spare_parts | 派单备件库 | varchar | 根据交付地点和时效分配的备件库城市 |

### wms_storeroom_table（WMS库房分配表）

WMS库房名称、库存地编码、库房编码的映射配置。

| 字段名 | 中文名 | 类型 | 说明 |
|---|---|---|---|
| storeroom_name | 库房名称 | varchar | WMS库房的中文名称 |
| address | 库存地 | varchar | 库存地简称，如"武汉"、"北京" |
| address_code | 库存地编码 | varchar | WMS库存地编码，如KCDBJ-WHBJC |
| storeroom_code | 库房编码 | varchar | WMS库房编码，如BJ-WHBJC |
| each_store_area | 各库区 | varchar | 是否属于各库区 |
| other_store_area | 其他库区 | varchar | 是否属于其他库区 |
| all_store_area | 所有库区 | varchar | 是否属于所有库区，"是"或"否" |
| alternative_store | 备选库 | varchar | 备选库名称 |
| alternative_store_code | 备选库编码 | varchar | 备选库的WMS编码 |
| alternative_store_area_code | 备选库存地编码 | varchar | 备选库存地的WMS编码 |
| regional_first_store | 区域一级库 | varchar | 区域一级库名称 |

### scene_project_table（现场备件项目对应表）

现场备件项目与CRM编号、库存城市、首选库的映射。

| 字段名 | 中文名 | 类型 | 说明 |
|---|---|---|---|
| project_name | 现场备件项目名 | varchar | 现场备件项目的名称 |
| crm_no | CRM立项编号 | varchar | 对应的CRM立项编号 |
| city | 库存城市 | varchar | 备件库存所在城市 |
| address | 首选库 | varchar | 首选的备件库 |
| scene_parts_num | 现场备件数量 | integer | 现场需要的备件数量 |

### network_spare_trs（网络产品测算）

网络产品（交换机等）的备件测算，数据来源为sn_network_pro_info。

| 字段名 | 中文名 | 类型 | 说明 |
|---|---|---|---|
| material_code | 物料代码 | varchar | 网络产品物料代码 |
| material_desc | 中文描述 | varchar | 物料中文描述 |
| material_team | 物料组描述 | varchar | 物料组的描述 |
| sales_num | 销量 | integer | 销量数据 |
| one_three_rate | 预估第1-3年不良率 | varchar | 固定为"1%" |
| apply_num | 预估备货量 | integer | 计算公式：ceil(销量×0.01/4) - 服务中心库存 |
| service_stock | 服务中心库存 | integer | 服务中心（4801/QF01业务范围）的库存数量 |
| dcn_stock | DCN库存 | integer | DCN（非4801/QF01业务范围）的库存数量 |

### factory_material_list（工厂物料清单）

从WMS同步的工厂物料PN码清单。

| 字段名 | 中文名 | 类型 | 说明 |
|---|---|---|---|
| sap_no | 物料代码 | varchar | 物料代码 |
| industry_standard_desc | 工业标准描述 | varchar | 工业标准描述（PN码） |
| material_desc | 物料描述 | varchar | 物料中文描述 |
| product_category2 | 产品Ⅱ级分类 | varchar | 产品二级分类 |
| product_category3 | 产品Ⅲ级分类 | varchar | 产品三级分类 |

### summary_kanban（汇总看板）

按项目+物料+城市维度汇总的看板数据。刷新时从 bom_total_table 聚合基础数据，再关联备料总表/替代料备料总表获取备货量、库存量、缺口等计算字段。

| 字段名 | 中文名 | 类型 | 说明 |
|---|---|---|---|
| proj_name | 项目名 | varchar | 项目名称，来自 bom_total_table |
| server_aging | 服务时效 | varchar | 服务响应时效，如 7*24*2H、7*24*4H、7*24*ND |
| delivery_location | 交付地点 | varchar | 项目交付的城市 |
| stock_location | 库存地点 | varchar | 备件库存所在城市 |
| material_code | 物料代码 | varchar | 物料代码，来自 bom_total_table.material_mode |
| bundling_number | 捆绑料号 | varchar | 该物料对应的捆绑料号 |
| material_desc | 物料描述 | varchar | 物料中文描述，来自 base_material |
| spare_parts_category | 备件大类 | varchar | 备件大类分类，来自 base_material |
| material_name | 产品Ⅱ级分类 | varchar | 产品二级分类，来自 base_material.name |
| product_category3 | 产品Ⅲ级分类 | varchar | 产品三级分类，来自 base_material |
| sum_count | 总数量 | integer | BOM展开后该项目在该城市需要的物料数量（聚合 SUM） |
| reserve_quantity | 备货量 | integer | 备料计算的备货量，来自备料总表或替代料备料总表 |
| stock_total | 库存量 | integer | 该物料在该城市的库存量，来自备料计算 |
| gap_quantity | 缺口 | integer | 库存量 - 备货量，负数表示不足 |
| wuhan_stock_quantity | 武汉库存量 | integer | 武汉库区的库存数量 |
| gap_total | 最终缺口 | integer | 考虑在途后的最终缺口 |
| purchase_in_transit | 采购在途 | integer | 采购在途数量 |
| dump_in_transit | 转储在途 | integer | 转储在途数量 |
| rma_in_transit | RMA在途 | integer | RMA在途数量 |
| xc_02 | XC02 | integer | XC02库存（信创备件库），来自鲲鹏日报 MHMU+XC02 |
| xc_16 | XC16 | integer | XC16库存，来自鲲鹏日报 MHMU+XC16 |
| xc_17 | XC17 | integer | XC17库存，来自鲲鹏日报 MH48+XC17 |
| has_media_retention | 是否介质保留 | varchar | 服务描述中是否包含"介质保留"，值为"是"或"否" |
| information_sources | 信息来源 | varchar | "存量表"或"过保"，来自 bom_total_table |
| proj_number | CRM立项编号 | varchar | CRM系统中的项目立项编号 |
| server_stare_time | 服务开始时间 | date | 维保服务开始日期 |
| server_end_time | 服务结束时间 | date | 维保服务结束日期 |
| sale | 销售员 | varchar | 负责该项目的销售员姓名 |
| remark | 备注 | varchar | 备注信息 |

---

## 三、表间关系（JOIN 规则）

### 物料代码字段名对照

不同表中"物料代码"字段名不同，JOIN 时必须注意：

| 表名 | 物料代码字段名 |
|---|---|
| base_material | material_code |
| bom_total_table | material_mode |
| bundling_part_number | material_mode |
| purchasing_transit | material_mode |
| dump_transit | sap_no |
| rma_transit | material_code |
| reject_ratio | sap_no |
| reservoir_area_stock | sap_no |
| kunpeng_daily | material_code |
| material_bom | material_code（父）/ assembly（子）|
| material_stock_order | material_code |
| non_electronic_materials | material_mode |
| material_transformation | sap_69_no / sap_302_no |
| purchase_order_inventory | material_mode |
| compute_proj_apply | material_code |
| inventory_query | material_code |
| factory_material_list | sap_no |
| summary_kanban | material_code |
| network_spare_trs | material_code |

### 常用 JOIN 路径

```
base_material.material_code = bom_total_table.material_mode
base_material.material_code = bundling_part_number.material_mode
base_material.material_code = reject_ratio.sap_no
base_material.material_code = reservoir_area_stock.sap_no
base_material.material_code = purchasing_transit.material_mode
base_material.material_code = dump_transit.sap_no
base_material.material_code = rma_transit.material_code
base_material.material_code = kunpeng_daily.material_code
```

### 捆绑料号关联

```
LEFT JOIN bundling_part_number bn ON <物料代码字段> = bn.material_mode
COALESCE(bn.bundling_number, <物料代码字段>) AS bundling_number
```

---

## 四、关键常量

### 45个城市列表（reservoir_area_stock.city）

```
武汉, whbj, 北京, 福州, 上海, 西安, 成都, 厦门, 肇庆, 合肥, 南京, 广州,
阿克苏, 大连, 呼和浩特, 济南, 昆明, 重庆, 南宁, 宁波, 沈阳, 长春, 哈尔滨,
兰州, 石家庄, 太原, 天津, 乌鲁木齐, 西宁, 银川, 汕头, 深圳, 东莞, 烟台,
海口, 武汉项目, 待定, 佛山, 贵阳, 杭州, 郑州, 长沙, 龙岩, 青岛, 南昌, 廊坊
```

"whbj" = 除武汉以外所有城市库存之和（计算字段，非真实城市）。

### 三个特殊库存地（kunpeng_daily）

| 工厂代码 | 库存地代码 | 含义 |
|---|---|---|
| MHMU | XC02 | XC02库存（信创备件库） |
| MHMU | XC16 | XC16库存 |
| MH48 | XC17 | XC17库存 |

### 信息来源（bom_total_table.information_sources）

只有两个值："存量表"（在保项目）、"过保"（已过保项目）

### 库存预警状态映射

| 英文值 | 中文值 |
|---|---|
| adequate | 充足 |
| replenished | 补货 |
| urgently_replenished | 急需补货 |
| out_of_stock | 无库存 |

### 派件补库单状态

| 字段 | 值 | 含义 |
|---|---|---|
| is_replenished | '0' | 未补库 |
| is_replenished | '1' | 已补库 |
| replenishment_status | '0' | Closed（已关闭） |
| replenishment_status | '1' | Ongoing（进行中） |
| replenishment_status | '2' | Cancel（已取消） |
| replenishment_status | '3' | Dely（延迟） |
| push_status | '0' | 未推送WMS |
| push_status | '1' | 已推送WMS |
