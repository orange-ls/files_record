---
name: "module_quotation"
description: "quotation 报价系统模块知识库，包含报价单管理、产品配置、价格精算、审批流程、物料管理的数据模型和业务流程。当开发涉及 quotation 模块、报价单、报价系统、xc.quotation、xc.product、产品配置、价格精算、特商资源、报价审批、报价共享、配置BOM转换、物料推荐、报价统计时，务必使用此技能。即使用户只是提到报价、询价、产品定价相关的开发需求，也应该触发此技能。"
---

# 报价系统（quotation）

> 信创报价系统 V2.0，管理报价单全生命周期：创建、产品配置、价格精算、审批流程、共享协作。

## 模块概述

quotation 是信创综合业务管理系统的核心业务模块之一，提供完整的报价管理能力。系统支持多种报价单类型（备货/询价/生产/样机借用等），集成了产品配置、BOM 转换、价格精算、工作流审批等功能。

模块依赖 `xc_user`（用户权限）、`xc_order`（订单系统）、`dcg_flowable`（工作流审批）、`xc_material_manage`（物料管理），是连接销售前端与生产后端的关键枢纽。系统通过 Redis 缓存字典数据，通过定时任务同步历史数据和产品主数据。

## 核心业务流程

1. 报价单创建：新建报价单 → 填写客户/销售信息 → 选择报价单类型（备货/询价/生产/样机借用/其他） → 关联商机编号/CRM项目
2. 产品配置：添加产品 → 配置产品详情（物料明细） → 配置BOM转换 → 审单校验（自动/人工）
3. 价格精算：触发精算 → 计算成本（华为采成本/外采成本） → 生成客户经理价/总经理价 → 精算状态更新
4. 审批流程：提交配置审核 → 工作流审批（集成 dcg_flowable） → 配置锁定 → 价格确认 → 价格锁定
5. 报价共享：创建共享链接 → 设置共享权限 → 协作编辑
6. 特商资源管理：特商资源台账 → 精算关联 → 超期邮件提醒（定时任务）

## 数据模型

| 模型名 | 说明 |
|--------|------|
| `xc.quotation` | 报价单主表，记录报价单基本信息、状态、客户、销售人员等 |
| `xc.product` | 报价单产品表，记录产品型号、数量、价格、审单结果等 |
| `xc.product.detail` | 产品详情表，记录产品的物料明细配置 |
| `xc.product.detail.transfer` | 产品详情转换表，配置BOM转换数据 |
| `xc.product.detail.special` | 产品详情特殊表，特殊配置信息 |
| `xc.product.detail.total` | 产品详情汇总表 |
| `xc.product.detail.cost` | 产品详情成本表 |
| `xc.product.total` | 产品汇总表 |
| `xc.product.expend` | 产品扩展表 |
| `xc.quotation.material` | 报价单物料关联表 |
| `xc.material` | 物料表，报价系统内的物料数据 |
| `xc.material.detail` | 物料详情表 |
| `xc.material.label` | 物料标签表 |
| `xc.material.recommend` | 物料推荐表 |
| `xc.price.actuarial` | 价格精算表 |
| `xc.price.actuarial.history` | 价格精算历史表 |
| `xc.special.price.actuarial.total` | 特商价格精算汇总表 |
| `xc.special.ledger` | 特商资源台账表 |
| `xc.special.table` | 特商表 |
| `xc.quotation.share` | 报价单共享表 |
| `xc.quotation.flowable` | 报价单工作流关联表 |
| `xc.quotation.flowable.expand` | 报价单工作流扩展表 |
| `xc.quotation.count.detail` | 报价单统计详情表 |
| `xc.quotation.audit.count` | 报价单审核统计表 |
| `xc.quotation.notice` | 报价单通知表 |
| `xc.quotation.notice.user` | 报价单通知用户表 |
| `xc.quotation.task.log` | 报价单任务日志表 |
| `xc.log.quotation` | 报价单操作日志表 |
| `xc.log.product` | 产品操作日志表 |
| `xc.log.product.detail` | 产品详情操作日志表 |
| `xc.log.quotation.material` | 报价单物料操作日志表 |
| `xc.rule.approval.log.detail` | 审单规则审批日志详情表 |
| `xc.auto.audit.log` | 自动审单日志表 |
| `xc.config.bom.snapshot` | 配置BOM快照表 |
| `sys.dict.type` | 系统字典类型表 |
| `sys.dict.data` | 系统字典数据表 |
| `sys.notice` | 系统通知表 |
| `product.master.data` | 产品主数据表 |
| `file.folder` | 文件夹表 |

## 主要功能模块

- **报价单管理**：报价单CRUD、状态流转（编辑中→已完成→已删除→已作废）、回收站、批量操作
- **产品配置**：产品添加/编辑、物料明细配置、配置BOM转换、审单校验（自动审单+人工审单）
- **价格精算**：成本计算（华为采/外采）、毛利率计算、精算状态管理、精算历史记录
- **审批流程**：配置审核、价格确认、工作流集成（dcg_flowable）、审批日志
- **特商资源**：特商台账管理、精算关联、超期提醒邮件
- **共享协作**：报价单共享、权限控制、协作编辑
- **数据字典**：字典类型/数据管理、Redis缓存同步
- **统计分析**：报价单统计、审核统计、操作日志

## 外部集成

| 系统 | 集成方式 | 说明 |
|------|----------|------|
| Redis | 直连 | 字典数据缓存同步 |
| CRM | HTTP API | 商机编号、项目信息关联 |
| 订单系统（xc_order） | ORM 依赖 | 报价单推送到订单 |
| 工作流（dcg_flowable） | ORM 依赖 | 审批流程集成 |

## 系统术语

| 术语 | 说明 |
|------|------|
| 报价单 | 面向客户的产品报价文档，包含产品配置和价格信息 |
| 配置BOM | 产品的物料清单配置，可进行BOM转换 |
| 精算 | 对报价单产品进行成本核算和价格计算的过程 |
| 特商资源 | 特殊商务资源台账，用于管理特殊定价和资源分配 |
| 客户经理价 | 销售人员给客户的报价 |
| 总经理价 | 经总经理审批的最终价格 |
| 审单 | 对产品配置进行合规性审核的过程 |
| 配置锁定 | 审批通过后锁定产品配置，防止修改 |
| 价格锁定 | 价格确认后锁定价格，防止修改 |
