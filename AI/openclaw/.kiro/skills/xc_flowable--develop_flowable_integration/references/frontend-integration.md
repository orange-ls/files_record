# 前端集成指南

> 本文档详细说明如何使用 `xc_flowable` 提供的公共组件完成前端审批交互集成。
> 所有审批操作统一通过 ORM RPC 直接调用 flowable 模型方法，不需要额外创建 Controller。

## 目录

- [公共组件清单](#公共组件清单)
- [第一步：JS Controller — 使用 useFlowableButton Mixin](#第一步js-controller--使用-useflowablebutton-mixin)
- [第二步：XML 模板 — 继承公共模板](#第二步xml-模板--继承公共模板)
- [第三步：Form 视图 XML](#第三步form-视图-xml)
- [第四步：assets 注册](#第四步assets-注册)
- [操作前钩子（before hooks）](#操作前钩子before-hooks)
- [ORM RPC 底层参考](#orm-rpc-底层参考)
- [驳回类型选择](#驳回类型选择)
- [指定下一级审批人](#指定下一级审批人)
- [审批日志 Widget](#审批日志-widget)
- [业务模型审批展示字段](#业务模型审批展示字段)
- [菜单与 Action 配置](#菜单与-action-配置)
- [完整前端集成示例：客供料出入库管理](#完整前端集成示例客供料出入库管理)
- [常见问题排查](#常见问题排查)

## 公共组件清单

`xc_flowable` 提供了完整的审批按钮公共组件，业务模块只需引入即可：

| 资源 | 路径 | 说明 |
|------|------|------|
| `useFlowableButton` | `xc_flowable/static/src/views/flowable_button_mixin/flowable_button_mixin.js` | JS Mixin，封装全部审批按钮逻辑 |
| `xc_flowable.FlowableFormButtons` | `xc_flowable/static/src/views/flowable_button_mixin/flowable_form_buttons.xml` | XML 模板，内置 popup-mask + 审批弹窗 + 转办弹窗 + 业务扩展插槽 |
| `FlowableApprovalDialog` | `xc_flowable/static/src/views/flowable_approval_dialog/` | 通过/驳回/回退/撤回弹窗，根据 code_type 自动切换内容 |
| `TransferFlowableDialog` | `xc_flowable/static/src/views/transfer_flowable_dialog/` | 转办/加签弹窗，内置用户选择器 |

`FlowableApprovalDialog` 根据 `code_type` prop 自动切换内容：
- `agree` → 处理意见输入框
- `reject` → 驳回类型选择框（`#reject_type`）+ 处理意见（必填）
- `rollback` / `cancel` → 处理意见输入框（必填）

两个弹窗组件通过 `env.bus` 事件与父 Controller 通信：
- 审批确认 → `bus.trigger('flowableActionBefore', { approval_message })`
- 转办确认 → `bus.trigger('transferFlowable')`
- 加签确认 → `bus.trigger('signatureFlowable')`

## 第一步：JS Controller — 使用 useFlowableButton Mixin

`useFlowableButton` 在 `setup()` 中调用一次，自动注入所有审批按钮方法、bus 监听和 `onMounted` 加载逻辑：

```javascript
/** @odoo-module **/
import { registry } from "@web/core/registry";
import { FormController } from "@web/views/form/form_controller";
import { formView } from "@web/views/form/form_view";
import { useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { RelationalModel } from "@web/views/basic_relational_model";
import { FlowableApprovalDialog } from "@xc_flowable/views/flowable_approval_dialog/flowable_approval_dialog";
import { TransferFlowableDialog } from "@xc_flowable/views/transfer_flowable_dialog/transfer_flowable_dialog";
import { useFlowableButton } from "@xc_flowable/views/flowable_button_mixin/flowable_button_mixin";

class XcSnFormController extends FormController {
    setup() {
        super.setup();
        this.rpc = useService("rpc");
        this.actionService = useService("action");
        // stateData 必须在 useFlowableButton 之前初始化
        this.stateData = useState({
            code_type: '',
            transfer_flowable: { userList: [], operateType: '' },
        });

        // 一行接入全部审批按钮能力（自动注入所有方法、bus 监听、onMounted 加载）
        useFlowableButton(this, {
            flowableModel: "xc.sn.flowable",
            processType: "xc_sn_flowable",
            businessNoField: "record_no",
            flowableIdField: "sn_flowable_id",
        });
    }

    // 暂存（不走 flowable，业务模块自行实现）
    async temp_saveRecord() {
        await this.saveButtonClicked();
    }

    // 示例：重写 flowableActionAfter 改为跳转列表
    // flowableActionAfter(code, msg) {
    //     $('.popup-mask').hide(); $('.flowableApproval').hide(); $('.transfer_block').hide();
    //     if (code === 200) {
    //         this.notification.add(msg, { title: "系统提示", type: 'success', sticky: false });
    //         this.actionService.doAction({
    //             res_model: 'xc.sn.record', name: 'SN记录',
    //             view_mode: 'tree', views: [[false, 'tree'], [false, 'form']],
    //             target: 'main', type: 'ir.actions.act_window',
    //         });
    //     } else {
    //         this.notification.add(msg, { title: "系统提示", type: 'danger', sticky: true });
    //     }
    // }
}

// 必须声明用到的子组件
XcSnFormController.components = {
    ...FormController.components,
    FlowableApprovalDialog,
    TransferFlowableDialog,
};
XcSnFormController.template = "xc_sn_form.FormButtons";

registry.category("views").add("xc_sn_form_view", {
    ...formView,
    Controller: XcSnFormController,
    Model: RelationalModel,
});
```

`useFlowableButton` mixin 自动注入的方法：
- `getDecideData()` — 获取审批按钮列表并渲染
- `renderButton()` — 渲染按钮到状态栏
- `submitRecord()` — 提交（flowable_id 传 -1）
- `agreeRecord()` — 通过（打开审批弹窗）
- `rejectRecord()` — 驳回（获取驳回类型 + 打开弹窗）
- `rollbackRecord()` — 回退
- `cancelRecord()` — 撤回
- `transferRecord()` — 转办（懒加载用户列表）
- `signatureRecord()` — 加签（懒加载用户列表）
- `temp_saveRecord()` — 暂存（默认空实现，业务模块必须重写）
- `flowableAction()` — 统一操作入口
- `flowableActionAfter()` — 操作后处理（默认刷新当前页，可重写为跳转列表）
- `getBaseFlowableParams()` — 获取基础审批参数

## 第二步：XML 模板 — 继承公共模板

业务模块的 XML 模板继承 `xc_flowable.FlowableFormButtons`，该公共模板已包含：
- `popup-mask` 遮罩层
- `FlowableApprovalDialog` 审批弹窗
- `TransferFlowableDialog` 转办/加签弹窗
- `xc_flowable.FlowableFormButtonsSlot` 业务扩展插槽

**无需额外弹窗时（最简写法）：**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<templates xml:space="preserve">
    <t t-name="xc_sn_form.FormButtons"
       t-inherit="xc_flowable.FlowableFormButtons"
       t-inherit-mode="primary" owl="1">
    </t>
</templates>
```

**需要追加业务弹窗时（通过插槽扩展）：**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<templates xml:space="preserve">
    <!-- 继承公共模板，替换插槽 -->
    <t t-name="xc_sn_form.FormButtons"
       t-inherit="xc_flowable.FlowableFormButtons"
       t-inherit-mode="primary" owl="1">
        <xpath expr="//t[@t-call='xc_flowable.FlowableFormButtonsSlot']" position="replace">
            <t t-call="xc_sn_form.FlowableSlot"/>
        </xpath>
    </t>

    <!-- 自定义插槽内容 -->
    <t t-name="xc_sn_form.FlowableSlot"
       t-inherit="xc_flowable.FlowableFormButtonsSlot"
       t-inherit-mode="primary" owl="1">
        <xpath expr="//div" position="replace">
            <div class="flowable_operate_block submit_block">
                <!-- 业务模块自定义弹窗内容，如提交时选择审批人 -->
                <header style="font-size: 24px; font-weight: 600;">提交</header>
                <hr/>
                <content class="flowable_operate_block_content">
                    <div class="d-flex align-items-center">
                        <span style="color: red; margin-right: 2px;">*</span>
                        <span>审批人员:</span>
                        <div id="submit_person" style="width: 330px; margin-left: 15px;"/>
                    </div>
                </content>
                <footer style="margin-top: 15px; float: right;">
                    <button class="btn btn-success" t-on-click="onSubmitFlowable">确定</button>
                    <button class="btn btn-white ml4" t-on-click="onCloseFlowable">取消</button>
                </footer>
            </div>
        </xpath>
    </t>
</templates>
```

> 注意：不能二级继承（即继承另一个 `t-inherit` 模板），Odoo QWeb 不支持。
> 必须直接继承 `xc_flowable.FlowableFormButtons` 或 `web.FormView`。

## 第三步：Form 视图 XML

```xml
<record id="xc_sn_record_view_form" model="ir.ui.view">
    <field name="name">SN记录表单</field>
    <field name="model">xc.sn.record</field>
    <field name="arch" type="xml">
        <form string="SN记录" js_class="xc_sn_form_view">
            <header>
                <!-- 审批按钮容器：useFlowableButton mixin 动态渲染按钮到此处 -->
                <div class="o_statusbar_buttons"/>
                <field name="process_status" widget="statusbar" options="{'clickable': '0'}"/>
            </header>
            <sheet>
                <!-- 隐藏字段：flowable 关联和业务单号（mixin 需要读取） -->
                <field name="sn_flowable_id" invisible="1"/>
                <field name="record_no" invisible="1"/>
                <!-- 业务字段... -->
                <notebook>
                    <page string="流程日志">
                        <widget name="flowable_task_log"
                                flowable_model="xc.sn.flowable"
                                flowable_id="sn_flowable_id"
                                business_no="record_no"/>
                    </page>
                </notebook>
            </sheet>
        </form>
    </field>
</record>
```

关键要点：
1. `<header>` 必须包含 `<div class="o_statusbar_buttons"/>`，mixin 通过 jQuery 选择器动态渲染按钮
2. `process_status` 使用 statusbar widget，`options="{'clickable': '0'}"` 禁止点击切换
3. 隐藏字段（`flowableIdField`、`businessNoField`）必须在 `<sheet>` 内声明，mixin 需要读取

## 第四步：assets 注册

```python
# __manifest__.py
'assets': {
    'web.assets_backend': [
        'xc_sn/static/src/views/**/*',      # 推荐：通配符包含所有视图文件
    ],
},
```

## 操作前钩子（before hooks）

`useFlowableButton` 内置了操作前钩子机制，业务模块可以定义 `before{Action}` 方法在按钮操作前执行校验逻辑。
钩子方法支持异步（async），返回 `false` 则中断后续操作，返回其他值或不定义则继续执行。

| 钩子方法 | 触发时机 | 说明 |
|----------|----------|------|
| `beforeSubmit()` | 点击"提交"后、执行 `submitRecord()` 前 | 提交前校验 |
| `beforeAgree()` | 点击"通过"后、打开审批弹窗前 | 通过前校验 |
| `beforeReject()` | 点击"驳回"后、打开驳回弹窗前 | 驳回前校验 |
| `beforeRollback()` | 点击"回退"后、打开弹窗前 | 回退前校验 |
| `beforeCancel()` | 点击"撤回"后、打开弹窗前 | 撤回前校验 |
| `beforeTransfer()` | 点击"转办"后、打开转办弹窗前 | 转办前校验 |
| `beforeSignature()` | 点击"加签"后、打开加签弹窗前 | 加签前校验 |
| `beforeFlowableConfirm(codeType, data)` | 弹窗点击确认后、调用后端 `do_action` 前 | 最终校验 |

使用示例：

```javascript
setup() {
    super.setup();
    this.stateData = useState({ code_type: '', transfer_flowable: { userList: [], operateType: '' } });
    useFlowableButton(this, { flowableModel: "xc.sn.flowable", processType: "xc_sn_flowable", businessNoField: "record_no", flowableIdField: "sn_flowable_id" });

    // 提交前校验：先保存，再检查条件
    this.beforeSubmit = async () => {
        const saved = await this.saveButtonClicked();
        if (!saved) return false;
        // 特殊条件下打开自定义弹窗，中断默认提交
        if (!this.model.root.data.has_disclaimer) {
            this.openFlowableSubmitDialog();
            return false;
        }
    };

    // 通过前校验
    this.beforeAgree = () => {
        const { amount } = this.model.root.data;
        if (amount <= 0) {
            this.notification.add('金额必须大于0', { title: '系统提示', type: 'warning', sticky: true });
            return false;
        }
    };
}
```

钩子方法与重写 `xxxRecord` 方法的区别：
- `beforeXxx` 钩子：只做校验，不改变操作流程，返回 false 中断，否则继续执行 mixin 原有逻辑
- 重写 `xxxRecord`：完全替换操作方法，需要自行实现完整逻辑
- 推荐优先使用钩子方法，仅在需要完全自定义操作流程时才重写 `xxxRecord`

## ORM RPC 底层参考

> 以下为 mixin 内部使用的底层调用方式，正常开发直接用 `useFlowableButton` 即可，无需手写。

```javascript
// 审批操作
let {code, msg} = await this.orm.call(
    "xc.sn.flowable", "do_action", [flowable_id], params
)
// 获取流程初始化数据
let {data} = await this.orm.call(
    "xc.sn.flowable", "get_decide_data", [flowable_id],
    { business_no: business_no }
)
```

### 审批参数 params 结构

```javascript
// 提交
{ business_id, business_no, code: 'submit', process_type: 'xc_sn_flowable', message: '提交审批' }
// 通过
{ business_id, business_no, code: 'agree', process_type, message: '同意' }
// 驳回
{ business_id, business_no, code: 'reject', process_type, message: '驳回原因', reject_type: '退回修改' }
// 加签
{ business_id, business_no, code: 'signature', process_type, message, signature_user: 'itcode1,itcode2', signature_type: 'signature' }
// 转办
{ business_id, business_no, code: 'transfer', process_type, message, assignee_id: userId }
// 回退
{ business_id, business_no, code: 'rollback', process_type, message, toNode: 'NODE_PZBOM' }
// 撤回
{ business_id, business_no, code: 'cancel', process_type, message: '撤回' }
```

## 驳回类型选择

驳回操作需要用户选择驳回类型。`useFlowableButton` mixin 已内置驳回类型获取和 xmSelect 渲染逻辑，无需手动实现。
以下内容供了解底层机制或需要自定义时参考。

### 整体流程

```
系统参数配置驳回类型列表 → 前端调用 get_reject_type 获取列表 → xmSelect 渲染下拉框
→ 用户选择（或自定义创建新类型） → reject_type 传入 do_action
→ mixin 写入 bpmn.task 并自动追加新类型到系统参数 → _reject_after 中按类型处理
```

### 系统参数配置

在系统参数（设置 > 技术 > 参数 > 系统参数）中添加：

| key | value |
|-----|-------|
| `xc.sn.flowable_flowable_reject_type` | `退回修改,终止流程,信息有误` |

key 命名规范：`{flowable 模型的 _name}_flowable_reject_type`

### 后端机制

- `get_reject_type()` — 从 `ir.config_parameter` 读取驳回类型列表，返回字符串数组
- `update_reject_type(value)` — 将新的驳回类型追加到配置列表（mixin 内部自动调用）

业务模块在 `_reject_after()` 中获取驳回类型：

```python
def _reject_after(self, kwargs=None):
    reject_type = self.message_param.get('reject_type', '')
    if reject_type == '终止流程':
        self.business_record_id.write({'process_status': '已终止状态值'})
    else:
        self.business_record_id.write({'process_status': '草稿状态值'})
```

## 指定下一级审批人

当 `bpmn.task.node` 中 `assignee_value` 和 `assignee_python_code` 都为空时，
该节点的审批人需要由上一个节点的审批人在点击"通过"时手动选择。

### 整体流程

```
前端获取用户列表 → 渲染用户选择器 → 用户选择审批人 → 前端组件直接返回审批人数组
→ 传入 do_action params → 后端 do_before 接收 → action_param 直接传给流程引擎
```

### 后端实现

1. 在 flowable 模型中定义非入库字段，字段名必须与 `bpmn.task.node` 的 `assignee_key` 一致：

```python
# 例如 bpmn.task.node 中配置 assignee_key = 'spr10List'
spr10List = fields.Char("产线生产审批人", store=False)
```

2. 在 `do_before` 中从 kwargs 提取（前端直接传入数组，无需 split）：

```python
def do_before(self, kwargs):
    # ... 其他参数
    self.dept_leader_list = kwargs.get("dept_leader_list", False)
```

3. 在 `action_param` 中直接传递数组给流程引擎：

```python
def action_param(self):
    var = super().action_param()
    if self.code == self.button_submit and self.dept_leader_list:
        # 前端已返回数组，直接传给 Flowable
        var.append({'name': 'dept_leader_list', 'value': self.dept_leader_list})
    return var
```

### 前端实现

用户数据来自 `xc_user` 模块的 `dc.users` 模型，调用 `get_all_user_list` 方法。
`useFlowableButton` mixin 提供了 `_ensureUserList()` 方法懒加载用户列表。

```javascript
// 获取用户列表（mixin 已内置，也可手动调用）
await this._ensureUserList();
let userData = this.stateData.transfer_flowable.userList;

// 渲染用户选择器
let userSelector = xmSelect.render({
    el: '#submit_person',
    filterable: true,
    paging: true, pageSize: 10,
    prop: { name: 'cn', value: 'login' },
    data: userData,
});

// 提交时直接获取数组传给后端（无需 split）
let itcodeArr = userSelector.getValue().map(u => u.login);
let params = {
    ...this.getBaseFlowableParams(),
    dept_leader_list: itcodeArr,  // 直接传数组
};
await this.orm.call("xc.sn.flowable", "do_action", [-1], params);
```

关键要点：
- 参数名必须与 `bpmn.task.node` 中配置的 `assignee_key` 完全一致
- 前端选择下级审批人的组件直接返回审批人数组，无需后端进行 split
- 只在特定节点（通过 `current_node_code` 判断）才显示用户选择器
- 用户数据源统一使用 `dc.users` 的 `get_all_user_list` 方法

## 审批日志 Widget

在业务单据的 form 视图中，使用 xc_flowable 提供的 `flowable_task_log` widget：

```xml
<notebook>
    <page string="流程日志">
        <widget name="flowable_task_log"
                flowable_model="xc.sn.flowable"
                flowable_id="sn_flowable_id"
                business_no="record_no"/>
    </page>
</notebook>
```

widget 参数：
- `flowable_model`：flowable 模型名
- `flowable_id`：业务单据上关联 flowable 记录的字段名
- `business_no`：业务单号字段名

## 业务模型审批展示字段

业务模型需要添加 compute 字段从 flowable 记录中读取审批信息，用于 tree 视图展示。

### 字段定义

```python
sn_flowable_id = fields.Many2one(
    "xc.sn.flowable", string="审批流程",
    domain="[('is_delete','=', 0)]", ondelete='set null'
)
current_spr = fields.Char("处理人", compute='_compute_flowable_data', default='')
current_node_name = fields.Char("处理节点", compute='_compute_flowable_data', default='')
current_node_code = fields.Char("处理节点code", compute='_compute_flowable_data', default='')
is_current_approver = fields.Boolean('是否当前审批人', compute='_compute_flowable_data', default=False)

def _compute_flowable_data(self):
    for s in self:
        s.current_spr = ''
        s.current_node_name = ''
        s.current_node_code = ''
        s.is_current_approver = False
        if s.sn_flowable_id.id > 0:
            current_spr, current_spr_names = s.sn_flowable_id.get_current_spr()
            s.current_spr = current_spr_names
            s.current_node_name = s.sn_flowable_id.current_node_name
            s.current_node_code = s.sn_flowable_id.current_node_code
            s.is_current_approver = s.sn_flowable_id.is_current_approver
```

### tree 视图展示

```xml
<tree>
    <!-- 业务字段... -->
    <field name="process_status" string="流程状态"/>
    <field name="current_node_name" string="处理节点"/>
    <field name="current_spr" string="处理人"/>
    <field name="current_node_code" invisible="1"/>
    <field name="is_current_approver" invisible="1"/>
</tree>
```

## 菜单与 Action 配置

### Action 定义

待办/已办 action 的 `res_model` 直接使用业务模型，`view_mode` 为 `tree,form`。
只通过 `view_id` 指定 tree 视图，不指定 form 视图 — Odoo 自动使用业务模型的默认 form 视图。

```xml
<?xml version="1.0" encoding="UTF-8" ?>
<odoo>
    <!-- 业务数据列表 -->
    <record id="xc_sn_record_action" model="ir.actions.act_window">
        <field name="name">SN记录</field>
        <field name="res_model">xc.sn.record</field>
        <field name="view_mode">tree,form</field>
    </record>

    <!-- 待我处理：通过 flowable 的 current_spr_ids 过滤，复用业务 tree + form 视图 -->
    <record id="xc_sn_process_todo_action" model="ir.actions.act_window">
        <field name="name">待我处理</field>
        <field name="res_model">xc.sn.record</field>
        <field name="view_mode">tree,form</field>
        <field name="target">current</field>
        <field name="context">{'view_type': 'todo'}</field>
        <field name="view_id" ref="xc_sn_record_tree"/>
        <field name="domain">[('sn_flowable_id.current_spr_ids', 'in', [uid])]</field>
    </record>

    <!-- 我已处理：通过 flowable 的 approved_spr_ids 过滤，复用业务 tree + form 视图 -->
    <record id="xc_sn_process_done_action" model="ir.actions.act_window">
        <field name="name">我已处理</field>
        <field name="res_model">xc.sn.record</field>
        <field name="view_mode">tree,form</field>
        <field name="target">current</field>
        <field name="context">{'view_type': 'done'}</field>
        <field name="view_id" ref="xc_sn_record_tree"/>
        <field name="domain">[('sn_flowable_id.approved_spr_ids', 'in', [uid])]</field>
    </record>
</odoo>
```

### 菜单定义

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <menuitem id="xc_sn_root_menu" name="SN系统"
              web_icon="xc_sn,static/description/icon.png"/>
    <menuitem id="xc_sn_record_menu" name="SN记录"
              parent="xc_sn_root_menu" action="xc_sn_record_action" sequence="5"/>
    <menuitem id="xc_sn_process_menu" name="我的流程"
              parent="xc_sn_root_menu" sequence="10"/>
    <menuitem id="xc_sn_audit_menu" name="SN审批"
              parent="xc_sn_process_menu" sequence="10"/>
    <menuitem id="xc_sn_process_todo_menu" name="待我处理"
              parent="xc_sn_audit_menu"
              action="xc_sn_process_todo_action" sequence="1"/>
    <menuitem id="xc_sn_process_done_menu" name="我已处理"
              parent="xc_sn_audit_menu"
              action="xc_sn_process_done_action" sequence="2"/>
</odoo>
```

### 权限组配置

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="group_sn_user" model="res.groups">
        <field name="name">SN 普通用户</field>
        <field name="category_id" ref="base.module_category_hidden"/>
    </record>
    <record id="group_sn_manager" model="res.groups">
        <field name="name">SN 管理员</field>
        <field name="category_id" ref="base.module_category_hidden"/>
        <field name="implied_ids" eval="[(4, ref('group_sn_user'))]"/>
    </record>
</odoo>
```

### odoo.conf 配置

确保配置了审批待办跳转 URL 模板：

```ini
# 参数顺序：menu_id, action_id, model, record_id
flowable_todo_url = http://[domain]/web#cids=1&menu_id={}&action={}&model={}&view_type=form&id={}
```

## 完整前端集成示例：客供料出入库管理

> 源码位置：`xc_addons/xc_production/`，这是采用最新公共组件集成方式的真实案例。

### JS Controller（customer_material_info_form.js）

```javascript
import { FormController } from "@web/views/form/form_controller";
import { formView } from "@web/views/form/form_view";
import { useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { Record, RelationalModel } from "@web/views/basic_relational_model";
import { useFlowableButton } from "@xc_flowable/views/flowable_button_mixin/flowable_button_mixin";
import { FlowableApprovalDialog } from "@xc_flowable/views/flowable_approval_dialog/flowable_approval_dialog";
import { TransferFlowableDialog } from "@xc_flowable/views/transfer_flowable_dialog/transfer_flowable_dialog";

class CustomerMaterialInfoFormController extends FormController {
    setup() {
        super.setup();
        this.actionService = useService("action");
        this.notification = useService("notification");
        this.orm = useService("orm");
        this.stateData = useState({
            code_type: '',
            transfer_flowable: { userList: [], operateType: '' },
        });

        useFlowableButton(this, {
            flowableModel: "xc.csm.flowable",
            processType: "xc_csm_flowable",
            businessNoField: "io_order_no",
            flowableIdField: "csm_flowable_id",
        });

        // 重写暂存
        this.temp_saveRecord = async () => { await this.saveButtonClicked(); };

        // 提交前钩子：先保存，无免责声明时打开审批人选择弹窗
        this.beforeSubmit = async () => {
            const saved = await this.saveButtonClicked();
            if (!saved) return false;
            if (!this.model.root.data.has_disclaimer) {
                this.openFlowableSubmitDialog();
                return false;  // 中断默认提交，由弹窗确认后手动调用
            }
        };

        // 操作成功后跳转列表页
        this.flowableActionAfter = (code, msg) => {
            $('.popup-mask').hide(); $('.flowableApproval').hide(); $('.transfer_block').hide();
            if (code === 200) {
                this.notification.add(msg, { title: "系统提示", type: 'success', sticky: false });
                this.actionService.doAction({
                    res_model: 'xc.customer.material.io.info', name: '客供料出入库管理',
                    view_mode: 'tree', views: [[false, 'tree'], [false, 'form']],
                    target: 'main', type: 'ir.actions.act_window',
                });
            } else {
                this.notification.add(msg, { title: "系统提示", type: 'danger', sticky: true });
            }
        };
    }

    async openFlowableSubmitDialog() {
        await this._ensureUserList();
        $('.popup-mask').show(); $('.submit_block').show();
        setTimeout(() => {
            this.submitPersonInput = xmSelect.render({
                el: '#submit_person', filterable: true, paging: true, pageSize: 10,
                prop: { name: 'cn', value: 'login' },
                data: this.stateData.transfer_flowable.userList,
            });
            this.submitPersonInput.setValue([]);
        }, 100);
    }

    onSubmitFlowable() {
        if (this.submitPersonInput.getValue().length == 0) {
            this.notification.add('请选择审批人员', { title: "系统提示", type: 'warning', sticky: true });
            return;
        }
        this.submitFlowable();
    }

    async submitFlowable() {
        let params = this.getBaseFlowableParams();
        // 前端直接返回数组，无需 split
        params.dept_leader_list = this.submitPersonInput.getValue().map(u => u.login);
        let { code, msg } = await this.orm.call("xc.csm.flowable", "do_action", [-1], params);
        this.flowableActionAfter(code, msg);
    }

    onCloseFlowable() {
        $('.popup-mask').hide(); $('.flowable_operate_block').hide();
    }
}

CustomerMaterialInfoFormController.components = {
    ...FormController.components, FlowableApprovalDialog, TransferFlowableDialog,
};
CustomerMaterialInfoFormController.template = "customerMaterialInfo.FormView";

registry.category("views").add("customerMaterialInfoFormView", {
    ...formView, Controller: CustomerMaterialInfoFormController, Model: RelationalModel,
});
```

### XML 模板（customer_material_info_form.xml）

```xml
<?xml version="1.0" encoding="UTF-8"?>
<templates xml:space="preserve">
    <!-- 继承公共模板，替换插槽添加提交审批人选择弹窗 -->
    <t t-name="customerMaterialInfo.FormView"
       t-inherit="xc_flowable.FlowableFormButtons"
       t-inherit-mode="primary" owl="1">
        <xpath expr="//t[@t-call='xc_flowable.FlowableFormButtonsSlot']" position="replace">
            <t t-call="customerMaterialInfo.FlowableSlot"/>
        </xpath>
    </t>

    <t t-name="customerMaterialInfo.FlowableSlot"
       t-inherit="xc_flowable.FlowableFormButtonsSlot"
       t-inherit-mode="primary" owl="1">
        <xpath expr="//div" position="replace">
            <div class="flowable_operate_block submit_block">
                <header style="font-size: 24px; font-weight: 600;">提交</header>
                <hr/>
                <content class="flowable_operate_block_content">
                    <div class="d-flex align-items-center">
                        <span style="color: red; margin-right: 2px;">*</span>
                        <span>审批人员:</span>
                        <div id="submit_person" style="width: 330px; margin-left: 15px;"/>
                    </div>
                </content>
                <footer style="margin-top: 15px; float: right;">
                    <button class="btn btn-success" t-on-click="onSubmitFlowable">确定</button>
                    <button class="btn btn-white ml4" t-on-click="onCloseFlowable">取消</button>
                </footer>
            </div>
        </xpath>
    </t>
</templates>
```

### 视图定义（customer_material_io_views.xml）

```xml
<record id="xc_production_customer_material_io_form_view" model="ir.ui.view">
    <field name="name">客供料出入库管理表单</field>
    <field name="model">xc.customer.material.io.info</field>
    <field name="arch" type="xml">
        <form string="客供料出入库管理" js_class="customerMaterialInfoFormView">
            <header/>
            <sheet>
                <field name="csm_flowable_id" invisible="1"/>
                <field name="io_order_no" invisible="1"/>
                <h3 style="font-weight: bold;">基本信息</h3>
                <hr style="border-bottom-color: black !important;"/>
                <group>
                    <field name="io_type"/>
                    <!-- 其他业务字段... -->
                </group>
                <notebook>
                    <page string="流程日志">
                        <widget name='flowable_task_log'
                                flowable_model="xc.csm.flowable"
                                flowable_id="csm_flowable_id"
                                business_no="io_order_no"/>
                    </page>
                </notebook>
            </sheet>
        </form>
    </field>
</record>
```

## 常见问题排查

### 问题 1：按钮不显示

**排查步骤**：
1. 检查 form 视图 XML 是否包含 `<header>` 和 `<div class="o_statusbar_buttons"/>`
2. 检查 `js_class` 是否正确声明并注册到 registry
3. 打开浏览器控制台，检查是否有 JS 错误
4. 检查 `__manifest__.py` 中是否正确注册了 JS 和 XML 文件
5. 清除浏览器缓存，重启 Odoo 服务（`-u <module>`）

### 问题 2：点击按钮报错 "Cannot read property of undefined"

**原因**：`stateData` 未在 `useFlowableButton` 之前初始化

```javascript
setup() {
    super.setup();
    // 必须先初始化 stateData
    this.stateData = useState({ code_type: '', transfer_flowable: { userList: [], operateType: '' } });
    // 再调用 useFlowableButton
    useFlowableButton(this, { ... });
}
```

### 问题 3：提交后按钮状态未更新

**原因**：`flowableIdField` 配置错误或字段未在视图中声明

```javascript
// 确保 flowableIdField 与模型字段名一致
useFlowableButton(this, { flowableIdField: "sn_flowable_id" });
```

```xml
<!-- 确保字段在视图中声明 -->
<field name="sn_flowable_id" invisible="1"/>
```
