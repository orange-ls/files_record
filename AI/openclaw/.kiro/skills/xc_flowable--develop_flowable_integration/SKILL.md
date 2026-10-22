---
name: develop_flowable_integration
description: 业务模块集成 xc_flowable 工作流引擎的完整开发指南。包含从零开始将审批流程接入业务模块的全部步骤：模型继承 mixin.bpmn.audit、流程生命周期钩子实现（do_before/do_action/do_after）、@flowable_shunt 多版本路由、审批按钮动态渲染、action_param 流程参数组装、消息通知配置、权限配置、前端 ORM RPC 调用等。当用户提到"集成工作流"、"接入审批流程"、"新模块加审批"、"flowable集成"、"添加审批功能"、"工作流对接"、"审批流开发"、"mixin.bpmn.audit 怎么用"、"flowable_shunt 怎么用"、"新建审批模型"时，务必使用此技能。即使用户只是简单说"给xx模块加个审批流程"也应该触发此技能。
---

# 业务模块集成 xc_flowable 工作流引擎 — 完整开发指南

> 本指南基于 xc_production（客供料出入库）、xc_dboms、xc_borrow 等已上线模块的真实集成代码提炼而成，覆盖从模型定义到前端交互的全链路。

## 参考资料索引

本 skill 按照渐进式加载设计，SKILL.md 包含核心集成流程，详细参考资料按需读取：

| 文件 | 内容 | 何时读取 |
|------|------|----------|
| `references/mixin-bpmn-audit-api.md` | mixin.bpmn.audit 完整 API（字段、方法签名、常量） | 需要查看 mixin 提供了哪些字段或方法时 |
| `references/flowable-shunt-guide.md` | @flowable_shunt 多版本路由详细说明 | 需要实现流程版本升级、多版本并存时 |
| `references/frontend-integration.md` | 前端集成完整指南：useFlowableButton mixin、公共组件、XML 模板继承、审批日志 widget、视图与菜单配置 | 实现前端审批交互时 |
| `references/real-world-examples.md` | xc_production、xc_dboms、xc_borrow 真实案例代码片段 | 需要参考已上线模块的具体实现时 |
| `references/checklist.md` | 完整集成检查清单 | 开发完成后做最终验收时 |
| `references/faq.md` | 常见问题与解决方案 | 遇到具体问题时 |

## 开发输入

使用此技能进行审批流开发时，需要用户提供以下输入：

1. Flowable BPMN 流程图文件（.bpmn20.xml）或流程图截图
   — 从中提取节点名称、节点 code、审批人参数 key、并签/或签类型、网关分支条件等
2. 需求描述
   — 业务背景、每个审批节点的业务逻辑（提交前校验、通过后处理、驳回后处理等）

拿到这两样数据后，按以下步骤开展：
1. 分析流程图，梳理出所有审批节点及其审批人配置方式
2. 向人工确认 `business_no` 和 `business_id` 对应业务模型的哪个字段
3. 检查业务模型是否已有 `process_status` 字段：
   - 如果已有，确认其枚举值定义
   - 如果没有，自动为业务模型创建默认的 `process_status` 字段（见下方默认定义）
4. 按本指南的步骤逐步实现后端模型、前端交互、菜单配置等

### process_status 默认定义

当业务模型没有 `process_status` 字段时，必须在业务模型中添加以下默认定义：

```python
PROCESS_STATUS_SELECT = [('0', '草稿'), ('1', '流程中'), ('2', '已完成')]

process_status = fields.Selection(
    PROCESS_STATUS_SELECT, string='流程状态', default='0', index=True,
    help='审批流程状态：0-草稿（未提交）、1-流程中（审批中）、2-已完成（审批通过）'
)
```

## 集成架构总览

```
业务模块（如 xc_sn）
├── models/
│   ├── xc_sn_flowable_v1.py      ← 继承 mixin.bpmn.audit 的审批模型（V1版本）
│   └── xc_sn_flowable_v2.py      ← 可选：新版本流程（继承 V1，用 @flowable_shunt）
├── static/src/views/
│   ├── xc_sn_form.js             ← OWL FormController（使用 useFlowableButton mixin）
│   └── xc_sn_form.xml            ← XML 模板（继承 xc_flowable.FlowableFormButtons）
├── views/
│   └── xc_sn_views.xml           ← form/tree 视图、Action、菜单定义
├── security/
│   ├── ir.model.access.csv        ← flowable 模型权限
│   └── security_group.xml         ← 权限组定义
└── __manifest__.py                ← depends 中加入 'xc_flowable'
```

## 核心概念

xc_flowable 的集成核心是 `mixin.bpmn.audit` 抽象模型。业务模块创建一个新的
ORM 模型继承它，就自动获得完整的审批流程能力。这个 mixin 提供了：

- 审批状态管理（pending/complete/reject/cancel/suspend）
- 流程操作方法（submit/agree/reject/rollback/transfer/signature/cancel/suspend/activate）
- 审批人追踪（current_spr/approved_spr + Many2many 字段用于待办过滤）
- 任务管理（task_ids 关联 bpmn.task）
- 消息通知（邮件/飞书/OA/Odoo 系统消息）

业务模块只需要实现三个钩子方法和几个配置方法，就能完成集成。
详细的 mixin 字段和方法列表见 `references/mixin-bpmn-audit-api.md`。

## 第一步：模块依赖配置

在 `__manifest__.py` 的 `depends` 列表中添加 `'xc_flowable'`：

```python
{
    'name': '你的模块名',
    'depends': ['base', 'xc_flowable'],
    'data': [
        'security/security_group.xml',
        'security/ir.model.access.csv',
    ],
    'assets': {
        'web.assets_backend': [
            'xc_sn/static/src/views/**/*',
        ],
    },
}
```

## 第二步：创建审批流程模型（核心）

在 `models/` 下创建 flowable 模型文件，继承 `mixin.bpmn.audit`。
这是集成的核心，需要实现以下内容：

### 模型定义模板

```python
import logging
from odoo import fields, models
from odoo.tools import config
from xc_addons.xc_common.ajax_result import AjaxResult

_logger = logging.getLogger(__name__)


class XcSnFlowableV1(models.Model):
    _name = "xc.sn.flowable"           # 模型名：xc.{模块}.flowable
    _inherit = ['mixin.bpmn.audit']     # 继承审批 mixin
    _description = 'SN审批'

    # ==================== 消息配置 ====================
    _message_subject = "信创XX系统通知"
    _message_system_name = 'SN审批'

    # ==================== 流程类型定义 ====================
    # Key 命名规范：model 的 _name 中的点替换为下划线，加上自定义业务标识
    # 一个 flowable 模型可以通过 PROCESS_TYPE 支持多种审批流程
    PROCESS_TYPE = [
        ('xc_sn_flowable', 'SN审批'),
    ]

    # ==================== 表字段 ====================
    process_type = fields.Selection(PROCESS_TYPE, index='trigram')
    business_record_id = fields.Many2one(
        "xc.sn.record", string="业务单据", ondelete='set null'
    )
    # 用于待办/已办过滤的 Many2many 字段
    current_spr_ids = fields.Many2many(
        comodel_name='res.users', string='当前审批人',
        index=True, column1='process_id',
        relation='xc_sn_flowable_current_spr_rel',
        column2='current_spr_id'
    )
    approved_spr_ids = fields.Many2many(
        comodel_name='res.users', string='已审批的审批人',
        index=True, column1='process_id',
        relation='xc_sn_flowable_approved_spr_rel',
        column2='approved_spr_id'
    )
```

### 三个生命周期钩子（必须实现）

```python
    def do_before(self, kwargs):
        """
        流程操作前的业务逻辑。在 parent_do_action() 执行前调用。
        职责：从 kwargs 提取参数、构建消息 URL、执行业务校验。
        """
        # --- 必传参数 ---
        self.business_id = kwargs.get("business_id", False)
        self.business_no = kwargs.get("business_no", False)
        self.code = kwargs.get("code", False)
        self.process_type = kwargs.get("process_type", False)

        # --- 可选参数（仅特定操作时前端才传） ---
        self.toNode = kwargs.get("toNode", False)
        self.reject_type = kwargs.get("reject_type", False)
        self.signature_user = kwargs.get("signature_user", False)
        self.signature_type = kwargs.get("signature_type", False)
        self.assignee_id = kwargs.get("assignee_id", False)
        self.message = (
            kwargs['message']
            if kwargs.get("message") and len(kwargs['message']) > 0
            else '通过'
        )

        # --- 消息跳转 URL ---
        menu_id = self.env.ref('xc_sn.xc_sn_root_menu').id
        action_id = self.env.ref('xc_sn.xc_sn_todo_action').id
        model = "xc.sn.flowable"
        self.message_jump_url = config['flowable_todo_url'].format(
            menu_id, action_id, model, self.business_id
        )

        # --- 业务字段赋值（用于消息通知） ---
        if self.code == self.button_submit:
            record = self._get_business_record(self.business_no)
            self.crm_no = record.crm_no if hasattr(record, 'crm_no') else ''
            self.project_name = record.project_name if hasattr(record, 'project_name') else ''
        else:
            self.crm_no = self.business_record_id.crm_no if self.business_record_id else ''
            self.project_name = self.business_record_id.project_name if self.business_record_id else ''
        self.price_apply_no = ''

        # --- 业务校验 ---
        if self.code == self.button_submit:
            self._submit_check(kwargs)
        if self.code == self.button_agree:
            self._agree_check(kwargs)

    def do_action(self, **kwargs):
        """
        流程操作主入口。前端通过 ORM RPC 调用此方法。
        标准流程：do_before → parent_do_action → do_after
        """
        self.do_before(kwargs)
        flowable = self.parent_do_action()
        try:
            msg = flowable.do_after(kwargs)
        except Exception as e:
            _logger.error("审批业务数据处理失败：%s", str(e))
            return AjaxResult.error(msg="审批业务数据处理失败：%s" % str(e))
        return AjaxResult.success(msg=msg)

    def do_after(self, kwargs=None):
        """
        流程操作后的业务逻辑。在 parent_do_action() 执行后调用。
        注意：此时 self 是 parent_do_action 返回的 flowable 记录。
        """
        msg = ""
        if self.code == self.button_submit:
            msg = "提交成功"
            self._submit_after()
        if self.code == self.button_agree:
            msg = "通过成功"
            self._agree_after()
        if self.code == self.button_reject:
            msg = "驳回成功"
            if not self.is_opt_signature:
                self._reject_after(kwargs)
        if self.code == self.button_rollback:
            msg = "回退成功"
        if self.code == self.button_signature:
            msg = "加签成功"
        if self.code == self.button_transfer:
            msg = "转办成功"
        if self.code == self.button_cancel:
            msg = "撤回成功"
            self._cancel_after()
        return msg
```

### 配置方法（按需重写）

```python
    def action_param(self):
        """
        组装流程参数。父类已处理 message、code、process_type、toNode
        以及 bpmn.task.node 中配置的审批人参数。
        子类重写添加业务特有的流程变量（如分支判断条件）。
        """
        var = super().action_param()
        # 示例：var.append({'name': 'need_extra_review', 'value': 1})
        return var

    def get_flowable_button(self, business_no):
        """
        根据流程状态和当前用户角色，返回前端应显示的审批操作按钮列表。
        每个按钮是 dict：{"name": "显示名", "code": "操作码", "class": "CSS类"}
        process_status 默认枚举：'0'-草稿, '1'-流程中, '2'-已完成
        """
        STATUS_DRAFT = '0'       # 草稿
        STATUS_PROCESSING = '1'  # 流程中
        # STATUS_NORMAL = '2'    # 已完成（审批通过）
        buttons = []
        record = self._get_business_record(business_no)
        process_status = record.process_status if record else STATUS_DRAFT

        if process_status == STATUS_DRAFT:
            buttons.append({"name": "提交", "code": self.button_submit,
                            "class": "div_button div_btn_success div_header_button"})
            buttons.append({"name": "暂存", "code": "temp_save",
                            "class": "div_button div_btn_white div_header_button"})

        if process_status == STATUS_PROCESSING and self.is_current_approver:
            buttons.append({"name": "通过", "code": self.button_agree,
                            "class": "div_button div_btn_success div_header_button"})
            buttons.append({"name": "转办", "code": self.button_transfer,
                            "class": "div_button div_btn_white div_header_button"})
            if self.current_node_name.find("加签") < 0:
                buttons.append({"name": "驳回", "code": self.button_reject,
                                "class": "div_button div_btn_red div_header_button"})
                buttons.append({"name": "加签", "code": self.button_signature,
                                "class": "div_button div_btn_white div_header_button"})
            # 回退按钮（普通回退）
            buttons.append({"name": "回退", "code": self.button_rollback,
                            "class": "div_button div_btn_white div_header_button"})

        if process_status == STATUS_PROCESSING and self.env.uid == self.create_uid.id:
            buttons.append({"name": "撤回", "code": self.button_cancel,
                            "class": "div_button div_btn_white div_header_button"})

        button_sort = ['submit', 'agree', 'reject', 'rollback',
                       'transfer', 'signature', 'suspend', 'activate', 'cancel']
        buttons.sort(key=lambda x: button_sort.index(x['code'])
                     if x['code'] in button_sort else len(button_sort))
        return buttons

    def get_decide_data(self, business_no):
        """前端页面初始化时调用，返回流程相关数据。"""
        data = {
            'get_task_log': self.get_task_log(),
            'get_flowable_button': self.get_flowable_button(business_no),
            'is_current_spr': self.is_current_approver,
            'current_node_code': self.current_node_code,
            'current_node_name': self.current_node_name,
        }
        return AjaxResult.success(msg="查询成功", data=data)
```

#### toNode：回退到指定节点

按钮的 dict 中有一个隐藏字段 `toNode`，用于回退操作时指定回退到哪个节点。
当流程有多个可回退目标时，可以为同一个 `button_rollback` code 创建多个按钮，
通过不同的 `toNode` 值区分回退目标。前端会将 `toNode` 作为 `data-` 属性渲染到按钮上，
点击时自动传入 `do_action` 的 kwargs。

真实案例（xc_borrow 251121 版本）：

```python
if self.current_node_code == 'NODE_CPJLSP':
    buttons.append({"name": "回退至配置BOM", "code": self.button_rollback,
                    "toNode": 'NODE_PZBOM',
                    "class": "div_button div_btn_white div_header_button"})
    buttons.append({"name": "回退至物料计划", "code": self.button_rollback,
                    "toNode": 'NODE_WLJQFK',
                    "class": "div_button div_btn_white div_header_button"})
```

### 业务回调方法（按需实现）

```python
    def _get_business_record(self, business_no):
        """根据业务单号查询业务单据记录"""
        return self.env['xc.sn.record'].search(
            [('record_no', '=', business_no)], limit=1
        )

    def _submit_check(self, kwargs):
        """提交前业务校验"""
        pass

    def _agree_check(self, kwargs):
        """通过前业务校验"""
        pass

    def _submit_after(self):
        """提交后更新业务单据状态为'流程中'"""
        record = self._get_business_record(self.business_no)
        record.write({'process_status': '1', 'flowable_id': self.id})
        self.write({'business_record_id': record.id})

    def _agree_after(self):
        """通过后：若流程全部完成，更新业务单据状态为'已完成'"""
        if self.audit_status == BpmnTask.status_complete:
            self.business_record_id.write({'process_status': '2'})

    def _reject_after(self, kwargs=None):
        """驳回后更新业务单据状态为'草稿'（可重新提交）"""
        self.business_record_id.write({'process_status': '0'})

    def _cancel_after(self):
        """撤回后更新业务单据状态为'草稿'（可重新提交）"""
        self.business_record_id.write({'process_status': '0'})
```

## 驳回类型机制

驳回操作需要用户选择驳回类型（如"退回修改"、"终止流程"等），整个流程如下：

1. 后端在 `ir.config_parameter` 中配置驳回类型列表，key = `{模型名}_flowable_reject_type`
2. 前端驳回前调用 `get_reject_type()` 获取可选类型列表（`useFlowableButton` mixin 已内置此逻辑）
3. 用户选择后通过 `reject_type` 参数传给 `do_action`
4. mixin 自动将 `reject_type` 写入 bpmn.task 记录，并支持用户自定义创建新类型
5. 业务模块在 `_reject_after()` 中通过 `self.message_param.get('reject_type')` 获取驳回类型

完整的前后端实现细节见 `references/frontend-integration.md` 的"驳回类型选择"章节。

## 第三步：前端集成（使用 useFlowableButton 公共组件）

`xc_flowable` 提供了完整的前端公共组件，业务模块只需引入 `useFlowableButton` mixin 即可一行接入全部审批按钮能力。

### 公共组件清单（xc_flowable 提供）

| 资源 | 路径 | 说明 |
|------|------|------|
| `useFlowableButton` | `xc_flowable/static/src/views/flowable_button_mixin/` | JS Mixin，封装全部审批按钮逻辑 |
| `xc_flowable.FlowableFormButtons` | 同上目录 `flowable_form_buttons.xml` | XML 模板，内置 popup-mask + 审批弹窗 + 转办弹窗 + 业务扩展插槽 |
| `FlowableApprovalDialog` | `xc_flowable/static/src/views/flowable_approval_dialog/` | 通过/驳回/回退/撤回弹窗 |
| `TransferFlowableDialog` | `xc_flowable/static/src/views/transfer_flowable_dialog/` | 转办/加签弹窗 |

### 3.1 JS Controller

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

        // 一行接入全部审批按钮能力
        useFlowableButton(this, {
            flowableModel: "xc.sn.flowable",       // flowable 模型名
            processType: "xc_sn_flowable",          // 流程类型
            businessNoField: "record_no",           // 业务单号字段名
            flowableIdField: "sn_flowable_id",      // 关联 flowable 的 Many2one 字段名
        });
    }

    // 暂存（不走 flowable，业务模块自行实现）
    async temp_saveRecord() {
        await this.saveButtonClicked();
    }
}

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

### 3.2 XML 模板（继承公共模板）

业务模块的 XML 模板继承 `xc_flowable.FlowableFormButtons`，该公共模板已包含
popup-mask、FlowableApprovalDialog、TransferFlowableDialog 和业务扩展插槽。

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
    <t t-name="xc_sn_form.FormButtons"
       t-inherit="xc_flowable.FlowableFormButtons"
       t-inherit-mode="primary" owl="1">
        <xpath expr="//t[@t-call='xc_flowable.FlowableFormButtonsSlot']" position="replace">
            <t t-call="xc_sn_form.FlowableSlot"/>
        </xpath>
    </t>

    <t t-name="xc_sn_form.FlowableSlot"
       t-inherit="xc_flowable.FlowableFormButtonsSlot"
       t-inherit-mode="primary" owl="1">
        <xpath expr="//div" position="replace">
            <!-- 业务模块自定义弹窗内容 -->
            <div class="flowable_operate_block submit_block">
                <!-- 例如：提交时选择审批人的弹窗 -->
            </div>
        </xpath>
    </t>
</templates>
```

### 3.3 Form 视图 XML

```xml
<form string="SN记录" js_class="xc_sn_form_view">
    <header>
        <div class="o_statusbar_buttons"/>
        <field name="process_status" widget="statusbar" options="{'clickable': '0'}"/>
    </header>
    <sheet>
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
```

### 3.4 操作前钩子（before hooks）

`useFlowableButton` 内置了操作前钩子机制，业务模块可定义 `before{Action}` 方法进行校验，
返回 `false` 中断操作。钩子方法支持异步（async）。

| 钩子方法 | 触发时机 |
|----------|----------|
| `beforeSubmit()` | 提交前 |
| `beforeAgree()` | 通过前 |
| `beforeReject()` | 驳回前 |
| `beforeRollback()` | 回退前 |
| `beforeCancel()` | 撤回前 |
| `beforeTransfer()` | 转办前 |
| `beforeSignature()` | 加签前 |
| `beforeFlowableConfirm(codeType, data)` | 弹窗确认后、调用后端前 |

使用示例：

```javascript
// 在 setup() 中定义钩子
this.beforeSubmit = async () => {
    const saved = await this.saveButtonClicked();
    if (!saved) return false;
    // 不返回 false，继续执行 submitRecord()
};
```

详细的前端集成指南（包括完整示例、常见问题排查）见 `references/frontend-integration.md`。

## 第四步：权限配置

flowable 模型需要给所有登录用户完整的 CRUD 权限：

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_xc_sn_flowable,xc.sn.flowable,model_xc_sn_flowable,base.group_user,1,1,1,1
```

## 第五步：业务模型添加审批展示字段 + 视图配置

业务模型需要添加 compute 字段从 flowable 记录中读取审批信息，用于 tree 视图展示。
审批待办/已办菜单的 action 的 `res_model` 直接使用业务模型，`view_mode` 为 `tree,form`，
这样点击列表行时自然复用业务模型的 form 视图，无需单独创建审批专用的 form。

### 业务模型添加审批展示字段

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

### tree 视图展示审批信息

```xml
<tree>
    <!-- 业务字段... -->
    <field name="process_status" string="流程状态"/>
    <field name="current_node_name" string="处理节点"/>
    <field name="current_spr" string="处理人"/>
    <!-- 隐藏字段（前端 JS 可能需要） -->
    <field name="current_node_code" invisible="1"/>
    <field name="is_current_approver" invisible="1"/>
</tree>
```

### 待办/已办 Action（复用业务模型视图）

待办/已办 action 的 `res_model` 直接使用业务模型，`view_mode` 为 `tree,form`。
只指定 `view_id`（tree 视图），不指定 form 视图，Odoo 自动使用业务模型的默认 form 视图：

```xml
<!-- 待我处理：通过 flowable 的 current_spr_ids 过滤 -->
<record id="xc_sn_process_todo_action" model="ir.actions.act_window">
    <field name="name">待我处理</field>
    <field name="res_model">xc.sn.record</field>
    <field name="view_mode">tree,form</field>
    <field name="target">current</field>
    <field name="context">{'view_type': 'todo'}</field>
    <field name="view_id" ref="xc_sn_record_tree"/>
    <field name="domain">[('sn_flowable_id.current_spr_ids', 'in', [uid])]</field>
</record>

<!-- 我已处理：通过 flowable 的 approved_spr_ids 过滤 -->
<record id="xc_sn_process_done_action" model="ir.actions.act_window">
    <field name="name">我已处理</field>
    <field name="res_model">xc.sn.record</field>
    <field name="view_mode">tree,form</field>
    <field name="target">current</field>
    <field name="context">{'view_type': 'done'}</field>
    <field name="view_id" ref="xc_sn_record_tree"/>
    <field name="domain">[('sn_flowable_id.approved_spr_ids', 'in', [uid])]</field>
</record>
```

完整的视图、菜单、权限组配置见 `references/frontend-integration.md` 的"菜单与 Action 配置"章节。

## 第六步：@flowable_shunt 多版本路由（可选）

当流程图升级但旧流程实例仍在运行时，需要多版本并存。
详细说明见 `references/flowable-shunt-guide.md`。

## 第八步：Dashboard 首页待办跳转链接

系统首页驾驶舱（xc_dashboard）展示用户的待办/已办审批任务列表，点击任务需要跳转到对应的业务表单。
新集成的 flowable 模型必须在 `xc_addons/xc_dashboard/controllers/flowable_controller.py` 的
`flowable_data` 方法中添加跳转链接映射。

在该方法的 `if/elif` 链中，按照已有模式添加新的分支：

```python
elif data['flowable_model_name'] == 'xc.csm.flowable':  # 客供料出入库
    menu_id = business_flowable.env.ref('xc_production.xc_production_process_menu').id
    action_id = business_flowable.env.ref('xc_production.csm_io_todo_action').id
    data['jump_url'] = config['flowable_todo_url'].format(menu_id, action_id, "xc.customer.material.io.info", business_flowable.business_id)
```

其中：
- `flowable_model_name`：flowable 模型的 `_name`
- `menu_id`：业务模块"我的流程"父菜单的 XML ID
- `action_id`：待我处理 action 的 XML ID
- 第三个参数：业务模型的 `_name`（注意不是 flowable 模型名）
- `business_id`：flowable 记录上的 business_id 字段

已注册的 flowable 模型跳转映射：

| flowable 模型 | 业务模块 | 菜单 XML ID | Action XML ID | 业务模型 |
|---------------|----------|-------------|---------------|----------|
| `xc.dboms.flowable` (sales_order/sales_delivery_note) | xc_dboms | `xc_dboms.xc_sales_order_direct_menu` | `xc_dboms.xc_sales_order_direct_action` | `xc.sales.order` |
| `xc.dboms.flowable` (其他) | xc_dboms | `xc_dboms.xc_project_distribution_menu` | `xc_dboms.xc_project_distribution_action` | `xc.project.distribution` |
| `xc.borrow.flowable` | xc_borrow | `xc_borrow.xc_borrow_menu` | `xc_borrow.xc_borrow_my_todo_not_do_action` | `xc.borrow.flowable` |
| `material.dump.flowable` | xc_borrow | `xc_borrow.xc_borrow_menu` | `xc_borrow.material_dump_my_todo_not_do_action` | `material.dump.flowable` |
| `production.virtual.batch.flowable` | xc_production | `xc_production.xc_production_virtual__batch_sec_menu` | `xc_production.xc_production_virtual_batch_action` | `production.virtual.batch` |
| `production.batch.flowable` | xc_production | `xc_production.xc_production_batch_todo_menu` | `xc_production.xc_production_batch_todo_action` | `production.batch` |
| `production.dump.flowable` | xc_production | `xc_production.xc_production_process_menu` | `xc_production.production_dump_todo_action` | `production.dump.info` |
| `xc.sales.contract.flowable` | xc_dboms | `xc_dboms.xc_dboms_root_menu` | `xc_dboms.xc_contract_process_todo_action` | `xc.sales.contract.flowable` |
| `xc.po.application.flowable` | xc_dboms | `xc_dboms.xc_dboms_root_menu` | `xc_dboms.xc_po_process_todo_action` | `xc.po.application.flowable` |
| `xc.csm.flowable` | xc_production | `xc_production.xc_production_process_menu` | `xc_production.csm_io_todo_action` | `xc.customer.material.io.info` |

## 第七步：Flowable 流程定义配置

在bpmn_task_node中审批人有三种配置方式：

1. **固定审批人** — `assignee_value` 直接填 ITCode（逗号分隔）
2. **动态审批人** — `assignee_python_code` 编写 Python 代码动态计算
3. **前一节点人工指定** — `assignee_value` 和 `assignee_python_code` 都为空，
   由当前审批人在"通过"时手动选择下一级审批人。
   前端选择下级审批人的组件会直接返回审批人数组（无需后端 split），
   后端在 `action_param()` 中直接将数组传给 Flowable 引擎。
   完整的前后端实现细节见 `references/frontend-integration.md` 的"指定下一级审批人"章节。

详细配置说明和示例见 `references/real-world-examples.md`。

## 开发完成后

使用 `references/checklist.md` 中的检查清单验证集成是否完整。
遇到问题可查阅 `references/faq.md`。
