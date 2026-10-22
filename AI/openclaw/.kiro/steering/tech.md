# 技术栈

## 核心框架

- Odoo 14.0 Community Edition（Python ERP 框架）
- Python 3.6+，PostgreSQL 10+（via psycopg2）
- Werkzeug（WSGI）、Jinja2（模板）、gevent（异步 worker）

## 前端

- Odoo OWL 1 框架（Odoo 14）
- jQuery + Underscore.js（传统 Widget 体系，Odoo 14 主流）
- SCSS 样式，XML 视图模板（form / tree / kanban / pivot / graph / calendar / search）

## Odoo 框架关键组件

- ORM：`models.Model`、`models.TransientModel`、`models.AbstractModel`
- 控制器：`odoo.http.Controller` + `@http.route`
- 报表：QWeb 模板 + `ir.actions.report` + wkhtmltopdf
- 定时任务：`ir.cron` XML 定义
- 权限：`ir.model.access.csv` + `ir.rule`
- RPC：XML-RPC / JSON-RPC

## 构建与运行

```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务
python odoo-bin --config=odoo.conf

# 异步 worker 模式
python odoo-bin gevent --config=odoo.conf

# 更新模块并运行测试
python odoo-bin --config=odoo.conf -d test_db -i <module> --test-enable --stop-after-init

常用 CLI 参数：`-d <db>`、`-u <module>`、`-i <module>`、`--dev=all`
```

