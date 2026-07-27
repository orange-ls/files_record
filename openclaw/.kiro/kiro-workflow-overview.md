# Kiro 开发规范体系 — 全景流程图

> 本文档将项目中所有 steering、hooks、skills、spec 规范整理为可视化流程图。

---

## 1. 整体架构总览

```mermaid
graph TB
    subgraph 规范层["📋 Steering 规范层（始终/条件加载）"]
        S1["product.md<br/>产品概述"]
        S2["structure.md<br/>项目架构"]
        S3["tech.md<br/>技术栈"]
        S4["spec-rules.md<br/>Spec 模式规范"]
        S5["development_rules.md<br/>开发规则 ⚡条件加载"]
        S6["vibe-rules.md<br/>Vibe 模式规范 ⚡条件加载"]
        S7["develop_code_traceability<br/>需求追溯规范 ⚡技能"]
    end

    subgraph Hook层["🪝 Hook 自动化层（事件驱动）"]
        H1["skills-index-lookup 技能索引查询<br/>📥 promptSubmit 用户提问时"]
        H0["protected-path-guard 禁区路径写入拦截<br/>🛡️ preToolUse write操作前"]
        H3["code-traceability-check 追溯标注提醒<br/>⏳ preTaskExecution 任务开始前"]
        H4["readme-sync-check 文档同步检查<br/>✅ postTaskExecution 任务完成后"]
        H5["claudeception-auto-extract 知识技能收集<br/>🛑 agentStop Agent停止时"]
        H6["sync-xc-addons-docs 全量文档同步<br/>👆 userTriggered 手动触发"]
    end

    subgraph 知识层["🧠 Skills 技能知识层"]
        SK1["INDEX.md 技能索引表"]
        SK2["claudeception 知识提取引擎 ✅已注册"]
        SK3["{module}-knowledge 模块知识库技能"]
    end

    subgraph 文档层["🧠 模块知识库技能层"]
        MD1[".kiro/skills/{module}/{module}-knowledge/SKILL.md"]
        MD2["各模块知识库技能文档"]
    end

    subgraph Spec层["📐 Spec 需求设计层"]
        SP1["requirements.md 需求文档"]
        SP2["design.md 设计文档"]
        SP3["tasks.md 任务清单"]
        SP4["traceability-matrix.md 追溯矩阵"]
    end

    规范层 -->|指导| Hook层
    Hook层 -->|触发查询| 知识层
    知识层 -->|触发读取| 文档层
    Hook层 -->|触发更新| Spec层
    知识层 -->|辅助| Hook层
```


---

## 2. 用户提问 → 任务完成 全流程

```mermaid
flowchart TD
    START(["👤 用户输入消息"]) --> PS{"promptSubmit 用户提问<br/>事件触发"}

    PS --> H1["🪝 skills-index-lookup 技能索引查询<br/>读取 INDEX.md 技能索引表<br/>按分类匹配技能"]

    H1 --> H1A{"命中技能?"}
    H1A -->|"是（已注册 ✅）"| H1B["discloseContext 加载技能<br/>注入上下文"]
    H1A -->|"是（未注册 ❌）"| H1D["readFile 读取 SKILL.md<br/>注入上下文"]
    H1A -->|否| H1C["跳过"]

    H1D --> BIZ_CHECK{"命中模块知识库技能?"}
    BIZ_CHECK -->|是| H2B["加载对应模块的<br/>{module}-knowledge SKILL.md"]
    BIZ_CHECK -->|否| KIRO

    H1B --> KIRO
    H1C --> KIRO
    H2B --> KIRO

    KIRO["🤖 Kiro 处理任务<br/>（Steering 规范引导始终生效）"]

    KIRO --> MODE{"开发模式判断"}

    MODE -->|Spec 模式| SPEC_FLOW
    MODE -->|Vibe 模式| VIBE_FLOW
    MODE -->|非代码任务| DIRECT["直接回答"]

    DIRECT --> STOP_EVENT

    subgraph SPEC_FLOW["📐 Spec 模式流程"]
        direction TB
        SF1["确认 Git 分支"] --> SF2["获取分支名"]
        SF2 --> SF3["向用户确认分支"]
        SF3 --> SF4["创建/定位<br/>.kiro/specs/{branch}/"]
        SF4 --> SF5["编写 requirements.md 需求文档"]
        SF5 --> SF6["编写 design.md 设计文档"]
        SF6 --> SF7["编写 tasks.md 任务清单"]
        SF7 --> SF8["逐个执行 Task"]
    end

    subgraph VIBE_FLOW["🎸 Vibe 模式流程"]
        direction TB
        VF1["确认 Git 分支"] --> VF2["获取分支名"]
        VF2 --> VF3["向用户确认分支"]
        VF3 --> VF4{"spec 目录<br/>已存在?"}
        VF4 -->|是| VF5["读取现有 spec<br/>理解上下文"]
        VF4 -->|否| VF6["标记: 需新建 spec"]
        VF5 --> VF7["执行代码变更"]
        VF6 --> VF7
        VF7 --> VF8["更新/创建 spec 文件"]
    end

    SF8 --> TASK_HOOKS
    VF7 --> TASK_HOOKS

    subgraph TASK_HOOKS["🪝 Task 执行期间的 Hook 钩子"]
        direction TB
        TH1["⏳ preTaskExecution 任务开始前<br/>code-traceability-check 追溯标注提醒<br/>提醒添加 @requirement/@task 标注"]
        TH1 --> TH0["🛡️ preToolUse write操作前<br/>protected-path-guard 禁区路径写入拦截<br/>拦截对 addons/ odoo/ 的写入"]
        TH0 --> TH2["📝 执行编码<br/>遵循 development_rules.md 开发规则<br/>遵循 develop_code_traceability 技能追溯规范"]
        TH2 --> TH3["✅ postTaskExecution 任务完成后<br/>readme-sync-check 文档同步检查<br/>检查是否需更新模块知识库技能"]
    end

    TASK_HOOKS --> STOP_EVENT

    STOP_EVENT(["🛑 agentStop Agent停止 事件"])
    STOP_EVENT --> H5

    subgraph KNOWLEDGE["🧠 知识收集判断"]
        direction TB
        H5["🪝 claudeception-auto-extract 知识技能收集"]
        H5 --> K1{"前置过滤:<br/>涉及实际代码?"}
        K1 -->|否| K_END["静默结束"]
        K1 -->|是| K2{"技能命中分析"}
        K2 -->|"A: 命中且一次解决"| K_END
        K2 -->|"B: 命中但多轮才解决"| K3["询问用户:<br/>是否补充现有技能?"]
        K2 -->|"C: 未命中且有复用价值"| K4["询问用户:<br/>是否创建新技能?"]
        K3 --> K5{"用户确认?"}
        K4 --> K5
        K5 -->|是| K6["激活 claudeception 知识提取引擎<br/>提取知识 → SKILL.md 技能文档<br/>更新 INDEX.md 技能索引表"]
        K5 -->|否| K_END
    end

    K6 --> FINAL(["✅ 流程结束"])
    K_END --> FINAL
```


---

## 3. Steering 规范加载机制

```mermaid
flowchart LR
    subgraph ALWAYS["🔵 始终加载（每次对话自动注入）"]
        A1["product.md 产品概述<br/>业务域 & 外部集成"]
        A2["structure.md 项目架构<br/>模块分层 & 依赖关系"]
        A3["tech.md 技术栈<br/>构建命令 & CLI参数"]
        A4["spec-rules.md Spec模式规范<br/>目录命名 & 分支管理"]
    end

    subgraph CONDITIONAL["🟡 条件加载（读取 xc_addons/**/*.py 时触发）"]
        C1["development_rules.md 开发规则<br/>安全红线 / 代码规范 /<br/>项目约定 / 知识库维护"]
        C2["vibe-rules.md Vibe模式规范<br/>分支确认 / Spec更新 /<br/>轻量版迭代流程"]
        C3["develop_code_traceability 技能 需求追溯规范<br/>@requirement @task 标注 /<br/>追溯矩阵维护"]
    end

    USER["👤 用户消息"] --> ALWAYS
    USER -->|"涉及 xc_addons/*.py"| CONDITIONAL
```


---

## 4. 编码阶段规范执行流程

```mermaid
flowchart TD
    CODE_START(["开始编码"]) --> CHECK_BRANCH{"确认 Git 分支<br/>非 main/master/develop?"}
    CHECK_BRANCH -->|否| BLOCK["❌ 禁止开发<br/>提醒切换功能分支"]
    CHECK_BRANCH -->|是| LOAD_RULES["加载编码规范"]

    LOAD_RULES --> R1["🔒 安全红线"]
    LOAD_RULES --> R2["📝 代码规范"]
    LOAD_RULES --> R3["🏷️ 需求追溯标注"]
    LOAD_RULES --> R4["📦 项目约定"]

    subgraph 安全红线["🔒 安全红线（不可违反）"]
        R1A["API 默认 auth='user'<br/>禁止 auth='public'"]
        R1B["默认逻辑删除<br/>active=True 字段"]
        R1C["禁止明文密码/密钥/IP"]
        R1D["禁止修改 addons/ odoo/ 目录"]
    end

    subgraph 代码规范["📝 代码规范"]
        R2A["中文注释"]
        R2B["异常处理 + 日志记录"]
        R2C["性能优化 + 缓存"]
        R2D["合理封装 + 设计模式"]
    end

    subgraph 需求追溯["🏷️ 需求追溯标注"]
        R3A["函数 docstring:<br/>@requirement {branch}-REQ-{n}<br/>@task {branch}-TASK-{n}"]
        R3B["关键逻辑行内:<br/>@businessRule 描述"]
        R3C["多版本迭代:<br/>追加标注，保留历史"]
    end

    subgraph 项目约定["📦 项目约定"]
        R4A["模型名: xc. 前缀"]
        R4B["API 返回: AjaxResult 封装"]
        R4C["外部调用: try-except + logging"]
        R4D["通用工具 → xc_common/"]
        R4E["关键字段加索引"]
    end

    R1 --> R1A & R1B & R1C & R1D
    R2 --> R2A & R2B & R2C & R2D
    R3 --> R3A & R3B & R3C
    R4 --> R4A & R4B & R4C & R4D & R4E

    R1A & R1B & R1C & R1D --> WRITE_CODE
    R2A & R2B & R2C & R2D --> WRITE_CODE
    R3A & R3B & R3C --> WRITE_CODE
    R4A & R4B & R4C & R4D & R4E --> WRITE_CODE

    WRITE_CODE(["✅ 编写代码"])
```


---

## 5. Spec 模式 vs Vibe 模式对比流程

```mermaid
flowchart TD
    NEED(["需求变更来了"]) --> JUDGE{"变更规模判断"}

    JUDGE -->|"新模块 / 跨3+模块 /<br/>大幅模型变更 / 架构重构"| SPEC["📐 使用 Spec 模式"]
    JUDGE -->|"小功能增补 / 需求修正 /<br/>功能优化"| VIBE["🎸 使用 Vibe 模式"]

    subgraph SPEC_DETAIL["📐 Spec 模式详细流程"]
        direction TB
        S1["① 确认分支 ≠ main/master/develop"]
        S1 --> S2["② git rev-parse --abbrev-ref HEAD"]
        S2 --> S3["③ 向用户确认分支"]
        S3 --> S4["④ 分支名安全处理: / → -"]
        S4 --> S5["⑤ 创建 .kiro/specs/{branch}/"]
        S5 --> S6["⑥ 编写 requirements.md 需求文档"]
        S6 --> S7["⑦ 编写 design.md 设计文档"]
        S7 --> S8["⑧ 编写 tasks.md 任务清单"]
        S8 --> S9["⑨ 逐个执行 Task"]
        S9 --> S10["⑩ 维护 traceability-matrix.md 追溯矩阵"]
    end

    subgraph VIBE_DETAIL["🎸 Vibe 模式详细流程"]
        direction TB
        V1["① 确认分支 ≠ main/master/develop"]
        V1 --> V2["② git rev-parse --abbrev-ref HEAD"]
        V2 --> V3["③ 向用户确认分支"]
        V3 --> V4{"④ .kiro/specs/{branch}/ 存在?"}
        V4 -->|是 情况一| V5A["读取现有 spec 上下文"]
        V4 -->|否 情况二| V5B["标记需新建轻量版 spec"]
        V5A --> V6["⑤ 执行代码变更<br/>遵循编码规范 + 追溯标注"]
        V5B --> V6
        V6 --> V7A{"情况一: 追加更新"}
        V6 --> V7B{"情况二: 创建轻量版"}

        V7A --> V8A["更新 requirements.md 需求文档<br/>添加 [VIBE-日期] 标记"]
        V8A --> V9A["更新 tasks.md 任务清单<br/>追加 Vibe 迭代任务章节"]
        V9A --> V10A["更新 traceability-matrix.md 追溯矩阵"]
        V10A --> V11A["按需更新 design.md 设计文档"]

        V7B --> V8B["创建轻量版 requirements.md 需求文档<br/>标注基线分支"]
        V8B --> V9B["创建轻量版 tasks.md 任务清单"]
        V9B --> V10B["创建轻量版 traceability-matrix.md 追溯矩阵"]
        V10B --> V11B["按需创建 design.md 设计文档"]
    end

    SPEC --> SPEC_DETAIL
    VIBE --> VIBE_DETAIL
```


---

## 6. Hook 事件驱动全景

```mermaid
flowchart LR
    subgraph 事件源["⚡ 事件源"]
        E1(["promptSubmit 用户提问<br/>用户发送消息"])
        E0(["preToolUse write操作前<br/>写入工具即将执行"])
        E2(["preTaskExecution 任务开始前<br/>Task 即将执行"])
        E3(["postTaskExecution 任务完成后<br/>Task 执行完毕"])
        E4(["agentStop Agent停止<br/>Agent 执行结束"])
        E5(["userTriggered 手动触发<br/>用户主动点击"])
    end

    subgraph Hook处理["🪝 Hook 处理"]
        E1 --> H1["skills-index-lookup<br/>技能索引查询"]
        E0 --> H0["protected-path-guard<br/>禁区路径写入拦截"]
        E2 --> H3["code-traceability-check<br/>追溯标注提醒"]
        E3 --> H4["readme-sync-check<br/>文档同步检查"]
        E4 --> H5["claudeception-auto-extract<br/>知识技能收集"]
        E5 --> H6["sync-xc-addons-docs<br/>全量文档同步"]
    end

    subgraph 执行动作["📋 执行动作"]
        H1 -->|askAgent| A1["读 INDEX.md 技能索引<br/>→ 按分类匹配技能<br/>→ 已注册: discloseContext 加载<br/>→ 未注册: readFile 读取 SKILL.md<br/>→ 模块知识库技能按需加载"]
        H0 -->|askAgent| A0["检查目标路径 → addons/ 或 odoo/ 则拒绝写入 → 其他路径放行"]
        H3 -->|askAgent| A3["提醒: @requirement @task @businessRule 标注"]
        H4 -->|askAgent| A4["检查模型/功能/集成变更 → 更新模块知识库技能 SKILL.md"]
        H5 -->|askAgent| A5["过滤 → 分析 → 询问 → 提取技能到 SKILL.md"]
        H6 -->|askAgent| A6["git diff → 分析变更类型 → 按需更新5类文档"]
    end
```


---

## 7. 模块知识库技能体系

```mermaid
flowchart TD
    subgraph 技能层["🧠 模块知识库技能层"]
        direction LR
        M1["xc_common<br/>xc-common-knowledge"]
        M2["xc_dboms<br/>xc-dboms-knowledge"]
        M3["xc_flowable<br/>xc-flowable-knowledge"]
        M4["xc_production<br/>xc-production-knowledge"]
        M5["xc_borrow<br/>xc-borrow-knowledge"]
        M6["xc_base_config<br/>xc-base-config-knowledge"]
        M7["xc_user<br/>xc-user-knowledge"]
        M8["xc_web_login<br/>xc-web-login-knowledge"]
        M9["xc_dashboard<br/>xc-dashboard-knowledge"]
        M10["xc_audit<br/>xc-audit-knowledge"]
        M11["xc_itsm<br/>xc-itsm-knowledge"]
        M12["xc_app<br/>xc-app-knowledge"]
        M13["xc_process_visual<br/>xc-process-visual-knowledge"]
        M14["cron_failure_notification<br/>cron-failure-notification-knowledge"]
        M15["redis_session_store<br/>redis-session-store-knowledge"]
    end

    subgraph 目录结构["📂 技能目录结构"]
        direction TB
        D1[".kiro/skills/{module}/"]
        D2["{module}-knowledge/SKILL.md"]
        D3["{module}-integration/SKILL.md（可选）"]
        D4["{module}-other-skill/SKILL.md（可选）"]
        D1 --> D2 & D3 & D4
    end

    subgraph 章节结构["📄 SKILL.md 标准章节"]
        direction TB
        CH1["# 模块中文名（module_name）"]
        CH2["> 一句话描述"]
        CH3["## 模块概述"]
        CH4["## 核心业务流程"]
        CH5["## 数据模型（表格）"]
        CH6["## 主要功能模块"]
        CH7["## 外部集成（表格，无则标注'无'）"]
        CH8["## 系统术语（表格）"]
    end

    M2 --> 章节结构

    subgraph 维护触发["🔄 维护触发条件"]
        T1["新增/删除数据模型"]
        T2["新增/删除功能模块"]
        T3["新增/变更外部集成"]
        T4["新增业务术语"]
    end

    维护触发 -->|"postTaskExecution 任务完成后<br/>readme-sync-check 文档同步检查"| 技能层
```


---

## 8. 手动文档同步流程（sync-xc-addons-docs 全量文档同步）

```mermaid
flowchart TD
    TRIGGER(["👆 userTriggered 用户手动触发"]) --> STEP1["① git diff 收集变更文件"]
    STEP1 --> STEP2{"xc_addons 下<br/>有变更?"}
    STEP2 -->|否| END1["告知用户，结束"]
    STEP2 -->|是| STEP3["② 分析变更类型"]

    STEP3 --> TYPE_A{"A: 新增模块<br/>新 __manifest__.py?"}
    STEP3 --> TYPE_B{"B: 模型变更<br/>_name 定义变化?"}
    STEP3 --> TYPE_C{"C: 功能变更?"}
    STEP3 --> TYPE_D{"D: 外部集成变更?"}
    STEP3 --> TYPE_E{"E: xc_common<br/>新工具类?"}
    STEP3 --> TYPE_F{"F: 依赖关系变化<br/>depends 变化?"}

    TYPE_A -->|是| UPD1["更新模块知识库技能 SKILL.md"]
    TYPE_A -->|是| UPD3["更新 structure.md 项目架构"]
    TYPE_A -->|是| UPD4["更新 product.md 产品概述"]

    TYPE_B -->|是| UPD1
    TYPE_C -->|是| UPD1
    TYPE_D -->|是| UPD1
    TYPE_D -->|是| UPD4

    TYPE_E -->|是| UPD5["更新 xc-common-knowledge SKILL.md"]

    TYPE_F -->|是| UPD3

    UPD1 & UPD3 & UPD4 & UPD5 --> SUMMARY["④ 输出变更摘要"]
```


---

## 9. 知识技能生命周期

```mermaid
flowchart TD
    subgraph 查询阶段["🔍 查询阶段（每次提问）"]
        Q1(["用户提问"]) --> Q2["skills-index-lookup Hook"]
        Q2 --> Q3["读取 INDEX.md 技能索引表"]
        Q3 --> Q4{"按分类触发关键词<br/>匹配?"}
        Q4 -->|"是（已注册 ✅）"| Q5["discloseContext 加载技能"]
        Q4 -->|"是（未注册 ❌）"| Q6["readFile 读取 SKILL.md 技能文档"]
        Q4 -->|否| Q7["跳过"]
        Q6 --> Q8{"命中模块知识库技能?"}
        Q8 -->|是| Q9["加载对应模块的<br/>{module}-knowledge SKILL.md"]
        Q8 -->|否| Q10["仅使用 SKILL.md 上下文"]
    end

    subgraph 收集阶段["📥 收集阶段（任务结束）"]
        C1(["agentStop Agent停止"]) --> C2["claudeception-auto-extract 知识技能收集 Hook"]
        C2 --> C3{"前置过滤"}
        C3 -->|非代码任务| C4["静默结束"]
        C3 -->|代码任务| C5{"技能命中分析"}
        C5 -->|A 命中+一次解决| C4
        C5 -->|B 命中+多轮解决| C6["询问: 补充现有技能?"]
        C5 -->|C 未命中+有复用价值| C7["询问: 创建新技能?"]
        C6 --> C8{"用户确认"}
        C7 --> C8
        C8 -->|是| C9["激活 claudeception 知识提取引擎"]
        C8 -->|否| C4
    end

    subgraph 创建阶段["✨ 创建阶段"]
        C9 --> W1["提取知识"]
        W1 --> W2["创建 .kiro/skills/{name}/SKILL.md 技能文档"]
        W2 --> W3["更新 INDEX.md 技能索引表<br/>追加 | name | description |"]
    end

    创建阶段 -->|下次提问时| 查询阶段
```


---

## 10. 项目模块四层架构

```mermaid
graph BT
    subgraph L1["🏗️ 第一层：基础设施层"]
        M1["xc_common<br/>公共工具库"]
        M2["redis_session_store<br/>Redis Session"]
        M3["cron_failure_notification<br/>定时任务通知"]
    end

    subgraph L2["⚙️ 第二层：平台服务层"]
        M4["xc_base_config<br/>基础主数据"]
        M5["xc_flowable<br/>工作流引擎"]
        M6["xc_user<br/>用户组织"]
        M7["xc_web_login<br/>认证SSO"]
    end

    subgraph L3["💼 第三层：核心业务层"]
        M8["xc_dboms<br/>IBOMS 核心"]
        M9["xc_production<br/>生产协同"]
        M10["xc_borrow<br/>样机借用"]
    end

    subgraph L4["🧩 第四层：辅助业务层"]
        M11["xc_itsm<br/>IT服务"]
        M12["xc_audit<br/>审单引擎"]
        M13["xc_dashboard<br/>驾驶舱"]
        M14["xc_app<br/>移动端API"]
        M15["xc_process_visual<br/>流程可视化"]
    end

    M1 -.->|import| M4 & M5 & M6 & M7
    M4 --> M8
    M5 --> M8
    M5 --> M15
    M8 --> M9
    M8 --> M10

    subgraph EXT["🌐 外部系统"]
        E1["SAP"]
        E2["CRM"]
        E3["WMS"]
        E4["MES"]
        E5["OA"]
        E6["Kafka"]
        E7["Redis"]
    end

    M8 -.-> E1 & E2 & E3 & E5
    M9 -.-> E4 & E3 & E1
    M10 -.-> E3 & E1 & E5
```

---

## 附录：文件清单

| 类别 | 文件 | 加载方式 | 用途 |
|------|------|----------|------|
| Steering | product.md | 始终加载 | 产品概述、业务域、外部集成 |
| Steering | structure.md | 始终加载 | 项目架构、模块分层、依赖关系 |
| Steering | tech.md | 始终加载 | 技术栈、构建命令、CLI 参数 |
| Steering | spec-rules.md | 始终加载 | Spec 目录命名规范（分支名） |
| Steering | development_rules.md | 条件加载 (xc_addons/**/*.py) | 安全红线、代码规范、项目约定 |
| Steering | vibe-rules.md | 条件加载 (xc_addons/**/*.py) | Vibe 模式工作流规范 |
| Skill | develop_code_traceability | 按需激活 | 需求追溯代码标注规范 |
| Hook | skills-index-lookup | promptSubmit | 技能索引查询（统一入口，间接触发模块文档加载） |
| Hook | protected-path-guard | preToolUse (write) | 禁区路径写入拦截（addons/ odoo/） |
| Hook | code-traceability-check | preTaskExecution | 需求追溯标注提醒 |
| Hook | readme-sync-check | postTaskExecution | 模块知识库技能同步检查 |
| Hook | claudeception-auto-extract | agentStop | 知识技能收集 |
| Hook | sync-xc-addons-docs | userTriggered | 全量文档同步 |
| Skill | claudeception | ✅ 已注册（discloseContext 加载） | 知识提取引擎 |
| Skill | {module}-knowledge | 按需激活 | 模块知识库技能（.kiro/skills/{module}/{module}-knowledge/SKILL.md） |
| 索引 | .kiro/skills/INDEX.md | promptSubmit 时读取 | 技能索引表（含分类和触发关键词） |
| Spec | .kiro/specs/{branch}/ | Spec/Vibe 模式创建 | requirements / design / tasks / traceability-matrix |
