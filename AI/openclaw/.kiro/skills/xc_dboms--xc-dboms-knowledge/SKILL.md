---
name: xc-dboms-knowledge
description: xc_dboms IBOMS核心业务系统模块知识库，包含项目信息、销售订单、项目分配、发货单、合同用印、PO采购申请、冲收入订单、多维度报表的数据模型和业务流程。当开发涉及IBOMS、项目信息管理、销售订单、项目分配、发货单、合同用印、PO采购申请、冲收入订单、业务报表、SAP/CRM/OA集成时，务必使用此技能。
---

# IBOMS 核心业务系统（xc_dboms）

> D-BOMS 3.0 核心业务模块，涵盖项目管理、销售订单、项目分配、合同管理、PO申请及各类业务报表。

## 模块概述

xc_dboms 是整个 D-BOMS 系统的核心业务模块，承载了从项目立项到销售交付的完整业务链路。它依赖 xc_base_config（基础配置）、xc_flowable（工作流引擎）和 xc_production（生产协同）模块，实现了项目信息管理、销售订单处理、项目分配、发货单管理、合同用印审批、PO采购申请等核心业务功能，并提供多维度的业务报表。

## 核心业务流程

1. 项目信息管理：从 CRM 系统同步项目立项信息，管理项目产品明细、交付信息、合同信息
2. 销售订单处理：创建销售订单 → 关联发货单 → SAP 物料同步 → 预收款管理 → 审批流程
3. 项目分配：将销售订单中的产品分配到具体项目，跟踪分配状态
4. 合同用印：合同创建 → 用印审批流程 → OA 印章系统对接
5. PO 采购申请：采购申请创建 → 审批流程 → 与 SAP 采购订单同步
6. 业务报表：销售订单明细报表、项目发票报表、发货确认报表、内部公司自动订单报表、寄售明细报表

## 数据模型

| 模型名 | 说明 |
|--------|------|
| `xc.project.info` | 项目信息主表 |
| `xc.project.delivery.info` | 项目交付信息 |
| `xc.project.product` | 项目产品信息 |
| `xc.project.product.details` | 项目产品明细 |
| `xc.project.contract.info` | 项目合同信息 |
| `xc.project.distribution` | 项目分配 |
| `xc.sales.order` | 销售订单 |
| `xc.sales.order.delivery` | 销售订单发货信息 |
| `xc.sales.order.delivery.material` | 发货物料明细 |
| `xc.sales.order.pre.payment` | 销售订单预收款 |
| `xc.sales.delivery.note` | 销售发货单 |
| `xc.sales.delivery.note.material` | 发货单物料明细 |
| `xc.sales.sap.material` | SAP 物料信息 |
| `xc.erp.order.delivery.relation` | ERP 订单发货关联 |
| `xc.sales.contract` | 销售合同 |
| `xc.po.application` | PO 采购申请 |
| `xc.dboms.flowable` | IBOMS 审批流程 |
| `ir.attachment`（继承） | 附件扩展 |

## 主要功能模块

- **项目信息（project_info）**：项目立项、产品配置、交付跟踪、合同关联、虚改配继承
- **项目分配（project_distribution）**：订单产品到项目的分配管理
- **销售订单（sales_order）**：订单创建、发货管理、物料同步、预收款
- **销售合同（sales_contract）**：合同管理、用印审批流程
- **PO 采购申请（po_apply）**：采购申请单管理、审批流程
- **冲收入订单（boost_revenue_order）**：上市冲收入订单、已售未发订单
- **业务报表（report）**：多维度业务数据报表
- **基础配置（base_config）**：客户扩展信息、系统配置
- **审批流程（flowable）**：基于 xc_flowable 的业务审批集成
- **历史数据（history_data）**：历史数据迁移和管理
- **业务日志（base_business_log_model）**：业务操作日志记录

## 外部集成

| 系统 | 集成方式 | 说明 |
|------|----------|------|
| SAP | PyRFC | 销售订单创建、物料信息同步、库存查询 |
| CRM（纷享销客） | HTTP API | 项目立项信息同步、客户数据 |
| OA 印章系统 | HTTP API | 合同用印审批 |
| 神州商桥 | HTTP API | 销售订单推送、发货单同步 |
| 发票系统 | HTTP API | 发票类别/类型查询 |
| 核销系统 | HTTP API | 预收款查询、现销申请单 |
| WMS | HTTP API | 库存查询 |

## 系统术语

| 术语 | 说明 |
|------|------|
| CRM 立项编号 | 纷享销客 CRM 系统中的项目编号，是项目的唯一标识 |
| 项目分配 | 将销售订单中的货物分配到具体项目的操作 |
| 发货单 | 销售订单对应的物流发货凭证 |
| 用印 | 合同盖章审批流程 |
| PO 申请 | 采购订单申请，向供应商下达采购需求 |
| 冲收入订单 | 用于财务冲抵收入的特殊订单类型 |
| 寄售 | 货物已发出但尚未确认收入的销售模式 |
| ZKAA 订单号 | SAP 系统中的内部销售订单编号 |
