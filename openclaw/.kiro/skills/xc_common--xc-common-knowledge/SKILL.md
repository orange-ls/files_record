---
name: xc-common-knowledge
description: xc_common 公共工具库知识库，包含 AjaxResult、加密工具、Redis、数据库连接、SAP/CRM/WMS 等外部系统封装、Excel 处理、飞书消息、装饰器等通用工具类索引。当开发需要使用通用工具类、对接外部系统、处理加密/缓存/消息通知、或查找已有工具避免重复造轮子时，务必使用此技能。
---

# 公共工具库（xc_common）

> 系统级公共工具集合，提供加密、缓存、数据库连接、外部系统集成、Excel 处理等通用能力。

## 模块概述

xc_common 不是一个标准的 Odoo 模块（无 `__manifest__.py`），而是一个 Python 工具包，为所有业务模块提供通用的工具类和外部系统集成封装。包括 API 返回封装、加密工具、Redis 缓存、多数据库连接、SAP/CRM/WMS 等外部系统对接、Excel 处理、消息通知等。

## 核心业务流程

无独立业务流程，作为基础工具层被其他模块调用。

## 数据模型

无独立数据模型。

## 主要功能模块（工具类索引）

> 开发时优先使用以下已有工具类，避免重复造轮子。新增工具类时在对应分类表格中追加一行。

### 通用工具

| 文件 | 类/函数 | 用途 | 使用示例 |
|------|---------|------|----------|
| `ajax_result.py` | `AjaxResult` | Controller API 统一返回封装 | `AjaxResult.success(data=xxx)` / `AjaxResult.error(msg='xxx')` |
| `excel_utils.py` | `generate_excel_header()` | 构造 Excel 表头（openpyxl） | `generate_excel_header(headers, sheet)` |
| `xc_date.py` | `XcDate` | 日期工具：当前时间、时间间隔计算 | `XcDate.get_current_time()` / `XcDate.sec_to_day_Hours_minutes(begin, end)` |
| `xc_utils.py` | `smart_round()` | 通用四舍五入（解决 Python 银行家舍入问题） | `smart_round(3.145, 2)` → `3.15` |
| `xc_utils.py` | `get_chinese_money()` | 数字金额转中文大写 | `get_chinese_money(12345.67)` → `壹万贰仟叁佰肆拾伍元陆角柒分` |
| `xc_utils.py` | `filtered_data_by_domain()` | 用 Odoo domain 过滤 dict 列表数据 | `filtered_data_by_domain('xc.model', domain, data_list)` |
| `xc_utils.py` | `sap_no_2material_code()` / `material_code_2sap_no()` | SAP 物料号与 18 位物料代码互转 | `sap_no_2material_code('123-456789')` |
| `action_code.py` | `ActionCode` | 动态执行 Python 代码（safe_eval） | `ActionCode.run_action_code_multi(eval_context, code)` |
| `fun_retry.py` | `retry_concurrent_update_with_backoff()` | 函数重试装饰器（指数退避） | `@retry_concurrent_update_with_backoff(max_retries=3)` |

### 加密工具

| 文件 | 类 | 用途 | 使用示例 |
|------|-----|------|----------|
| `aes_crypt.py` | `AesCodec` | AES 对称加密/解密（ECB 模式） | `AesCodec().aes_encrypt(secret_key, data_dict)` |
| `asymmetric_encrypt.py` | `AsymmetricEncryptionTool` | RSA 非对称加密/解密 | `tool.encrypt(plaintext)` / `tool.decrypt(ciphertext)` |

### 装饰器

| 文件 | 函数 | 用途 | 使用示例 |
|------|------|------|----------|
| `xc_decorators.py` | `con_control(wait)` | 防重复请求（节流） | `@con_control(2)` |
| `xc_decorators.py` | `async_call(sleeptime)` | Odoo 模型方法异步执行 | `@async_call(sleeptime=20)` |
| `xc_decorators.py` | `async_call_new(sleeptime)` | 非 Odoo 继承类的异步执行 | `@async_call_new(sleeptime=20)` |
| `flowable_shunt.py` | `@flowable_shunt` | 工作流版本路由（按流程定义版本分发方法调用） | `@flowable_shunt` |

### 缓存与消息

| 文件 | 类 | 用途 | 使用示例 |
|------|-----|------|----------|

| `xc_redis.py` | `XcRedis` | Redis 单例客户端 + 每日自增计数器 | `XcRedis.get_instance().set(k, v)` / `run_counter('type')` |
| `xc_message.py` | `XcMessage` | 邮件发送 + OA 消息推送 | `XcMessage.send_mail(subject, html, receiver)` / `XcMessage.execute_commands(kwargs)` |
| `feishu_util.py` | `FeiShuUtil` | 飞书机器人消息（批量发送、卡片更新、图片上传） | `FeiShuUtil.batch_send_messsage(type, user_ids, title, content_text, redirect_url)` |

### 数据库连接

| 文件 | 函数 | 用途 |
|------|------|------|
| `database_connect.py` | `get_db_2_0_conn()` | DBOMS 2.0 MSSQL 连接 |
| `database_connect.py` | `get_crm_middle_conn()` | CRM 中间库 MSSQL 连接 |
| `database_connect.py` | `get_bcm_pg_conn()` | BCM PostgreSQL 连接 |
| `database_connect.py` | `get_fx_backup_conn()` | 纷享销客备份 MySQL 连接 |
| `database_connect.py` | `get_fp_conn()` | 发票系统 Oracle 连接 |
| `database_connect.py` | `fetch_all_dict(cur)` | Oracle 游标结果转 dict 列表 |

### 外部系统集成

| 文件 | 类/函数 | 对接系统 | 主要功能 |
|------|---------|----------|----------|
| `sap_function.py` | `sap_conn()` + 各 `call_*` 函数 | SAP | 库存查询、销售/采购订单创建、客户信息、物料转储等 |
| `crm_service.py` | `CRMHelper` | 纷享销客 CRM | 对象查询/锁定/解锁/修改、框架状态更新 |
| `wms_abutment.py` | `WmsAbutment` | WMS 仓储 | 库存查询（总量/分库区）、交易凭证查询 |
| `common_sql.py` | `CommonSql` | CRM 中间库 | 价格申请单 CRUD、框架协议导入 |
| `dcg_oa_seal_service.py` | `DcgOASealService` | OA 印章系统 | 获取印章列表 |
| `dcg_ssp_service.py` | `DcgSspService` | SSP 合规系统 | 合规受限客户查询 |
| `dcg_verification_service.py` | `DcgVerificationService` | 核销系统 | 预收款查询、现销申请单推送/删除 |
| `dcg_sales_invoice_service.py` | `DcgSalesInvoiceService` | 发票系统 | 发票类别/类型查询 |
| `dcg_sq_system_service.py` | `DcgSqSystemService` | 神州商桥 | 销售订单推送、发货单同步、PO 通知单、排产计划 |
| `dcg_take_seal_number_service.py` | `DcgTakeSealNumberService` | 排号系统 | 申请排号、查询排号 |
| `dboms_2_0_services.py` | `DBOMS2Helper` | DBOMS 2.0 | 旧系统 HTTP 接口调用 |
| `odoo14_api_util.py` | `Odoo14ApiUtil` | Odoo 14 旧系统 | JSON-RPC 接口调用 |
| `quotation_api.py` | `XcQuotationApi` | 报价系统 | 获取报价配置数据 |

### 其他

| 文件 | 类/函数 | 用途 |
|------|---------|------|
| `skywalking/` | SkyWalking 集成 | APM 链路追踪 |

## 外部集成

| 系统 | 集成方式 | 说明 |
|------|----------|------|
| SAP | PyRFC | 库存、订单、客户、物料等 |
| CRM（纷享销客） | HTTP API | 对象查询/锁定/修改 |
| WMS | HTTP API / MySQL | 库存查询、交易凭证 |
| OA 印章系统 | HTTP API | 印章列表获取 |
| SSP 合规系统 | HTTP API | 受限客户查询 |
| 核销系统 | HTTP API | 预收款查询、现销申请单 |
| 发票系统 | HTTP API / Oracle | 发票类别/类型查询 |
| 神州商桥 | HTTP API | 订单推送、发货同步 |
| 排号系统 | HTTP API | 申请/查询排号 |
| DBOMS 2.0 | HTTP API / MSSQL | 旧系统数据对接 |
| Odoo 14 | JSON-RPC | 旧系统接口调用 |
| 报价系统 | HTTP API | 报价配置数据 |
| 飞书 | HTTP API | 机器人消息推送 |
| Redis | redis-py | Session 缓存、计数器 |

## 系统术语

| 术语 | 说明 |
|------|------|
| AjaxResult | 统一的 API 返回格式封装，包含 code/msg/data |
| smart_round | 修正 Python 银行家舍入的四舍五入方法，已全局替换内置 round |
| flowable_shunt | 流程版本路由装饰器，根据流程定义版本分发到不同的处理方法 |