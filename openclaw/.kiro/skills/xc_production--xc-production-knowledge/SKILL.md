---
name: xc-production-knowledge
description: xc_production 信创生产协同系统模块知识库，包含项目批次管理、BOM配置与对比、虚改配、排产计划（日历视图）、完工检验、物料转储、SLA计算的数据模型和业务流程。当开发涉及生产协同、项目批次、BOM配置、虚改配、排产计划、完工检验、物料转储、SLA计算、MES/WMS/SAP集成时，务必使用此技能。
---

# 信创生产协同系统（xc_production）

> 管理生产批次、虚改配、排产计划、完工检验及物料转储的生产协同模块。

## 模块概述

xc_production 是生产协同管理模块，围绕项目批次的全生命周期进行管理。从 CRM 项目立项到生产批次创建、配置 BOM 管理、排产计划、完工检验、物料转储，覆盖了生产协同的核心业务场景。模块与 MES（制造执行系统）、WMS（仓储管理系统）、SAP 等外部系统深度集成，实现生产数据的实时同步。

## 核心业务流程

1. 项目批次管理：CRM 项目关联 → 创建生产批次 → 配置 BOM → 提交审批 → 工厂排产确认
2. 虚改配流程：创建虚改配批次 → 上传配置清单 → 描述需求 → 提交审批
3. 排产计划：从协同系统和 MES 同步数据 → 生成排产计划 → 日历视图展示 → 导出报表
4. 完工检验：MES 完工数据同步 → SAP 完工检验数据对比
5. 物料转储：创建转储单 → 审批流程 → SAP 转储执行

## 数据模型

| 模型名 | 说明 |
|--------|------|
| `production.project` | 生产项目，关联 CRM 立项信息 |
| `production.project.config` | 项目产品配置 |
| `production.batch` | 项目批次，生产协同核心单据 |
| `production.batch.config` | 批次配置信息（产品型号、数量等） |
| `production.batch.config.detail` | 批次配置 BOM 明细 |
| `production.batch.config.report` | 批次配置报表 |
| `production.batch.log` | 批次变更日志 |
| `production.batch.flowable` | 批次审批流程 |
| `production.virtual.batch` | 虚改配批次 |
| `production.virtual.batch.flowable` | 虚改配审批流程 |
| `production.plan.table` | 排产计划表 |
| `production.complete.inspection` | 完工检验 |
| `production.complete.inspection.sap` | SAP 完工检验数据 |
| `production.dump.info` | 物料转储信息 |
| `production.dump.list` | 转储明细 |
| `production.dump.flowable` | 转储审批流程 |
| `plm.config` | PLM 配置 |

## 主要功能模块

- **项目批次管理**：批次创建、BOM 配置、配置锁定/解锁、BOM 对比（物料计划 vs 报价系统 vs 调度统筹）
- **虚改配管理**：虚改配批次创建、配置清单上传、审批流程
- **排产计划**：MES 数据同步、排产日历视图、计划拆分、WMS 实时库存查询、Excel 导出
- **完工检验**：MES 完工数据同步、SAP 完工检验对比
- **物料转储**：转储单管理、审批流程
- **急单管理**：急单等级变更、邮件通知
- **SLA 计算**：从 MES 和 WMS 获取数据计算 SLA 时效

## 外部集成

| 系统 | 集成方式 | 说明 |
|------|----------|------|
| MES 1.0 | MySQL 直连 | 生产工单、需求数量、入库数量、投产/完工数量 |
| MES 2.0 | PostgreSQL 直连 | 生产项目数据、入库明细（含福州和厦门工厂） |
| WMS | HTTP API / MySQL 直连 | 实时库存查询、入库确认时间 |
| SAP | PyRFC | 完工检验数据、物料转储 |
| CRM（纷享销客） | HTTP API | 项目立项信息、商机阶段 |

## 系统术语

| 术语 | 说明 |
|------|------|
| 项目批次 | 一个 CRM 项目下的一次生产批次，包含多个产品配置 |
| 虚改配 | 对已有产品配置进行虚拟变更的流程，不涉及实际物料变动 |
| BOM | Bill of Materials，物料清单，描述产品的组成物料 |
| 配置锁定 | 批次配置审批通过后锁定，防止修改 |
| 排产计划 | 生产排程计划，包含排产日期、需求数量、入库数量等 |
| SLA | Service Level Agreement，从批次创建到入库完成的时效 |
| 急单 | 需要优先生产的紧急订单 |
| 转储 | 物料在不同库位/工厂之间的转移 |
| SAP NO | SAP 系统中的 18 位物料编码 |
