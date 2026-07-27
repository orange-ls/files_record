# 常见问题

## Q: business_no 和 business_id 对应业务模型的哪个字段？

这两个字段是 flowable 流程与业务单据之间的核心关联：

- `business_no`：业务单号（如 io_order_no、borrow_no、sales_order_no）
- `business_id`：业务单据的数据库记录 ID（即 ORM 的 id）

不同业务模型的单号字段名不同，开发时务必先确认。
详细映射表见 `references/real-world-examples.md` 的"business_no 和 business_id 映射"章节。

## Q: do_after 中 self 的字段值被重置了？

`parent_do_action()` 过程中非数据库入库字段会被重置。mixin 已经从上下文中恢复了 `code` 等关键字段，
**但如果你在 `do_before` 中设置了自定义的非库字段，需要在 `do_after` 中从 `self.message_param` 中重新获取。**

```python
def do_after(self, kwargs=None):
    # self.code 已被 mixin 恢复，可以直接使用
    # 自定义非库字段需要从 message_param 获取
    my_custom_field = self.message_param.get('my_custom_field', '')
```

## Q: 如何判断流程是否全部完成？

在 `_agree_after()` 中检查 `self.audit_status == BpmnTask.status_complete`。

```python
def _agree_after(self):
    if self.audit_status == BpmnTask.status_complete:
        self.business_record_id.write({'process_status': '2'})
```

## Q: 如何实现条件分支？

在 `action_param()` 中添加分支判断变量，Flowable 流程图中用网关节点读取：

```python
def action_param(self):
    var = super().action_param()
    if self.code == self.button_submit:
        var.append({'name': 'has_disclaimer', 'value': 1 if has_disclaimer else 0})
    return var
```

## Q: 如何在特定节点执行特殊业务逻辑？

在 `_agree_after()` 中通过 `self.message_param.get('current_opt_task_code')` 获取当前节点 code：

```python
def _agree_after(self):
    task_code = self.message_param.get('current_opt_task_code', '')
    if task_code == 'NODE_FINANCE_REVIEW':
        self._do_finance_check()
    if self.audit_status == BpmnTask.status_complete:
        self.business_record_id.write({'process_status': '2'})
```

## Q: 驳回类型怎么配置和使用？

1. 在系统参数中配置：key = `{模型名}_flowable_reject_type`，value = 逗号分隔的类型字符串
2. `useFlowableButton` mixin 已内置驳回类型获取和 xmSelect 渲染逻辑
3. 业务模块在 `_reject_after()` 中通过 `self.message_param.get('reject_type')` 获取

详细说明见 `references/frontend-integration.md` 的"驳回类型选择"章节。

## Q: process_status 的枚举值怎么定义？

默认定义：`[('0', '草稿'), ('1', '流程中'), ('2', '已完成')]`

如果业务模型已有 `process_status` 但枚举值不同（如 xc_borrow 使用 `'1'`~`'4'`），
则沿用已有定义，不覆盖。开发前先检查业务模型是否已有该字段。

## Q: 提交时 flowable_id 传什么？

提交操作时 flowable 记录还不存在，前端传 `-1`。mixin 的 `submit()` 方法会自动创建 flowable 记录。

```javascript
let {code, msg} = await this.orm.call("xc.sn.flowable", "do_action", [-1], params)
```

## Q: Many2many 关联表名冲突怎么办？

`current_spr_ids` 和 `approved_spr_ids` 的 `relation` 参数必须全局唯一。
命名规范：`{模型名下划线}_{字段用途}_rel`

```python
current_spr_ids = fields.Many2many(
    comodel_name='res.users',
    relation='xc_sn_flowable_current_spr_rel',  # 必须唯一
    column1='process_id',
    column2='current_spr_id'
)
```

## Q: toNode 回退到指定节点怎么用？

在 `get_flowable_button()` 中为回退按钮添加 `toNode` 字段，前端会自动将其传入 `do_action`。
后端在 `do_before` 中通过 `kwargs.get("toNode")` 接收，在 `action_param()` 中根据 toNode 值组装流程变量。

详细示例见 SKILL.md 的"toNode：回退到指定节点"章节和 `references/real-world-examples.md` 的 xc_borrow 案例。

## Q: 前端选择下级审批人需要后端 split 吗？

不需要。前端选择下级审批人的组件现在直接返回审批人数组，后端在 `action_param()` 中直接将数组传给 Flowable 引擎即可。

```python
# 前端传入的已经是数组，直接传递
if self.dept_leader_list:
    var.append({'name': 'dept_leader_list', 'value': self.dept_leader_list})
```

## Q: 如何使用公共模板的扩展插槽？

`xc_flowable.FlowableFormButtons` 模板提供了 `xc_flowable.FlowableFormButtonsSlot` 插槽。
业务模块通过继承该插槽添加自定义弹窗内容（如提交时选择审批人）。

详细示例见 `references/frontend-integration.md` 的"第二步：XML 模板"章节和客供料出入库完整示例。
