---
name: "module_xc_sn"
description: "xc_sn 溯源系统模块知识库，包含序列号管理、SN池、产品追踪、MES/BI数据同步、华为返利、库存查询的数据模型和业务流程。当开发涉及 xc_sn 模块、溯源、序列号、SN管理、sn.pool.info、SN池、物料SN、产品发货、华为返利、MES数据同步、BI数据同步、完整机配置、BOM组件、库位查询、借用管理、网络销售时，务必使用此技能。即使用户只是提到SN、序列号追踪、产品溯源相关的开发需求，也应该触发此技能。"
---

# 溯源系统（xc_sn）

> SN 序列号全生命周期管理系统，提供产品溯源、库存追踪、MES/BI 数据同步和华为业务数据管理能力。

## 模块概述

xc_sn 是信创系统的核心业务层模块，负责产品序列号（SN）的全生命周期管理。系统以 SN 池为核心，记录每个物料从入库、装配、出库到售后服务的完整追踪链路。

模块集成了 MES（制造执行系统）、BI（商业智能）、WMS（仓储管理）等多个外部系统的数据，通过定时任务实现数据自动同步。同时管理华为相关的返利、汇总、配置查询等业务数据。模块包含 57 个数据模型和 11 个 Controller API，是数据量最大、集成最复杂的模块之一。

模块依赖 `mail`，相对独立但被 `xc_spare_parts`、`xc_borrow` 等模块引用。

## 核心业务流程

1. SN入库：WMS/MES 推送入库数据 → 创建 SN 池记录 → 记录库房/工厂/批次/供应商信息
2. SN装配与出库：MES 调用接口更新装配状态 → 记录出库时间 → 更新标识（已出库/已装配）
3. 数据同步：定时任务同步 MES 数据（每天03:00） → 同步 BI 数据 → 同步华为 BI 数据 → 同步借用数据
4. 产品发货：创建发货记录 → 关联 SN 信息 → 导出发货明细
5. 华为业务：华为返利数据管理 → 华为汇总统计 → 华为配置查询 → 返利金额计算
6. 售后服务：服务完成信息记录 → BOM 组件追踪 → 完整机配置变更 → 备件更换确认

## 数据模型

| 模型名 | 说明 |
|--------|------|
| `sn.pool.info` | SN池信息表（核心），记录物料SN的入库/出库/装配状态 |
| `sn.pool.info.new` | SN池信息新表，新版SN池数据 |
| `sn.pool.info.update` | SN池信息更新表，SN数据批量更新 |
| `sn.product.shipment` | 产品发货表 |
| `sn.hw.result` | 华为结果表 |
| `sn.hw.result.xm` | 华为结果项目表 |
| `sn.hw.rebates` | 华为返利表 |
| `sn.hw.rebates.money` | 华为返利金额表 |
| `sn.hw.summary` | 华为汇总表 |
| `sn.hw.config.query` | 华为配置查询表 |
| `sn.hw1246.config` | 华为1246配置表 |
| `sn.pc.stock.information` | PC库存信息表 |
| `sn.pc.bom.component.information` | PC BOM组件信息表 |
| `sn.a3220.complete.machine` | A3220完整机表 |
| `sn.a3220.config` | A3220配置表 |
| `mes.data` | MES数据表，同步MES制造数据 |
| `mes.gz.base.data` | MES广州基础数据 |
| `mes1.from.ret.prd.mtdt` | MES1产品元数据 |
| `mes2.from.t.wip.keyp.info` | MES2 WIP关键信息 |
| `bi.data` | BI数据表，同步BI统计数据 |
| `bi.data.hw` | BI华为数据表 |
| `bi.data.hb` | BI湖北数据表 |
| `city.sales` | 城市销售表 |
| `material.find.manage` | 物料查找管理表 |
| `sn.network.sales` | 网络销售表 |
| `sn.network.pro.info` | 网络产品信息表 |
| `sn.service.complete.info` | 服务完成信息表 |
| `sn.service.complete.info.history` | 服务完成信息历史表 |
| `sn.new.service.complete.info` | 新服务完成信息表 |
| `sn.new.complete.sync` | 新完成同步表 |
| `sn.new.sync.info` | 新同步信息表 |
| `sn.sync.basic.model` | 同步基础模型 |
| `sn.service.bom.info` | 服务BOM信息表 |
| `sn.service.type` | 服务类型表 |
| `sn.borrow.manage.detail` | 借用管理详情表 |
| `sn.gz.complete` | 广州完成表 |
| `sn.gz.bom` | 广州BOM表 |
| `sn.ql.pc.bom.info` | 麒麟PC BOM信息表 |
| `sn.ql.pc.complete.info` | 麒麟PC完成信息表 |
| `sn.qs.complete.info` | QS完成信息表 |
| `sn.hic.info` | HIC信息表 |
| `sn.sequence` | SN序列号生成表 |
| `sn.single.record` | SN单条记录表 |
| `sn.professional.service.record` | 专业服务记录表 |
| `sn.es.memory.sn` | ES内存SN表 |
| `sn.mail.push.service` | 邮件推送服务表 |
| `sn.log` | SN操作日志表 |
| `wm.stock.location.query` | WMS库位查询表 |
| `delivery.address` | 收货地址表 |
| `import.log` | 导入日志表 |
| `business.manual` | 业务手册表（支持Word转PDF） |
| `operation.log` | 操作日志表 |
| `operation.log.mixin` | 操作日志混入类 |
| `sketch.manage` | 草图管理表 |
| `beijian.manage` | 备件管理表 |
| `spare.parts` | 备件表（溯源模块内） |

## 主要功能模块

- **SN池管理**：SN入库/出库/装配状态管理、批量导入/更新、逻辑删除、MES接口更新
- **产品发货**：发货记录管理、发货明细导出
- **华为业务**：返利数据管理、返利金额计算、华为汇总统计、配置查询
- **数据同步**：MES数据自动同步、BI数据同步、华为BI数据同步、借用数据同步
- **库存查询**：PC库存信息、BOM组件信息、WMS库位查询
- **售后服务**：服务完成信息、BOM组件追踪、完整机配置变更、备件更换
- **辅助功能**：操作日志、导入日志、业务手册（Word转PDF）、邮件推送

## 外部集成

| 系统 | 集成方式 | 说明 |
|------|----------|------|
| MES | HTTP API / 数据库直连 | 同步制造执行数据（生产、装配、BOM） |
| BI 平台 | HTTP API | 同步销售、库存等统计数据 |
| WMS | HTTP API | 库位查询、库存信息同步 |
| OA 系统 | HTTP API | 审批流程对接 |
| 华为系统 | HTTP API | 返利数据、配置查询 |
| CRM | HTTP API | 客户和项目数据关联 |

## 系统术语

| 术语 | 说明 |
|------|------|
| SN | 序列号（Serial Number），产品唯一标识 |
| SN池 | 存储所有物料SN信息的核心数据表 |
| MES | 制造执行系统（Manufacturing Execution System） |
| BI | 商业智能（Business Intelligence） |
| WMS | 仓储管理系统（Warehouse Management System） |
| 完整机 | 由多个组件装配而成的完整产品 |
| 返利 | 华为渠道合作的返利政策和金额 |
| 库位 | 仓库中物料存放的具体位置 |
| 借用管理 | 样机或物料的借出和归还管理 |
