---
name: "module_xc_spare_parts"
description: "xc_spare_parts 备件测算模块知识库，包含备料总表、BOM测算、库存预警、采购在途、WMS库存同步、鲲鹏日报、扩展保修的数据模型和业务流程。当开发涉及 xc_spare_parts 模块、备件测算、备料、prepare.materials、库存预警、BOM总表、物料BOM、库区库存、采购在途、转储在途、RMA在途、鲲鹏日报、扩展保修、物料短缺、补货订单、仓库分配、捆绑料号时，务必使用此技能。即使用户只是提到备件、备料、库存测算、采购计划相关的开发需求，也应该触发此技能。"
---

# 备件测算（xc_spare_parts）

> 智能备件管理与需求测算平台，提供备料计算、库存预警、多库区管理、采购优化和 WMS 数据同步能力。

## 模块概述

xc_spare_parts 是信创系统的核心业务层模块，负责备件需求预测和库存优化管理。模块以备料总表为核心，基于产品销量、理论不良率和多库区库存数据，自动计算备货量、缺口量和库存预警状态。

模块集成了 WMS（仓储管理系统）和 BI 平台的数据，通过 6 个定时任务实现数据自动同步（每天22:30-22:50执行）。系统支持多库区库存管理，覆盖采购在途、转储在途、RMA在途等多种在途状态，为采购决策提供数据支撑。

模块依赖 `base`、`mail`，相对独立。内部使用 `spare.parts.mixin` 混入类封装通用逻辑。

## 核心业务流程

1. BOM测算：导入/维护物料BOM → 生成BOM总表 → 关联捆绑料号 → 计算物料使用量
2. 备料计算：获取城市销量 → 乘以理论不良率 → 计算备货量 → 对比库存量 → 得出缺口 → 生成库存预警
3. 库存同步：定时任务同步WMS库区库存（每天22:30） → 同步其他库区库存（22:50） → 同步出库单 → 同步库存查询
4. 采购管理：汇总各库区缺口 → 扣除采购在途/转储在途/RMA在途 → 计算最终缺口 → 生成补货订单
5. 扩展保修：维护扩展保修基础数据 → 关联保修BOM → 计算保修汇总 → 导出保修报表
6. 项目测算：CRM项目关联 → 场景项目配置 → 计算项目备件需求 → 未测算项目邮件通知

## 数据模型

| 模型名 | 说明 |
|--------|------|
| `prepare.materials` | 备料总表（核心），汇总备货量、库存量、缺口、预警状态 |
| `alternative.prepare.materials` | 替代备料表，替代物料的备料数据 |
| `material.bom` | 物料BOM表，物料清单关系 |
| `bom.total.table` | BOM总表，BOM测算汇总数据 |
| `base.material` | 基础物料表，物料主数据 |
| `bundling.part.number` | 捆绑料号表，物料捆绑关系 |
| `kunpeng.daily` | 鲲鹏日报表，同步BI销售数据 |
| `reservoir.area.stock` | 库区库存表，各库区的库存数据（WMS同步） |
| `other.reservoir.area.stock` | 其他库区库存表 |
| `dump.transit` | 转储在途表 |
| `purchasing.transit` | 采购在途表 |
| `rma.transit` | RMA在途表 |
| `purchase.order.inventory` | 采购订单库存表 |
| `purchase.order.inventory.new` | 采购订单库存新表 |
| `non.electronic.materials` | 非电子物料表 |
| `warehouse.allocation` | 仓库分配表 |
| `factory.material.list` | 工厂物料清单表 |
| `material.transformation` | 物料转换表 |
| `reject.ratio` | 拒收率表 |
| `inventory.query` | 库存查询表（WMS同步） |
| `summary.kanban` | 汇总看板表 |
| `compute.proj.apply` | 计算项目申请表 |
| `network.spare.trs` | 网络备件转储表 |
| `wms.storeroom.table` | WMS库房表 |
| `material.stock.order` | 物料出库单表（WMS同步） |
| `scene.project.table` | 场景项目表 |
| `crm.city.id` | CRM城市ID表 |
| `crm.table` | CRM表，CRM数据同步 |
| `week.estimates` | 周预估表 |
| `production.stock` | 生产库存表 |
| `production.batch.detail` | 生产批次详情表 |
| `replenishment.order` | 补货订单表 |
| `extended.warranty.base.data` | 扩展保修基础数据表 |
| `extended.warranty.sum.data` | 扩展保修汇总数据表 |
| `extend.warranty.bom.table` | 扩展保修BOM表 |
| `material.shortage` | 物料短缺表 |
| `spare.parts.labor.cost` | 备件劳动成本表 |
| `spare.parts.mixin` | 备件混入类，封装通用逻辑 |
| `version.control.customization` | 版本控制定制表 |

## 主要功能模块

- **备料测算**：备料总表计算、替代备料、库存预警（充足/补货/急需补货/无库存）、缺口分析
- **BOM管理**：物料BOM维护、BOM总表生成/刷新、捆绑料号管理
- **库存管理**：多库区库存查询、WMS库房数据、库存汇总看板、仓库分配
- **在途管理**：采购在途、转储在途、RMA在途、出库单同步
- **采购优化**：最终缺口计算、补货订单生成、采购订单库存
- **扩展保修**：保修基础数据、保修BOM、保修汇总、保修报表导出
- **数据同步**：鲲鹏日报BI同步、WMS库存同步、出库单同步、库存查询同步
- **项目管理**：CRM项目关联、场景项目配置、项目备件需求计算、未测算项目通知
- **数据导入导出**：Excel批量导入（基础物料、捆绑料号）、Excel导出（备料总表、保修数据）

## 外部集成

| 系统 | 集成方式 | 说明 |
|------|----------|------|
| WMS | HTTP API | 同步库区库存、出库单、库存查询数据（定时任务） |
| BI 平台 | HTTP API | 同步鲲鹏日报销售数据（定时任务） |
| CRM | HTTP API | 同步项目和城市数据 |

## 系统术语

| 术语 | 说明 |
|------|------|
| 备料总表 | 汇总所有物料的备货量、库存量、缺口和预警状态的核心报表 |
| 捆绑料号 | 多个物料绑定为一组的编号，用于整体管理 |
| 库存预警 | 根据库存量与备货量的对比，分为充足/补货/急需补货/无库存四级 |
| 理论不良率 | 物料的预期故障率，用于计算备货量 |
| 库区 | 仓库中的分区，不同库区存放不同类型的物料 |
| 在途 | 已下单但尚未到达目标库区的物料（采购在途/转储在途/RMA在途） |
| 鲲鹏日报 | 从BI平台同步的每日销售和库存数据报表 |
| 扩展保修 | 超出标准保修期的额外保修服务 |
| BOM总表 | 物料清单的汇总计算表，用于测算备件需求 |
