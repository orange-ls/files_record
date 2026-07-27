# mixin.bpmn.audit API 参考

> 源码位置：`xc_addons/xc_flowable/models/mixin_bpmn_audit.py`

## 操作码常量

```python
button_submit = "submit"       # 提交
button_agree = "agree"         # 通过
button_reject = "reject"       # 驳回
button_rollback = "rollback"   # 回退
button_transfer = "transfer"   # 转办
button_signature = "signature" # 加签
button_suspend = "suspend"     # 挂起
button_activate = "activate"   # 激活
button_cancel = "cancel"       # 撤回
```

## 审批状态枚举

```python
AUDIT_STATUS = [
    (BpmnTask.status_pending, '审批中'),    # 'pending'
    (BpmnTask.status_complete, '已完成'),   # 'complete'
    (BpmnTask.status_reject, '已驳回'),     # 'reject'
    (BpmnTask.status_cancel, '已撤回'),     # 'cancel'
    (BpmnTask.status_suspend, '已挂起'),    # 'suspend'
]
```

## 入库字段

| 字段 | 类型 | 说明 | 索引 |
|------|------|------|------|
| `name` | Char | 业务流程名称（自动生成：单号-流程类型） | ✓ |
| `business_no` | Char | 业务单号 | ✓ |
| `business_id` | Integer | 业务单 ID | ✓ |
| `p_ins_id` | Many2one → bpmn.process.instance | 流程实例 | ✓ |
| `p_def_id` | Many2one → bpmn.process.def | 流程定义 | ✓ |
| `audit_status` | Selection(AUDIT_STATUS) | 审批状态，默认 pending | ✓ |
| `process_type` | Selection(PROCESS_TYPE) | 流程类型（子类定义） | ✓ |
| `current_spr` | Char | 当前审批人（逗号分隔的 login） | |
| `approved_spr` | Char | 已审批人（逗号分隔的 login） | |
| `is_delete` | Integer | 逻辑删除标记，默认 0 | ✓ |
| `apply_uid` | Many2one → res.users | 申请人，默认当前用户 | |
| `end_time` | Datetime | 流程结束时间 | |
| `project_name` | Char | 项目名称 | |

## 非入库字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `task_ids` | One2many → bpmn.task | 关联的审批任务列表（compute） |
| `is_current_approver` | Boolean | 当前用户是否为审批人（compute） |
| `current_node_name` | Char | 当前审批节点名称（compute） |
| `current_node_code` | Char | 当前审批节点 code（compute） |
| `current_task_id` | Integer | 当前审批任务 ID（compute） |
| `signature_user` | Char | 加签人 ITCode |
| `assignee_id` | Integer | 转办人 ID |
| `message` | Char | 审批备注，默认"通过" |
| `code` | Char | 当前操作码 |
| `message_param` | Json | 审批消息提醒参数 |
| `message_jump_url` | Char | 消息跳转 URL |
| `is_opt_signature` | Boolean | 是否加签审批 |
| `crm_no` | Char | CRM 编号 |
| `price_apply_no` | Char | 价格申请单号 |
| `quot_no` | Char | 报价单号 |
| `toNode` | Char | 节点分流参数（回退到指定节点时使用） |
| `reject_type` | Char | 驳回类型（从 ir.config_parameter 配置的列表中选择） |
| `signature_type` | Char | 加签类型（signature=或加签, and_signature=并加签） |

## 子类必须重写的方法

### do_before(self, kwargs)
流程操作前业务处理。从 kwargs 提取参数、构建消息 URL、执行业务校验。

### do_action(self, **kwargs)
流程操作主入口。标准实现：`do_before → parent_do_action → do_after`。

### do_after(self, kwargs=None)
流程操作后业务处理。根据 `self.code` 分发到各业务回调方法。

### extra_mail_receiver(self)
可选重写，返回额外的邮件接收人 login 列表。默认返回空列表。

## 父类核心方法

### parent_do_action(self) → flowable record
流程操作的核心执行方法。执行流程：
1. 参数校验（code、business_no、business_id、process_type）
2. 将入参放入 ORM 上下文（context）
3. 根据 code 调用对应方法（submit/agree/reject/rollback 等）
4. 从上下文恢复非库字段（method() 过程中非库字段会被重置）
5. 异步发送消息通知
6. 返回 flowable 记录

### submit(self) → flowable record
提交流程。执行：校验审批人 → 组装参数 → 创建 flowable 记录 → 启动流程 → 创建任务 → 更新审批人。

### agree(self) → self
通过操作。调用 `task_action()`。

### reject(self) → self
驳回操作。调用 `task_action()`，删除所有未完成任务，更新状态为 reject。

### rollback(self) → self
回退操作。调用 `task_action()`。

### transfer(self) → self
转办操作。将当前任务的 assignee_id 更新为目标用户。

### cancel(self) → self
撤回操作。取消流程实例、创建撤回任务记录、删除未完成任务、更新状态为 cancel。

### signature(self) → self
加签操作。支持或加签（signature）和并加签（and_signature）。

### suspend(self) / activate(self) → self
挂起/激活流程实例。

### action_param(self) → list[dict]
组装流程参数。基础实现包含：
- message、code、process_type、toNode
- 从 `bpmn.task.node` 配置中读取的审批人参数
- 审批人校验（检查用户是否存在）

子类重写时调用 `super().action_param()` 后追加业务变量。

### task_create(self)
从 Flowable 引擎拉取新任务，创建 bpmn.task 记录。
所有任务完成时自动将 audit_status 设为 complete。

### update_approved_current_spr(self)
更新 current_spr/approved_spr 字段及对应的 Many2many 字段。

### get_task_log(self) → list
获取审批日志列表，用于前端展示。

## 消息通知方法

mixin 内置了四种消息通知渠道，在 `parent_do_action` 结束后自动异步调用：

| 方法 | 渠道 | 说明 |
|------|------|------|
| `send_message(message_param)` | 总入口 | 异步调用以下四个方法 |
| `mail_message(message_param)` | 邮件 | 给审批人和发起人发邮件 |
| `odoo_message(message_param)` | Odoo 系统消息 | 通过 mail.channel 发送 |
| `oa_message(message_param)` | OA 系统 | 通过 XcMessage 推送 |
| `feishu_message(message_param)` | 飞书 | 通过飞书 API 推送 |

消息配置字段：
- `_message_subject`：邮件主题
- `_message_system_name`：系统名称简称
- `message_jump_url`：审批待办跳转 URL

## 辅助方法

| 方法 | 说明                                                                     |
|------|------------------------------------------------------------------------|
| `submit_check()` | 提交前校验（流程状态、审批人配置）                                                      |
| `task_action_check()` | 操作前校验（是否当前审批人、流程是否挂起）                                                  |
| `task_action()` | 执行 task 动作（通过/驳回/回退的统一入口）                                              |
| `get_my_current_task()` | 获取当前用户的待办任务                                                            |
| `_binding_process_bydb()` | 获取当前模型绑定的流程定义                                                          |
| `_compute_is_approver()` | 计算当前用户是否为审批人                                                           |
| `check_current_spr_exist(login)` | 检查指定用户是否在当前审批人中                                                        |
| `generate_t_id()` | 生成任务唯一 ID                                                              |
| `do_signature(my_current_task)` | 处理加签通过/回退                                                              |
| `get_reject_type()` | 获取驳回类型列表（从 `ir.config_parameter` 读取），key=`{模型名}_flowable_reject_type`） |
| `update_reject_type(value)` | 将新的驳回类型追加到config_parameter中 |
