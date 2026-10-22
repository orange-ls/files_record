# 真实案例参考

> 本文档包含已上线模块的 flowable 集成代码片段，供开发时参考。

## 案例索引

| 模块 | flowable 模型文件 | 说明                      | 集成方式 |
|------|-------------------|-------------------------|----------|
| xc_production | `models/csm_flowable_v1.py` | 客供料出入库审批（最新集成方式）        | useFlowableButton + 公共模板继承 |
| xc_dboms | `models/flowable/xc_dboms_flowable_v1.py` | 确收审批（多流程类型集成场景）         | useFlowableButton |
| xc_dboms | `models/flowable/xc_po_application_flowable_v1.py` | PO单审批                   | useFlowableButton |
| xc_dboms | `models/flowable/xc_sales_contract_flowable_v1.py` | 合同审批                    | useFlowableButton |
| xc_borrow | `models/xc_borrow_flowable_v1.py` | 样机借用审批（多版本）             | 自定义前端（旧方式） |
| xc_borrow | `models/xc_borrow_flowable_251121.py` | 借用审批新版（@flowable_shunt） | 自定义前端（旧方式） |

## xc_production 客供料出入库审批（推荐参考）

这是采用最新公共组件集成方式的典型案例，包含条件分支、手动选择审批人、飞书通知等特性, 使用当前技能时优先使用最新的集成方式。

### 模型定义

```python
# xc_addons/xc_production/models/csm_flowable_v1.py
class CsmFlowableV1(models.Model):
    _name = "xc.csm.flowable"
    _inherit = ['mixin.bpmn.audit']
    _description = '客供料出入库审批'

    _message_subject = "信创生产协同系统通知"
    _message_system_name = '客供料出入库审批'

    PROCESS_TYPE = [('xc_csm_flowable', '客供料出入库审批')]

    # 审批流程节点 code
    NODE_ZSBMSP = 'NODE_ZSBMSP'   # 直属部门审批
    NODE_GCSP = 'NODE_GCSP'       # 工厂审批
    NODE_CKSP = 'NODE_CKSP'       # 仓库审批
    NODE_MESSP = 'NODE_MESSP'     # MES审批

    process_type = fields.Selection(PROCESS_TYPE, index='trigram')
    csm_io_id = fields.Many2one('xc.customer.material.io.info', string='客供料出入库单', ondelete='set null')
    current_spr_ids = fields.Many2many('res.users', 'xc_csm_flowable_current_spr_rel',
                                        'flowable_id', 'user_id', string='当前审批人')
    approved_spr_ids = fields.Many2many('res.users', 'xc_csm_flowable_approved_spr_rel',
                                         'flowable_id', 'user_id', string='已审批人')
    # 前端直接传入审批人数组（无需 split）
    dept_leader_list = fields.Json("直属部门审批人", store=False)
```

### action_param 中的条件分支

```python
def action_param(self):
    var = super().action_param()
    if self.code == self.button_submit:
        csm_io = self.get_csm_io(self.business_no)
        # has_disclaimer 用于 BPMN 网关分支判断
        has_disclaimer = csm_io.has_disclaimer if csm_io else False
        var.append({'name': 'has_disclaimer', 'value': 1 if has_disclaimer else 0})
        # 无免责声明时，传递直属部门审批人列表（前端直接传入数组）
        if not has_disclaimer and self.dept_leader_list:
            var.append({'name': 'dept_leader_list', 'value': self.dept_leader_list})
    return var
```

### get_flowable_button 中的节点控制

```python
def get_flowable_button(self, business_no):
    buttons = []
    csm_io = self.get_csm_io(business_no) if business_no else None
    process_status = csm_io.process_status if csm_io else '0'

    if process_status == '0':
        buttons.append({"name": "提交", "code": self.button_submit, "class": "div_button div_btn_success div_header_button"})
        buttons.append({"name": "暂存", "code": "temp_save", "class": "div_button div_btn_white div_header_button"})

    if process_status == '1' and self.is_current_approver:
        buttons.append({"name": "通过", "code": self.button_agree, "class": "div_button div_btn_success div_header_button"})
        buttons.append({"name": "转办", "code": self.button_transfer, "class": "div_button div_btn_white div_header_button"})
        buttons.append({"name": "驳回", "code": self.button_reject, "class": "div_button div_btn_red div_header_button"})
        # 仅仓库审批和MES审批节点显示回退
        if self.current_node_code in (self.NODE_CKSP, self.NODE_MESSP):
            buttons.append({"name": "回退", "code": self.button_rollback, "class": "div_button div_btn_white div_header_button"})

    if process_status == '1' and self.env.uid == self.create_uid.id:
        buttons.append({"name": "撤回", "code": self.button_cancel, "class": "div_button div_btn_white div_header_button"})
    return buttons
```

## xc_dboms 确收审批（多流程类型）

xc_dboms 用一个 flowable 模型支持了 4 种流程类型，是多流程类型的典型案例。

### PROCESS_TYPE 定义

```python
# xc_addons/xc_dboms/models/flowable/xc_dboms_flowable_v1.py
PROCESS_TYPE = [
    ('xc_dboms_flowable', '销售主管确认'),
    ('xc_dboms_flowable_sw', '商务确认'),
    ('xc_dboms_flowable_kdsw', '开单商务创建'),
    ('xc_dboms_flowable_zjqr', '质检确认'),
]
```

### do_before 中按 process_type 分发

```python
def do_before(self, kwargs):
    self.business_id = kwargs.get("business_id", False)
    self.business_no = kwargs.get("business_no", False)
    self.code = kwargs.get("code", False)
    self.process_type = kwargs.get("process_type", False)

    # 根据 process_type 获取不同的菜单和 action
    if self.process_type == 'xc_dboms_flowable':
        menu_id = self.env.ref('xc_dboms.xc_dboms_root_menu').id
        action_id = self.env.ref('xc_dboms.xc_dboms_todo_action').id
    elif self.process_type == 'xc_dboms_flowable_sw':
        menu_id = self.env.ref('xc_dboms.xc_dboms_root_menu').id
        action_id = self.env.ref('xc_dboms.xc_dboms_sw_todo_action').id
    # ...
```

### do_after 中按 process_type 分发业务逻辑

```python
def submit_after(self, kwargs):
    if self.process_type == 'xc_dboms_flowable':
        distribution = self.get_project_distribution(self.business_no)
        distribution.write({'process_status': '1', 'flowable_id': self.id})
        self.write({'distribution_id': distribution.id})
    elif self.process_type == 'xc_dboms_flowable_sw':
        sales_order = self.get_sales_order(self.business_no)
        sales_order.write({'sw_process_status': '1', 'sw_flowable_id': self.id})
        self.write({'sales_order_id': sales_order.id})
```

## xc_borrow 样机借用审批（多版本 + toNode 回退）

xc_borrow 是多版本路由（@flowable_shunt）和 toNode 回退到指定节点的典型案例。

### 新版本中回退到指定节点

```python
# xc_addons/xc_borrow/models/xc_borrow_flowable_251121.py
@flowable_shunt
def get_flowable_button(self, business_no):
    # ...
    if self.current_node_code == 'NODE_CPJLSP':
        buttons.append({"name": "回退至配置BOM", "code": self.button_rollback,
                        "toNode": 'NODE_PZBOM',
                        "class": "div_button div_btn_white div_header_button"})
        buttons.append({"name": "回退至物料计划", "code": self.button_rollback,
                        "toNode": 'NODE_WLJQFK',
                        "class": "div_button div_btn_white div_header_button"})
```

### action_param 中根据 toNode 组装流程变量

```python
@flowable_shunt
def action_param(self):
    var = super().action_param()
    if self.code == self.button_rollback:
        if self.toNode == 'NODE_PZBOM' and self.current_node_code == 'NODE_CPJLSP':
            var.append({'name': "toNext", 'value': 3})
        else:
            var.append({'name': "toNext", 'value': 2})
    elif self.code == self.button_agree:
        if not self.is_to_product and self.current_node_code == 'NODE_ZDSCJH':
            var.append({'name': "toNext", 'value': 3})
        else:
            var.append({'name': "toNext", 'value': 1})
    return var
```

## 审批人配置方式详解

### 方式一：固定审批人

在 `bpmn.task.node` 中配置：

| 字段 | 值 |
|---|---|
| name | 物料交期反馈 |
| description | NODE_WLJQFK |
| type | many_or（或签） |
| assignee_key | spr6List |
| assignee_value | hanml,haogj,nimx |
| assignee_python_code | （空） |

### 方式二：动态审批人

```python
# assignee_python_code 示例
borrow_apply = self.env['xc.borrow.apply'].search(
    [('borrow_no', '=', business_no)], limit=1
)
product_field = borrow_apply.product_field
action = []
if product_field == '3':
    action = ['guanbina']
elif product_field == '2':
    action = ['songcld']
else:
    action = ['wanghyaam']
```

### 方式三：前一节点人工指定

在bpmn_task_node中无需配置`assignee_value` 和 `assignee_python_code`，都为空。
前端选择审批人后直接返回数组传给后端，后端在 `action_param()` 中直接传给 Flowable 引擎。

前端传参（直接传数组）：
```javascript
let itcodeArr = userSelector.getValue().map(u => u.login);
let params = {
    ...this.getBaseFlowableParams(),
    dept_leader_list: itcodeArr,
};
```

后端组装（直接传递数组，无需 split）：
```python
if self.dept_leader_list:
    var.append({'name': 'dept_leader_list', 'value': self.dept_leader_list})
```

## business_no 和 business_id 映射

**不同业务模型的单号字段名不同，开发时务必先确认**：

| 模块 | business_no 对应字段 | business_id 对应模型 |
|------|---------------------|---------------------|
| xc_production 客供料 | io_order_no | xc.customer.material.io.info 的 id |
| xc_borrow | borrow_no | xc.borrow.apply 的 id |
| xc_dboms 分货 | distribution_no | xc.project.distribution 的 id |
| xc_dboms 销售订单 | sales_order_no | xc.sales.order 的 id |
| xc_dboms PO单 | draft_no | xc.po.application 的 id |
| xc_dboms 合同 | contract_no | xc.sales.contract 的 id |
