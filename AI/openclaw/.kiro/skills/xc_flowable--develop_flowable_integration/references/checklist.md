# 完整集成检查清单

## 开发前确认（向人工确认）

- [ ] 确认 `business_no` 对应业务模型的哪个字段（如 io_order_no、borrow_no）
- [ ] 确认 `business_id` 对应业务模型的哪个字段（通常是 ORM 的 id）
- [ ] 确认业务模型是否已有 `process_status` 字段：若无，已按默认定义创建
- [ ] 已获取 Flowable BPMN 流程图文件或截图
- [ ] 已获取需求描述（每个节点的业务逻辑）

## 后端模型（第一步 + 第二步）

- [ ] `__manifest__.py` 的 `depends` 包含 `'xc_flowable'`
- [ ] 创建了 flowable 模型文件，继承 `mixin.bpmn.audit`
- [ ] 定义了 `_message_subject` 和 `_message_system_name`
- [ ] 定义了 `PROCESS_TYPE` 和 `process_type` 字段
- [ ] 定义了业务单据关联字段（Many2one）
- [ ] 定义了 `current_spr_ids` 和 `approved_spr_ids`（Many2many，用于待办过滤）
- [ ] 实现了 `do_before()` 方法（必传参数 + 可选参数 + 业务校验）
- [ ] 实现了 `do_action()` 方法（do_before → parent_do_action → do_after）
- [ ] 实现了 `do_after()` 方法（按 code 分发到各业务回调方法）
- [ ] 实现了 `action_param()` 方法（组装流程变量）
- [ ] 实现了 `get_flowable_button()` 方法（动态渲染按钮，含 toNode 回退）
- [ ] 实现了 `get_decide_data()` 方法（前端初始化数据）
- [ ] 在 `models/__init__.py` 中导入了 flowable 模型文件

## 前端集成（第三步）

- [ ] 创建了 JS Controller，使用 `useFlowableButton` mixin
- [ ] `stateData` 在 `useFlowableButton` 之前用 `useState` 初始化
- [ ] 声明了 `FlowableApprovalDialog` 和 `TransferFlowableDialog` 组件
- [ ] 创建了 XML 模板，继承 `xc_flowable.FlowableFormButtons`
- [ ] Form 视图包含 `<header>` + `<div class="o_statusbar_buttons"/>`
- [ ] Form 视图声明了隐藏字段（flowableIdField、businessNoField）
- [ ] Form 视图包含 `flowable_task_log` widget
- [ ] `__manifest__.py` 的 `assets.web.assets_backend` 注册了前端资源

## 权限配置（第四步）

- [ ] 配置了 `security_group.xml`（权限组定义）
- [ ] 配置了 `ir.model.access.csv`（flowable 模型给 base.group_user 完整权限）

## 业务模型展示字段 + 视图与菜单（第五步）

- [ ] 业务模型定义了 flowable 关联字段（Many2one → flowable 模型）
- [ ] 业务模型定义了 compute 字段：`current_spr`、`current_node_name`、`is_current_approver`
- [ ] 实现了 `_compute_flowable_data()` 方法
- [ ] tree 视图中展示了流程状态、处理节点、处理人
- [ ] 配置了业务数据列表 action
- [ ] 配置了"我的流程"菜单（待我处理/我已处理）
- [ ] 待办/已办 action 使用 `current_spr_ids`/`approved_spr_ids` 做 domain 过滤
- [ ] 待办/已办 action 的 `res_model` 是业务模型本身，复用业务 form 视图

## Dashboard 首页待办跳转（第八步）

- [ ] 在 `xc_addons/xc_dashboard/controllers/flowable_controller.py` 的 `flowable_data` 方法中，为新的 flowable 模型添加 `jump_url` 跳转链接映射

## odoo.conf

- [ ] 确认 `flowable_todo_url` 已配置

## Flowable 引擎配置（第七步）

- [ ] 在 Flowable 中设计并部署了流程定义
- [ ] 在 Odoo 中同步并绑定了流程定义到业务模型
- [ ] 配置了各节点的审批人（固定 ITCode / 动态 Python 代码 / 前一节点人工指定）
