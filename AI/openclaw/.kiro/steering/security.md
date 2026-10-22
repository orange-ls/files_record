---
inclusion: fileMatch
fileMatchPattern: 'xc_addons/**'
---
# 安全规范

## 代码安全
- 禁止代码中直接明文显示一切账号，密码，密钥，服务器ip，域名，数据库配置等信息
- 非必要禁止直接修改xinchuang-materiel/addons和xinchuang-materiel/odoo下的任何文件，若一定要修改才能实现相应功能的话，则给出提醒，将需修改的代码交由人工手动编写
- 禁止在 `main`、`master` 等主干分支上直接进行开发（需提醒用户切换到功能分支或者创建新分支）
- 没有明确说明时禁止私自使用 `auth='public'`，所有API默认是使用`auth='user'`
- 防SQL注入

## 权限体系

### 模型访问权限 (ir.model.access.csv)
- xc_addons下的业务module默认创建普通用户权限组和管理员权限组,普通用户只能对自己创建的数据进行增删改查，管理员能对所有数据进行增删改查
  
```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_my_model_user,my.model.user,model_my_model,xc_sn.group_sn_user,1,0,0,0
access_my_model_manager,my.model.manager,model_my_model,xc_sn.group_sn_manager,1,1,1,1
```

### sudo() 使用规范
- 在当前module中使用ORM查询其他module的数据但是又没有其他module的权限时，可以使用sudo()
- cron定时任务无用户上下文，需要 sudo

## 敏感数据处理
- 外部系统连接信息，数据库密码、API Key 等放在 `odoo.conf` 或环境变量中，不硬编码
- 日志中不打印完整密码、token 等敏感信息

## XSS 防护
- QWeb 模板默认转义 HTML，使用 `t-raw` 时必须确认内容安全
- 前端用户输入必须经过转义后再渲染
- 避免在 JavaScript 中直接拼接 HTML

## 定时任务安全
- 避免 cron 中执行不可回滚的外部操作（如发邮件）放在事务提交后