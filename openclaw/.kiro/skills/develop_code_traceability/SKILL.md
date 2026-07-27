---
name: develop_code_traceability
description: 需求追溯代码规范知识库，包含代码与需求文档（requirements.md、tasks.md）的双向追溯标注规范：@requirement/@task/@businessRule 标签使用、函数/类/Controller/行内注释的标注格式、多版本迭代标注、docstring 业务逻辑说明要求、追溯矩阵维护规范。当开发涉及 xc_addons 目录下的任何代码编写、需求追溯标注、@requirement/@task 标签添加、docstring 编写规范、traceability-matrix.md 维护、代码审查检查清单时，务必使用此技能。
---

# 需求追溯代码规范

本规范确保AI生成的代码能够与需求文档（requirements.md）、任务文档（tasks.md）建立双向追溯关系。

**适用范围：** 仅适用于 `xc_addons` 目录下的 Python 后端代码（models、controllers、wizards 等）。JS、XML、SCSS 等前端代码只需遵循常规代码注释规范，无需进行需求追溯标注。

---

## 核心原则

1. 每个业务函数/方法的 docstring 中必须包含对应的需求编号和任务编号, 并且docstring 不仅要描述"做了什么"，更要说明"为什么这样做"——即业务背景、设计决策和关键约束
2. 若同一个方法经历多次版本迭代，docstring 中需按时间顺序记录每个版本的需求编号和任务编号
3. 关键业务逻辑的行内注释中需标注对应的需求编号
4. 每个 spec 版本目录下应维护一份追溯矩阵文件

---

## 需求标识规范

### 标识格式

标识必须**全局唯一**，由当前分支名和文档编号组合而成：

- 需求标识：`{branch_name}-REQ-{需求编号}`
- 任务标识：`{branch_name}-TASK-{任务编号}`

其中：
- `branch_name`：当前 Git 分支名称（与 `.kiro/specs/` 下的目录名一致）
- 需求编号：对应 `requirements.md` 中的编号（如 `1`, `1.1`, `2`）
- 任务编号：对应 `tasks.md` 中的任务序号（如 `1`, `2`, `3`）

### 示例

```
zk-kiro-dev-standard-REQ-1.1
zk-kiro-dev-standard-TASK-3
```

---

## 代码注释规范

### 1. 函数/方法级别标注（必须）

所有新增代码或修改的代码，必须在 docstring 中使用 `@requirement` 和 `@task` 标注关联的需求和任务。

docstring 不仅要描述"做了什么"，更要说明"为什么这样做"——即业务背景、设计决策和关键约束

```python
def create_borrow_apply(self, vals):
    """创建借用申请单

    业务背景：借用申请是样机管理的入口环节，每笔借用必须关联 CRM 立项编号，
    以便后续与 CRM 系统进行借用-项目的交叉核对和成本归集。
    借用单号采用自动生成策略（年份+流水号），确保全局唯一且可按时间排序，
    便于仓库和财务按单号快速检索。

    @requirement zk-borrow-feature-REQ-1.1
    @task zk-borrow-feature-TASK-2
    """
    if not vals.get('crm_no'):
        raise ValidationError("CRM立项编号不能为空")
    vals['borrow_no'] = self._generate_borrow_no()
    return super().create(vals)
```

### 2. 类/模块级别标注

当一个类整体服务于某个需求时，在类的 docstring 中标注该需求。适用于新增模型的场景。

```python
class XcBorrowApply(models.Model):
    """借用申请单模型

    管理借用申请的完整生命周期，包括创建、审批、归还等流程。
    设计为独立模型而非继承 sale.order，是因为借用业务与销售流程存在本质差异：
    借用不产生收入确认，需要独立的归还跟踪和超期处理机制，
    且审批流程需要对接 OA 系统而非走 Odoo 原生的销售审批。

    @requirement zk-borrow-feature-REQ-1
    @requirement zk-borrow-feature-REQ-2
    """
    _name = "xc.borrow.apply"
    _description = "借用单"
```

### 3. 行内注释标注（关键逻辑）

对于实现特定业务规则的关键代码行，使用行内注释标注对应的需求编号。仅在逻辑不易理解或涉及特殊业务规则时使用，避免过度标注。

```python
def _check_borrow_limit(self):
    # 营销类借用最大周期限制为180天，因为营销样机属于高价值资产，
    # 长期外借会导致资产折旧风险和库存周转率下降 @requirement zk-borrow-feature-REQ-3.2
    if self.borrow_type == '1' and self.test_cycle > 180:
        raise ValidationError("营销类借用周期不能超过180天")

    # 非营销类高金额借用需要额外审批，这是财务风控要求：
    # 超过5万元的非营销借用需要部门总监+财务双重审批 @requirement zk-borrow-feature-REQ-3.3
    if self.borrow_type == '0' and self.amount > 50000:
        self._trigger_extra_approval()
```

### 4. Controller 级别标注

API 接口同样需要标注对应的需求和任务。

```python
class XcBorrowController(http.Controller):

    @http.route('/api/borrow/create', type='json', auth='user', methods=['POST'])
    def create_borrow(self, **kwargs):
        """创建借用申请接口

        提供给移动端和第三方系统调用的借用创建入口。
        使用 JSON-RPC 而非 REST 风格，是为了与 Odoo 原生 RPC 机制保持一致，
        降低前端对接成本。接口内部会复用 model 层的校验逻辑，
        避免 controller 和 model 出现重复的业务规则校验。

        @requirement zk-borrow-feature-REQ-1.1
        @task zk-borrow-feature-TASK-2
        """
        # 业务逻辑...
```

### 5. 多版本迭代标注

当同一个方法在不同版本中被修改时，按时间顺序在 docstring 中追加标注，保留历史记录。

```python
def compute_borrow_amount(self):
    """计算借用金额

    借用金额 = 明细行的 单价×数量 之和，再扣除折扣。
    采用实时计算而非存储字段，是因为明细行会频繁变动（增删物料、调整数量），
    存储字段会导致大量 write 触发和一致性维护成本。
    折扣率由销售政策模块统一下发，此处仅做应用，不做折扣规则判断，
    以保持职责单一。

    @requirement zk-borrow-v1-REQ-2.1  -- 初始版本：基础金额计算
    @requirement zk-borrow-v2-REQ-1.3  -- V2迭代：增加折扣逻辑
    @task zk-borrow-v1-TASK-4
    @task zk-borrow-v2-TASK-2
    """
    base_amount = sum(line.unit_price * line.quantity for line in self.line_ids)
    # 折扣逻辑：折扣率来源于销售政策，此处直接应用，
    # 不在借用模块内维护折扣规则 @requirement zk-borrow-v2-REQ-1.3
    if self.discount_rate:
        base_amount *= (1 - self.discount_rate)
    self.total_amount = base_amount
```

### 注释风格

- 行内注释：与代码同行，用 `#` 加两个空格隔开
- 块注释：独立一行，用 `#` 开头，描述下方代码块的整体逻辑
- 文档字符串：类和公共方法使用三引号 `"""`，私有方法可选

### docstring 业务逻辑说明要求

docstring 的核心价值在于传递"为什么"，而非复述代码本身。具体要求：

1. 说明业务背景：这段代码服务于什么业务场景？解决什么业务问题？
2. 解释设计决策：为什么选择这种实现方式？有哪些备选方案被排除？理由是什么？
3. 标注关键约束：业务规则的来源（如财务风控要求、外部系统限制）、阈值的依据
4. 避免无意义复述：不要写"根据参数创建记录"这类仅复述代码行为的描述

对比示例：

```python
# ❌ 不好的写法：仅描述"做了什么"，读代码就能看出来
def _sync_to_sap(self):
    """同步数据到SAP

    调用SAP接口将借用单数据同步到SAP系统。

    @requirement zk-borrow-feature-REQ-4.1
    @task zk-borrow-feature-TASK-6
    """

# ✅ 好的写法：说明"为什么这样做"，传递代码背后的业务逻辑和决策
def _sync_to_sap(self):
    """同步借用单数据到SAP

    借用单审批通过后需同步至 SAP 生成物料凭证，以便财务进行资产出库核算。
    采用异步推送而非实时调用，是因为 SAP 接口响应较慢（平均 3-5s），
    同步调用会阻塞用户的审批操作体验。
    失败时记录日志并标记状态为"待重试"，由定时任务每30分钟批量重推，
    最多重试3次后转人工处理，避免无限重试占用系统资源。

    @requirement zk-borrow-feature-REQ-4.1
    @task zk-borrow-feature-TASK-6
    """
```

---

## 追溯矩阵维护

### 存放位置

每个 spec 版本目录下应包含 `traceability-matrix.md`，路径为：

```
.kiro/specs/{modulename}/{版本号}/traceability-matrix.md
```

### 矩阵模板

```markdown
# 需求 → 代码追溯矩阵

## 模块信息
- 模块名称：xc_borrow
- 分支名称：zk-borrow-feature
- 更新日期：2026-03-12

## 追溯记录

| 需求ID | 任务ID | 实现文件 | 函数/类 | 变更类型 | 说明 |
|--------|--------|----------|---------|----------|------|
| REQ-1.1 | TASK-2 | models/xc_borrow_apply.py | XcBorrowApply.create_borrow_apply | 新增 | 创建借用申请单 |
| REQ-3.2 | TASK-5 | models/xc_borrow_apply.py | XcBorrowApply._check_borrow_limit | 新增 | 借用周期校验 |
| REQ-1.1 | TASK-2 | controllers/xc_borrow_controller.py | XcBorrowController.create_borrow | 新增 | 创建借用申请接口 |
```

### 变更类型说明

| 类型 | 含义 |
|------|------|
| 新增 | 全新的函数/类 |
| 修改 | 对已有代码的功能变更 |
| 重构 | 不改变功能的代码结构调整 |
| 修复 | Bug 修复 |

---

## 标注使用的完整标签列表

| 标签 | 用途 | 必须 | 示例 |
|------|------|------|------|
| `@requirement` | 关联需求编号 | ✅ 业务函数必须 | `@requirement zk-xxx-REQ-1.1` |
| `@task` | 关联任务编号 | ✅ 业务函数必须 | `@task zk-xxx-TASK-2` |
| `@businessRule` | 标注业务规则实现 | 仅涉及业务规则时 | `@businessRule 借用周期不超过180天` |
| `@deprecated` | 标注废弃代码 | 仅废弃时 | `@deprecated zk-xxx-REQ-2.1 replaced by REQ-3.1` |

---

## AI 开发时的强制要求

1. **实现任何业务功能前**，先从 `requirements.md` 和 `tasks.md` 中确认对应的需求ID和任务ID
2. **生成代码时**，必须在函数 docstring 中添加 `@requirement` 和 `@task` 标注
3. **实现业务规则时**，必须添加 `@businessRule` 标注，并在关键逻辑处添加行内注释
4. **修改已有函数时**，在 docstring 中追加新的 `@requirement` 和 `@task`，不得删除历史标注
5. **完成开发后**，更新对应 spec 目录下的 `traceability-matrix.md`
6. **标识格式必须严格遵守** `{branch_name}-REQ-{编号}` / `{branch_name}-TASK-{编号}` 的命名规则

---

## 代码审查检查清单

- [ ] 新增的业务函数是否有 `@requirement` 和 `@task` 标注？
- [ ] 业务规则实现是否有 `@businessRule` 标注和行内注释？
- [ ] 多版本迭代的函数是否保留了历史标注记录？
- [ ] 需求标识格式是否符合 `{branch_name}-REQ/TASK-{编号}` 规范？
- [ ] `traceability-matrix.md` 是否已同步更新？
