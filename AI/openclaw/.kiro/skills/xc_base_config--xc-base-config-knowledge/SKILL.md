---
name: xc-base-config-knowledge
description: xc_base_config 基础配置模块知识库，包含省市区、客户、币种、销售组、付款条件、分销渠道等基础主数据的数据模型。当开发涉及基础主数据查询/维护、客户信息、销售配置、财务配置、API调用日志、邮件日志时，务必使用此技能。
---

# 基础配置模块（xc_base_config）

> 系统基础数据配置，提供省市区、客户、币种、销售组、付款条件等基础主数据管理。

## 模块概述

xc_base_config 是系统基础配置模块，管理业务运行所需的各类基础主数据。包括行政区划（省/市）、客户信息、币种、销售组、付款条件、分销渠道、国际贸易条款、终端用户行业、销售发票配置、销售办事处、公司信息等。同时提供外部系统 API 调用日志和邮件发送日志的记录功能。

## 核心业务流程

1. 基础数据维护：管理员维护各类基础配置数据
2. 数据同步：通过定时任务从外部系统同步基础数据（如客户信息从 SAP 同步）

## 数据模型

| 模型名 | 说明 |
|--------|------|
| `xc.province` | 省份 |
| `xc.city` | 城市 |
| `xc.base.delivery.mode` | 交货方式 |
| `xc.base.currency` | 币种 |
| `xc.base.sales.group` | 销售组 |
| `xc.base.customer` | 客户信息 |
| `xc.base.customer.email` | 客户邮箱 |
| `xc.base.payment.terms` | 付款条件 |
| `xc.base.distribution.channel` | 分销渠道 |
| `xc.base.terms.of.international.trade` | 国际贸易条款 |
| `xc.base.end.user.industry` | 终端用户行业 |
| `xc.base.sales.invoice.config` | 销售发票配置 |
| `xc.base.sales.office` | 销售办事处 |
| `xc.base.company` | 公司信息 |
| `xc.base.industry.email` | 行业邮箱配置 |
| `xc.base.send.mail.log` | 邮件发送日志 |
| `xc.base.external.system.api.log` | 外部系统 API 调用日志 |

## 主要功能模块

- **行政区划**：省份、城市数据维护
- **客户管理**：客户基础信息、客户邮箱
- **销售配置**：销售组、销售办事处、分销渠道、交货方式
- **财务配置**：币种、付款条件、国际贸易条款
- **发票配置**：销售发票相关配置
- **行业配置**：终端用户行业分类
- **日志记录**：邮件发送日志、外部系统 API 调用日志

## 外部集成

无（作为基础数据层被其他模块引用）

## 系统术语

| 术语 | 说明 |
|------|------|
| 分销渠道 | SAP 中的销售渠道分类 |
| 付款条件 | 与客户约定的付款方式和期限 |
| 销售组 | 销售团队的组织单元 |
