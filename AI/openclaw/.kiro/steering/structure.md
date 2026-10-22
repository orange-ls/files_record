# Project Structure

## Top-Level Layout

```
├── odoo/              # Odoo 14.0 core framework (DO NOT modify unless necessary)
│   ├── addons/        # Core base addon (base module)
│   ├── api.py         # Decorator API (@api.model, @api.depends, etc.)
│   ├── fields.py      # Field type definitions
│   ├── models.py      # Base Model, TransientModel, AbstractModel classes
│   ├── http.py        # HTTP/Controller layer
│   ├── cli/           # CLI commands (server, scaffold, shell, etc.)
│   ├── modules/       # Module loader, registry
│   ├── service/       # RPC services
│   ├── tools/         # Utility functions (config, mail, image, etc.)
│   └── tests/         # Core framework tests
├── addons/            # Stock Odoo community addons (~474 modules)
├── xc_addons/         # Custom business modules (primary development area)
├── odoo-bin           # Server entry point
├── odoo.conf          # Server configuration (INI 格式，含 Redis、SAP、外部服务 URL、数据库连接)
├── requirements.txt   # Python dependencies
└── setup.py           # Package setup
```

## Odoo Module Structure Convention

Each module follows this standard layout:

```
xc_addons/<module_name>/
├── __init__.py          # Python package init (imports subpackages)
├── __manifest__.py      # Module metadata, dependencies, data files, assets
├── models/              # ORM model definitions (business logic)
│   ├── __init__.py      # Imports all model files/subpackages
│   └── <domain>/        # Grouped by business domain
├── controllers/         # HTTP endpoints / REST APIs
│   ├── __init__.py
│   └── <domain>/        # Grouped by business domain
├── views/               # XML view definitions (form, tree, kanban, search)
│   └── <domain>/        # Grouped by business domain
├── security/            # Access control
│   ├── ir.model.access.csv   # Model-level ACLs
│   └── security_group.xml    # Security groups and record rules
├── data/                # Default data, cron jobs, email templates
├── static/              # Frontend assets
│   └── src/
│       ├── js/          # JavaScript widgets / OWL 1 components
│       ├── xml/         # QWeb 前端模板
│       └── scss/        # Stylesheets
└── i18n/                # Translation files (.po)
```

## 自定义业务模块 (`xc_addons/`)

所有自定义开发均在此目录下进行。模块按四层架构组织：

```
xc_addons/
│
│  # 第一层：基础设施层（不含业务逻辑，为上层提供基础能力）
├── xc_common/                  # 公共工具库（非标准模块，直接 import）AjaxResult、加密、Redis、多DB连接、SAP/CRM/WMS/MES等外部系统封装、Excel
├── cron_failure_notification/  # 定时任务失败通知，扩展 ir.cron 增加执行日志和失败告警
├── auditlog/                   # 审计日志模块
│
│  # 第二层：平台服务层（跨业务平台能力，被业务模块依赖）
├── xc_user/                    # 用户与组织管理：扩展 Odoo 用户体系，增加 ITCode、部门树形结构
├── oa_web_login/               # 认证与单点登录：UUIP OAuth 扫码登录
├── dcg_flowable/               # 工作流引擎（Flowable BPM）：流程定义/实例管理、审批任务处理
├── xc_theme/                   # 自定义主题样式
│
│  # 第三层：核心业务层（物料管理主要业务流程）
├── xc_material/                # 物料主数据管理
├── xc_material2/               # 物料管理扩展
├── xc_material_manage/         # 物料综合管理
├── xc_order/                   # 订单管理
├── xc_production/              # 生产协同：项目批次管理、BOM配置、排产计划、完工检验、物料转储；集成 MES/WMS/SAP/CRM
├── xc_borrow/                  # 样机借用与物料占料：借用申请、BOM物料配置、占料/释放、超期处理
├── xc_sn/                      # 序列号管理
├── xc_spare_parts/             # 备件管理
├── xc_dos/                     # DOS 相关业务
├── xc_data_sync/               # 数据同步模块
│
│  # 第四层：辅助业务层（专项或轻量级模块）
├── xc_audit/                   # 审单与规则引擎：审单规则配置、物料审核执行
├── xc_report/                  # 报表模块
├── xc_notice/                  # 通知公告
├── xc_home/                    # 首页/门户
├── xc_app/                     # 移动端API：纯 Controller 模块，为移动应用提供 REST API
├── xc_business_visualization/  # 业务可视化
├── xc_operations_dashboard/    # 运营驾驶舱
├── xc_defect_rate/             # 不良率统计
├── xc_network_demand_matching/ # 网络需求匹配
├── dashboard/                  # 仪表盘
├── quotation/                  # 报价管理
├── xc_quotation/               # 报价管理扩展
└── superset_connector/         # Superset BI 连接器
```

### 其他目录

```
xc_interface/                   # 外部接口脚本（独立于 Odoo 模块体系）
├── synchronize_data/           # 数据同步脚本
└── update_material_data/       # 物料数据更新脚本

xc_tools/                       # 第三方工具模块
├── access_restriction_by_ip/   # IP 访问限制
├── auto_backup/                # 自动备份
└── odoo_rabbitmq/              # RabbitMQ 消息队列集成
```

### 模块依赖关系

```
xc_common（工具库，直接 import 引用）
    ↑
xc_user    oa_web_login    dcg_flowable
                ↑
    xc_material / xc_order / xc_production / xc_borrow
                ↑
    xc_sn / xc_spare_parts / xc_material_manage

xc_audit / xc_report / xc_app / xc_notice（相对独立）
```