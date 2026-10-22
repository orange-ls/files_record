---
name: xc-spare-parts-knowledge
description: xc_spare_parts 信创备件测算系统模块知识库，包含BOM总表、备料总表、各库区库存、物料逻辑、存量模块、网络产品测算、延保成本核算、400派件补库单、数据审视等功能区的数据模型、业务流程和技术设计。当开发涉及备件测算、BOM总表、备料总表、各库区库存、物料BOM、物料转换、捆绑料号、不良率、PO单与存量、延保成本核算、派件补库单、网络产品测算、鲲鹏日报、采购在途、转储在途、RMA在途、物料基础数据、汇总看板、欠料调拨、版本管控、WMS库存同步、SAP BI视图同步时，务必使用此技能。
---

# 信创备件测算系统（xc_spare_parts）

> 根据项目交付的物料BOM，结合库存、在途、不良率等多维度数据，自动计算各地库房的备件需求量和缺口，支撑采购决策和库存规划。同时提供延保成本核算能力。

## 模块概述

| 项目 | 说明 |
|------|------|
| 技术名 | xc_spare_parts |
| 依赖 | base, mail |
| 模型数 | ~40 |
| 使用者 | 备件测算人员、延保报价人员、系统管理员 |

xc_spare_parts 是备件供应链管理的核心模块。系统从PO单与存量数据出发，通过递归BOM展开、物料转换、非电子物料过滤等逻辑生成BOM总表，再结合各库区库存、在途数据、不良率参数计算备料总表和缺口。同时提供延保成本核算（7项成本×3种税率）、400派件补库单（WMS双向集成）、网络产品测算等业务能力。

## 菜单结构

```
信创备件测算系统
├── 汇总预测
│   ├── BOM总表
│   ├── 备料总表
│   ├── 替代料备料总表
│   ├── 本周项目测算
│   └── 延保项目BOM总表
├── 数据审视
│   ├── 汇总看板
│   ├── SAP库存查询
│   ├── 计算产品备货申请
│   ├── 400派件补库单
│   ├── 生产系统PO单
│   ├── 生产po单数据源
│   ├── 本地库存查询
│   ├── 欠料调拨总表
│   └── 版本管控&定制化
├── 基础数据
│   ├── 各库区库存 / 其他库区库存
│   ├── 鲲鹏日报
│   ├── 采购在途 / 转储在途 / RMA在途
│   ├── PO单与存量
│   ├── 工厂物料清单
│   └── 物料基础数据
├── 物料逻辑
│   ├── 非电子物料 / 物料转换 / 物料BOM
│   ├── 捆绑料号
│   └── 不良率
├── 存量模块
│   ├── PO单与存量查询
│   ├── 库区分配表 / WMS库房分配表
│   ├── 现场备件项目对应表
│   └── CRM市级ID
├── 网络产品测算
└── 延保成本核算
    ├── 延保核算基础数据 / ASP上门成本基础数据表
    ├── 备件&ASP上门成本
    ├── 仓储成本 / 物流运输成本 / 健康巡检成本
    └── 成本汇总
```

## 核心业务流程

### BOM总表刷新（save_bom_total → refresh_bom_total）

1. 获取旧表数据（用于延保比对）→ 清空 bom_total_table
2. 获取所有数据源（PO单与存量、物料转换、CRM信息、销售信息、物料基础数据、捆绑料号、服务时间）
3. 递归CTE展开BOM（WITH RECURSIVE，bom_quantity逐层累乘到叶子节点）
4. 应用物料转换映射（SAP 69号→302号）
5. 过滤非电子物料
6. 补充字段：产品分类（base_material）、捆绑料号（bundling_part_number）、服务时间（sn_service_complete_info）
7. 信息来源判定：服务结束时间<今天→"过保"，>=今天→"存量表"，无时间→保持原值
8. 延保判断：旧记录"过保"→新值"存量表"时，写入 extend.warranty.bom.table
9. get_same_data 合并相同维度记录（累加sum_count）→ UPSERT写入
10. 同步CRM字段 → 同步WMS库存（各库区+其他库区）→ 同步鲲鹏日报

### 延保成本核算（get_all_data）

1. 获取物料清单（CRM编号/整机SN/外拓导入三选一）
2. 整机SN模式：递归展开BOM(304/309) → 过滤非电子物料 → 合并重复
3. SAP RFC取部件成本价 → 匹配延保基础数据（不良率/周转次数）
4. 计算：故障数=个数×不良率，备货量=故障数/周转次数，备件削价成本=备货量×成本价×(1-残值率)
5. 维修费 + ASP上门成本 + 仓储/物流/巡检成本
6. 7项成本汇总（未税/6%税/13%税 × 总成本/单台成本）

### 400派件补库单

1. 定时任务同步WMS派件数据
2. 用户选择记录暂存补库单 → 自动生成外部单据号 KJ{YYYYMMDD}{序号}（同天同库房复用，不同库房递增，首次从09开始）
3. 推送WMS执行库间转储

## 数据模型

### 核心聚合层

| 模型 | 存储 | 说明 |
|------|------|------|
| `bom.total.table` | 全量刷新 | BOM总表，递归CTE+多源合并+信息来源判定。唯一约束：(material_mode, proj_name, stock_location, information_sources, server_aging, write_time) |
| `prepare.materials` | 实时SQL | 备料总表，多表JOIN+动态城市列+缺口计算+库存预警 |
| `alternative.prepare.materials` | 实时SQL | 替代料备料总表，按捆绑料号维度聚合 |
| `week.estimates` | 实时SQL | 本周项目测算，按本周时间过滤 |
| `extend.warranty.bom.table` | 本地存储 | 延保项目BOM总表，过保恢复为存量表时自动写入 |
| `purchase.order.inventory.new` | 实时SQL | PO单与存量查询(新)，CTE查溯源系统+服务时效映射+库区分配 |
| `network.spare.trs` | 实时SQL | 网络产品测算，网络产品销量+鲲鹏日报库存 |
| `summary.kanban` | 实时SQL | 汇总看板，多表JOIN聚合 |

### 基础数据层

| 模型 | 数据来源 | 说明 |
|------|----------|------|
| `reservoir.area.stock` | WMS API同步 | 各库区库存，45城市动态列透视表。唯一约束：(sap_no, city) |
| `other.reservoir.area.stock` | WMS API同步 | 其他库区库存，结构同上 |
| `kunpeng.daily` | Oracle BI视图 | 鲲鹏日报，SAP库存明细（事业部/工厂/库存地维度），禁止删除 |
| `purchasing.transit` | Excel导入 | 采购在途。唯一约束：(material_mode) |
| `dump.transit` | Excel导入 | 转储在途。唯一约束：(sap_no) |
| `rma.transit` | Excel/WMS同步 | RMA在途。唯一约束：(material_code) |
| `purchase.order.inventory` | Excel导入 | PO单与存量（BOM总表核心数据源） |
| `factory.material.list` | WMS K3 MySQL | 工厂物料清单。唯一约束：(sap_no, industry_standard_desc, material_desc) |
| `base.material` | Excel导入 | 物料基础数据（所有模型的物料校验基准）。唯一约束：(material_code) |

### 规则配置层

| 模型 | 说明 |
|------|------|
| `non.electronic.materials` | 非电子物料过滤清单。唯一约束：(material_mode) |
| `material.transformation` | 物料转换（SAP 69号→302号映射）。UPSERT约束：(sap_69_no, sap_302_no) |
| `material.bom` | 物料BOM层级关系（递归展开用）。唯一约束：(material_code, assembly) |
| `bundling.part.number` | 捆绑料号映射。唯一约束：(material_mode) |
| `reject.ratio` | 不良率参数。唯一约束：(sap_no) |
| `warehouse.allocation` | 库区分配表（交付地点+时效→派单备件库） |
| `wms.storeroom.table` | WMS库房分配表 |
| `extended.warranty.base.data` | 延保核算基础数据（不良率/周转次数/可维修比例/工程师等级） |
| `asp.cost.per.visit` | ASP上门成本基础数据。唯一约束：(engineer_level, visit_aging, distance) |

### 业务应用层

| 模型 | 说明 |
|------|------|
| `spare.parts.labor.cost` | 备件&ASP上门成本（延保核心计算模型） |
| `warehousing.cost` | 仓储成本 |
| `logistics.transportation.cost` | 物流运输成本 |
| `health.inspection.cost` | 健康巡检成本 |
| `extended.warranty.sum.data` | 成本汇总（7项成本×3种税率×总/单台） |
| `material.stock.order` | 400派件补库单（唯一流程类：补库单+外部单据号+WMS推送） |
| `compute.proj.apply` | 计算产品备货申请 |
| `production.stock` | 生产系统PO单 |
| `production.batch.detail` | 生产po单数据源 |
| `replenishment.order` | 本地库存查询 |
| `material.shortage` | 欠料调拨总表 |
| `version.ctrl.customization` | 版本管控&定制化。唯一约束：(proj_name, crm_number, material_code) |

### 辅助模型

| 模型 | 说明 |
|------|------|
| `spare.parts.mixin` | 公共混入（AbstractModel），提供 get_material_name_plm/get_material_name_base/get_material_name_base_3 |
| `scene.project.table` | 现场备件项目对应表 |
| `crm.city.id` | CRM市级ID |
| `crm.table` | CRM表（同步CRM字段） |

## 通用技术特征

### 动态列机制
reservoir_area_stock / prepare_materials 等模型通过 fields_view_get + fields_get 运行时注入城市库存列。数据库按行存储（物料×城市），前端按列展示。search_read/search_count/read 全部重写为自定义SQL。

### 实时SQL查询
purchase_order_inventory_new / network_spare_trs / summary_kanban / prepare_materials 等不存储本地数据，重写 search_read 执行自定义SQL。

### 递归BOM展开
BOM总表和延保成本核算使用 WITH RECURSIVE CTE 展开物料BOM到叶子节点，bom_quantity逐层累乘。

### UPSERT模式
所有导入和同步使用 INSERT ... ON CONFLICT ... DO UPDATE 幂等写入。

### Excel导入导出
openpyxl生成，黄色表头+冻结首行+防公式注入（'='前加空格），几乎所有模型都支持。

### 物料代码格式转换
SAP格式(xxx-xxxxxx) ↔ WMS格式(18位前导零) 双向转换。8位物料11个前导零，9位物料10个前导零。跳过69开头的物料。

### 前端复用组件
- `summary_predict_button`：导出按钮（BOM总表/备料总表/本周项目测算/替代料备料总表共用）
- `render_switch`：存量开关+刷新按钮（localStorage存储开关状态，注入information_sources上下文）
- `import_and_export_button`：导入导出按钮（基础数据/物料逻辑/各库区库存共用）
- `summary_model`：自定义Model，注入information_sources上下文到search_read和read_group
- 自定义field widget：stock_alert_widget(库存预警)、gap_quantity_widget(缺口)、city_widget(服务时效含2H/4H红色)

### 物料校验
所有基础数据和物料逻辑模型的 create/write/excel_import 都校验物料代码是否在 base.material 中维护，不存在则抛出 UserError。

## 外部系统集成

| 系统 | 连接方式 | 方向 | 用途 |
|------|----------|------|------|
| SAP BI视图 | cx_Oracle | 入 | 鲲鹏日报库存数据（VW_DCN_DIKCMX视图） |
| WMS系统 | HTTP API(MD5签名) | 双向 | 库存同步(入)、补库单推送(出) |
| WMS K3数据库 | pymysql | 入 | 工厂物料清单 |
| SAP RFC | sap_conn(PyRFC) | 入 | 延保部件成本价(VERPR)、SAP库存查询 |
| 邮件系统 | XcMessage | 出 | 未测算项目通知 |

### 平台内部共享表（SQL直查同库）

| 平台内部表 | 模块 | 被谁引用 | 提供什么数据 |
|-----------|------|----------|-------------|
| sn_service_complete_info | 溯源系统(xc_sn) | BOM总表、延保成本核算 | 服务时间、销售员、CRM编号、维保类型 |
| sn_service_bom_info | 溯源系统(xc_sn) | BOM总表、延保成本核算、PO单与存量查询(新) | 项目BOM物料清单、CRM编号映射 |
| sn_pc_bom_component_information | 溯源系统(xc_sn) | PO单与存量查询(新) | PC产品BOM物料清单 |
| sn_network_pro_info | 溯源系统(xc_sn) | 网络产品测算 | 网络产品销售信息 |
| mes_data | 溯源系统(xc_sn) | PO单与存量查询(新) | MES物料代码转换 |
| xc_plm_material | 物料管理系统 | spare.parts.mixin | 产品Ⅱ/Ⅲ级分类 |
| material_manage | 不良率模块(xc_defect_rate) | 延保成本核算 | 69料号与302料号映射 |
| xc_material | 报价系统(quotation) | 延保成本核算 | 物料成本价(备选来源) |
| default_type_data | 不良率模块(xc_defect_rate) | 延保成本核算 | 部件名称 |
| wms.abutment | 数据同步模块(xc_interface) | 各库区库存、工厂物料清单、400派件补库单 | WMS API调用封装 |

## 定时任务

| 时间 | 任务 | 方法 | 默认状态 |
|------|------|------|----------|
| 22:30 | 鲲鹏日报同步 | kunpeng.daily.get_bi_view_data() | 未激活 |
| 22:30 | 各库区库存同步 | reservoir.area.stock.get_wms_data() | 未激活 |
| 22:50 | 其他库区库存同步 | other.reservoir.area.stock.get_wms_data() | 未激活 |
| 22:30 | 出库单同步 | material.stock.order.sync_material_stock_order() | 未激活 |
| 22:30 | 未测算项目通知 | bom.total.table.sync_mail_project() | 未激活 |
| 22:30 | 库存查询同步 | inventory.query.sync_inventory() | 未激活 |

## 权限设计

| 权限组 | 适用范围 |
|--------|----------|
| spare_parts_menu_group | 基础数据、物料逻辑、汇总预测、存量模块、网络产品测算、汇总看板（CRUD全部） |
| base.group_user | 延保成本核算、生产PO单、本地库存查询、欠料调拨、版本管控（CRUD全部） |

特殊控制：Excel导入仅允许指定用户（硬编码 limlg/zhoutingg/huhxd/admin）；鲲鹏日报禁止删除；无记录规则(ir.rule)。

## 关键字段索引

以下字段在模型中设置了 index=True：
- bom.total.table: material_mode
- reservoir.area.stock: sap_no
- kunpeng.daily: material_code
- base.material: material_code
- material.transformation: sap_69_no, sap_302_no, product_category2
- non.electronic.materials: product_category2
- bundling.part.number: bundling_number, material_mode, product_category2
- reject.ratio: sap_no
- factory.material.list: sap_no
- purchase.order.inventory.new: material_mode

## 系统术语

| 术语 | 说明 |
|------|------|
| BOM总表 | 按项目+物料维度汇总的备件需求报表，是系统核心 |
| 备料总表 | 按物料维度汇总需求量+库存+缺口的报表 |
| 信息来源 | 标识数据来源状态：存量表/过保/PO单 |
| 捆绑料号 | 多个物料代码映射到同一个替代料号，用于替代料合并计算 |
| 物料转换 | SAP 69号→302号的物料代码映射 |
| 非电子物料 | 需要从BOM总表中过滤掉的物料（如包装材料等） |
| 动态列 | 数据库按行存储，前端按列展示的透视表机制 |
| WHBJ | 除武汉外所有城市库存之和（计算列） |
| 递归CTE | WITH RECURSIVE SQL，用于展开多层BOM到叶子节点 |
| UPSERT | INSERT ... ON CONFLICT ... DO UPDATE，幂等写入 |
| 存量开关 | 前端开关，控制显示"存量表"数据还是全部数据 |
| 延保成本 | 7项成本：备件成本、介质保留、ASP上门、健康巡检、仓储、物流运输、400分摊 |
| 外部单据号 | 补库单编号格式 KJ{YYYYMMDD}{序号}，同天同库房复用 |
| SAP NO | SAP系统中的物料编码，格式 xxx-xxxxxx |
| WMS编码 | WMS系统中的18位前导零物料编码 |
