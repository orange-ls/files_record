---
name: "module_xc_report"
description: "xc_report 报表模块知识库，包含订单报表、BOM报表、质量报表、库存报表、呼叫中心报表、工厂生产报表的数据模型和业务流程。当开发涉及 xc_report 模块、报表、数据统计、base.report、BOM报表、订单报表、HIC报表、质量报表、库存报表、不良报表、保修报表、呼叫中心、工厂成品库存、降价模拟、动态月报、产品详情报表时，务必使用此技能。即使用户只是提到报表开发、数据展示、统计分析相关的需求，也应该触发此技能。"
---

# 报表（xc_report）

> 综合报表平台，提供订单、BOM、质量、库存、呼叫中心、工厂生产等多维度业务数据的统计展示和导出能力。

## 模块概述

xc_report 是信创系统的辅助业务层模块，为各业务线提供统一的报表管理能力。模块包含 50+ 个报表模型，覆盖订单、BOM、质量、库存、呼叫中心、工厂生产等业务领域。

模块设计了 `base.report` 基类（`_auto=False`），统一封装了日志记录（create/write/unlink 自动记录到 `log.report`）和通用字段处理。各业务报表继承基类后专注于自身的数据逻辑。报表数据主要来源于 CRM 系统、BI 平台和内部业务模块，通过定时任务或 API 接口同步。

模块依赖 `base`、`mail`，相对独立，不依赖其他自定义业务模块。

## 核心业务流程

1. 数据采集：定时任务/API 从 CRM、BI、SAP 等外部系统同步数据 → 写入报表模型
2. 报表查询：用户通过 tree/form 视图查询报表数据 → 支持多维度筛选和排序
3. 数据导出：通过 Controller API 导出 Excel 报表 → 支持自定义导出格式
4. 仪表板展示：工厂成品库存仪表板 → 呼叫中心数据看板 → 运营管理视图
5. 数据计算：TAT 时间计算 → 折旧差异计算 → 期末余额计算 → 降价模拟

## 数据模型

| 模型名 | 说明 |
|--------|------|
| `base.report` | 报表基类（_auto=False），封装日志记录和通用字段处理 |
| `log.report` | 报表操作日志表 |
| `network.product.report` | 网络产品报表（返厂维修、TAT计算） |
| `compute.product.report` | 计算产品报表（故障维修统计） |
| `hic.order.report` | HIC订单报表 |
| `hic.summary.data.report` | HIC汇总数据报表 |
| `hic.order.num.search` | HIC订单号查询 |
| `hic.on.sale.product` | HIC在售产品 |
| `material.hic.upl.report` | 物料HIC UPL报表 |
| `supplier.material.hic.upl.report` | 供应商物料HIC UPL报表 |
| `supplier.material.hic.upl.user.config` | 供应商物料HIC UPL用户配置 |
| `order.detail.report` | 订单详情报表 |
| `order.huawei.shipment.data` | 华为发货数据 |
| `order.shipment.lower.layer.details.data` | 发货下层明细数据 |
| `bom.report` | BOM报表 |
| `bom.data.tree` | BOM数据树（支持BOM对比） |
| `bj.default.data` | 北京默认数据 |
| `dynamic.monthly` | 动态月报（折旧差异、期末余额计算） |
| `cut.price.simulator` | 降价模拟器 |
| `material.inventory` | 物料库存报表 |
| `industry.region.overview` | 行业区域概览 |
| `media.rention` | 介质保留报表 |
| `media.retention.basic.data` | 介质保留基础数据 |
| `warranty.out` | 出保报表 |
| `warranty.out.overview` | 出保概览 |
| `problem.report` | 问题报表 |
| `customer.complaint.tracking.record` | 客户投诉跟踪记录 |
| `network.hard.problem` | 网络硬件问题 |
| `scrap.basic.data` | 报废基础数据 |
| `faulty.part.scrap.list` | 故障件报废清单 |
| `faulty.part.scrap` | 故障件报废 |
| `area.people` | 区域人员 |
| `project.issue` | 项目问题 |
| `work.log` | 工作日志 |
| `call.log.report` | 呼叫日志报表（集成呼叫中心API） |
| `search.sap.no.list` | SAP编号查询列表 |
| `quotation.sap.no.count.report` | 报价单SAP编号统计报表 |
| `requirements.acceptance.list` | 需求验收清单 |
| `test.service.list` | 测试服务清单 |
| `factory.finished.goods.stock.detail` | 工厂成品库存详情 |
| `factory.auto.send.email.records` | 工厂自动发送邮件记录 |
| `factory.finished.goods.stock.summary.by.project.weekly` | 工厂成品库存按项目周汇总 |
| `factory.contract.expiration.reminder` | 工厂合同到期提醒 |
| `factory.material.arrival.notice` | 工厂物料到货通知 |
| `factory.production.plan` | 工厂生产计划 |
| `expected.commission.report` | 预期佣金报表 |
| `finished.goods.data` | 成品数据 |
| `stocking.sales.variance` | 备货销售差异 |
| `product.detail.report` | 产品详情报表 |
| `hic.eco.ledger.management` | HIC ECO台账管理 |

## 主要功能模块

- **订单报表**：HIC订单报表、订单详情报表、华为发货数据、发货下层明细
- **BOM报表**：BOM报表查询、BOM数据树对比、BOM数据导出
- **质量报表**：网络产品报表（TAT计算）、问题报表、客户投诉跟踪、网络硬件问题、故障件报废
- **库存报表**：物料库存、工厂成品库存详情/仪表板、备货销售差异
- **财务报表**：动态月报（折旧计算）、降价模拟器、预期佣金报表、平均转移价格
- **呼叫中心**：呼叫日志报表、呼叫中心月报、热线个人数据、二线支持
- **工厂管理**：生产计划、物料到货通知、合同到期提醒、自动邮件发送
- **数据导出**：通用Excel导出、自定义报表格式

## 外部集成

| 系统 | 集成方式 | 说明 |
|------|----------|------|
| CRM | HTTP API | 同步订单、客户、项目数据（通过 crm_utils） |
| BI 平台 | HTTP API | 同步统计分析数据 |
| 呼叫中心 | HTTP API | 同步呼叫日志数据 |
| SAP | HTTP API | SAP编号查询和关联 |

## 系统术语

| 术语 | 说明 |
|------|------|
| HIC | 华为信息与通信，相关订单和报表的前缀标识 |
| UPL | 统一价格表（Unified Price List） |
| TAT | 周转时间（Turn Around Time），衡量维修效率 |
| BOM | 物料清单（Bill of Materials） |
| RMA | 退货授权（Return Merchandise Authorization） |
| 出保 | 产品超出保修期 |
| 介质保留 | 故障硬盘等存储介质的保留管理 |
