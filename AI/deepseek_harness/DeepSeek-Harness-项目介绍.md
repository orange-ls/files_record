# DeepSeek Harness 项目介绍

- 上游仓库：https://github.com/deepseek-ai/deepseek-harness
- 当前版本：0.1.0-rc.5（开发者预览）
- 许可证：MIT（第三方依赖见 `THIRD_PARTY_NOTICES.md`）
- 文档编写日期：2026-08-14

---

## 1. 项目概述

DeepSeek Harness（命令名 `dsh`）是由 DeepSeek AI 开发的**开源 agent harness（智能体运行框架）**。它不是一个单一的"聊天机器人应用"，而是一套用来**组装、运行和扩展编码智能体（coding agent）的完整运行时**：模型适配、工具注册与执行、会话持久化、权限与沙箱、审批交互、Web 界面等，全部以插件形式装配在一起。

项目有两个最鲜明的设计特征：

1. **一切皆插件**。产品每一部分——模型适配器、工具注册表、会话日志，乃至 agent loop（智能体循环）本身——都是插件，都可以从配置替换。不存在需要打补丁的特权内核。
2. **由 Cordis 驱动**。底层框架 Cordis（vendored 自 cordiverse）让插件向共享上下文贡献服务、类型化事件和可逆的副作用，设计参见论文《A Programming Paradigm for Spatiotemporal Composability》。

项目当前处于**开发者预览**阶段，正在快速迭代，官方明确声明未来将出现破坏兼容性的变更。

## 2. 解决什么问题

构建一个可靠的编码 agent，远不止"接一个大模型 API"那么简单。围绕模型需要一整套基础设施：安全的命令执行、受控的文件读写、可恢复的会话状态、人机审批、多提供方切换、子 agent 委派、后台任务、上下文压缩等等。DeepSeek Harness 把这些能力做成**可插拔、可组合、可替换**的标准化部件：

- 想换模型提供方？替换一个适配器插件。
- 想把 Bash、文件系统、终端整体搬到远程沙箱？替换对应的 Service Provider，上层工具无需改动。
- 想给 agent 加一个全新的面向模型能力？注册一个工具插件，它的 schema 自动进入系统提示词组装。

扩展 dsh 的方式不是 fork 内核，而是**把插件挂载到其他插件旁边**；每一项注册都是副作用，插件卸载时自动撤销。

## 3. 产品形态与入口

DeepSeek Harness 提供多种运行形态，覆盖从个人使用到自动化集成的场景：

| 形态 | 说明 |
|---|---|
| **Web UI**（`dsh web`） | 浏览器界面，默认 `http://127.0.0.1:3080`。配置模型、选择工作区、运行任务、审批操作，开箱即用 |
| **Headless CLI**（`dsh --profile headless "任务"`） | 一次性任务：运行完成后打印最终答案并退出，适合脚本与 CI 集成，不开监听端口 |
| **ACP 服务器** | Agent Client Protocol，通过 JSON-RPC stdio 向程序化客户端提供会话、权限与取消操作 |
| **JSON-RPC SDK** | `packages/sdk` 提供协议、服务器与 TypeScript 客户端，从另一进程驱动运行时 |
| **Python SDK** | PyPI 包 `deepseek-harness-sdk`，自带内置运行时（无需系统 Node.js），供 Python 程序内嵌调用 |

安装最简方式：`npx @deepseek-ai/dsh web`（需要 Node.js `^22.19 || >=24`）。

## 4. 核心特性

### 4.1 多模型提供方支持

- 原生 DeepSeek 适配器随基础组合包挂载。
- 已安装目录提供方：Anthropic、OpenAI 等，提供端点、协议和模型列表。
- 自定义提供方：任何 OpenAI 兼容的公司网关或自建服务器，可手动录入模型、协议与凭据，支持"获取可用模型"发现。
- 原生认证提供方：Bedrock（AWS 凭据）、Vertex（ADC）、Azure（api-version）、Codex（OAuth）。
- 模型变更即时生效，无需重启；图片输入能力按模型显式声明（`input: [text, image]`）。

### 4.2 丰富的面向模型工具

工具由插件注册到 `ctx.tools`，schema 自动参与系统提示词组装。随产品发布的工具包括（摘自自动生成的工具目录 `docs/tool-catalog.zh.md`）：

- **执行**：`bash`（一次性与持久 PTY 两种）、`pwsh`（Windows PowerShell 方言）、`terminal_*`（持久终端管理）、`run_code`（Code Mode）
- **文件**：`read`、`write`、`edit`、`read_image`、`str_replace_editor`、`glob`、`grep`（内置随包 ripgrep，无需宿主机安装 rg）
- **协作与流程**：`ask_user_question`、`todo_write`、`exit_plan_mode`（Plan 模式）、`create_goal`/`get_goal`/`update_goal`、`schedule_*`（会话内定时）、`workflow`、`ralph`
- **委派与后台**：`subagent`、`subagent_fork`、`send_message`、`interrupt_agent`、`list_agents`、`job_list`/`job_output`/`job_kill`
- **知识与集成**：`web_search`、`web_fetch`、`lsp`、`skill`（技能目录与加载）、`session_search`/`session_trace` 等会话查询工具
- **自指**：`cordis_define`、`cordis_run`、`cordis_inspect_*` 等（需显式选择启用），agent 可检查并挂载/卸载运行时的插件——即"agent 修改自己的运行时"

### 4.3 会话日志：模型可见即已记录

会话日志（append-only 的 `SessionEvent` 流）是模型所见上下文的唯一来源：`deriveMessages()` 从日志投影出模型历史，fork、恢复、transcript、遥测和持久化都派生自该事件流。运行时强制一条不变量——**抵达模型请求的一切都必须能从日志重建**。这保证了会话的可审计性与可回放性。持久化后端提供 JSONL 与 SQLite 两种，投影缓存、标题生成、会话遥测围绕同一数据平面构建。

### 4.4 能力 Seam：可替换性的架构基石

一个 **capability seam（能力缝隙）** 是一项可替换能力，包含三种角色：声明接口的 Service Definition、实现它的 Service Provider、使用它的 Consumer（通常是面向模型的工具）。文件系统、子进程、shell、终端、LSP、Web、压缩、subagent、沙箱等都是 seam。

这带来极强的替换能力：文件系统与进程提供方共享同一个执行世界，把它们指向远程沙箱（如 E2B），就把 Bash、PTY 和 LSP 一并搬了过去，无需任何提供方专用 fork；subagent 提供方在同一接口之后可以从"新建子 agent"变为"把一个轮次委派给另一个产品"。

### 4.5 权限、审批与沙箱

- 新会话默认 `workspace-write` 权限预设：Bash 与文件修改限制在会话 workspace 与平台临时根目录内；读取、网络与进程可见性不受限制。可通过 `DSH_PERMISSION_MODE` 调整。
- 需要审批的操作会先向用户询问。
- 进程沙箱后端：Linux bwrap / Landlock（仓库附带原生模块 `node-addon-landlock-run`）、macOS Seatbelt。
- 会话遥测默认留在本地，显式开启 OTLP 导出前官方明确提醒了无脱敏规则的风险。

### 4.6 组合机制：Profile 与组合包

运行中的 `dsh` 是一棵插件树，由配置层按序叠加而成：

- **Profile** 是存放在 Harness home（`$DSH_HOME`，默认 `~/.dsh`）中的具名组装，列出自己叠放的组合包、树外插件和用户自己的 `cordis.patch.yml`。`web` 与 `headless` 作为模板随发行版交付。
- **组合包（bundle）** 是 Cordis 配置项及其挂载代码的分发格式，其插入的内容始终可被上层 patch。内置组合包：`dsh-base`（模型适配、工具、持久化、沙箱与审批、设置、凭据、遥测）、`dsh-web-app`（浏览器应用）、`dsh-headless`（一次性运行器，不带服务器）。
- 叠加顺序：各组合包 → profile 的 `cordis.patch.yml` → home 级 `cordis.patch.yml` → `--patch` overlay，后者优先；patch 按 id 替换整个条目 config 或插入新条目。
- `dsh plugin --profile <name> add <包/git 地址>` 安装第三方插件组合包；社区插件通过 `dsh-plugin` GitHub topic 发现。
- 配置层支持热更新：运行期间编辑 `cordis.patch.yml` 会被监视并事务性重新应用。

### 4.7 Agent 循环与事件体系

一个**步骤**是一次模型请求加上它调用的工具；一个**轮次**包含零个或多个步骤，在领取首条输入前打开、不再欠下工作时关闭。事件体系分三个域：

- **会话事件**：追加到日志并广播的持久事实，重载后依然存在；
- **Agent 事件**（`agent/*`）：携带活跃 Agent 的实时状态——inbox、步骤、请求、验证、续跑；
- **能力事件**：无需导入循环即可向 seam（`fs/*`、`tools/*`、`telemetry/*`）附加策略和适配器。

`agent/pre-step`、`agent/request`、`llm/stream`、`tools/*` 等 waterfall 事件允许监听器改写或拒绝后再委托，构成了拦截与策略注入的扩展点。

## 5. 仓库结构

```
vendor/      Vendored Cordis 源码（固定版本副本，manifest 记录上游 SHA）
packages/    @deepseek-ai/dsh-<pkg> 工作区包，按组划分（约 50 个组）
  core/        产品 API 主干：session、system-prompt、tools、agent、agent-loop
  llm/         LLM 能力：Service Definition/Consumer + DeepSeek 提供方
  shell/ subprocess/ terminal/ fs/ lsp/ web/ compaction/ subagent/ sandbox/
               各能力 seam（Service Definition + 提供方 + 工具 Consumer）
  session/     持久会话数据平面：JSONL/SQLite 持久化、投影、标题、遥测
  sdk/         进程外 SDK：JSON-RPC 协议、服务器与 TypeScript 客户端
  acp/         仅面向自动化的 Agent Client Protocol 服务器
  host/ client/ Web GUI 的宿主半侧（API 网关 + HTTP 服务器）与浏览器半侧
  bundle/      可安装的 dsh --profile patch 层组合包
  extensions/  agent 运行时自修改：实时插件检查与挂载/卸载
  interaction/ 审批/交互能力、权限预设、命令、询问用户
  ……           另有 todo、plan、preset、guard、hooks、settings、credentials、
               workflow、jobs、schedule、goal、skill、typert 等
apps/        cli（dsh 命令入口）、web（前端应用）
python/      Python SDK 与内置运行时
native/      node-addon-landlock-run 原生模块源
examples/    可运行的 cordis.yml 叶子示例（headless-agent、acp-agent、
             jsonrpc-agent、web-cordis、web-schedule、mcp-memory）
docs/        架构、子系统参考、cookbook、事后分析、生成目录（双语）
website/     VitePress 文档站点（本地投影）
scripts/     仓库门禁与生成器
.agents/     Agent 工作流与 Agent Notes 决策记录
```

包按组置于 `packages/<group>/<pkg>/`，包名统一为 `@deepseek-ai/dsh-<pkg>`。绝大多数组为"产品：稳定 API"发布预期，`e2b/` 标注为 POC，`examples/` 与 `test-support/` 为支持基础设施。

## 6. 技术栈与工程实践

| 维度 | 选型与实践 |
|---|---|
| 语言 | TypeScript（ESM，`strict: true` + `noImplicitAny`，NodeNext 消费方检查） |
| 运行时 | Node.js `^22.19 || >=24` |
| 包管理 | pnpm workspaces + Corepack（固定 pnpm 11.7.0） |
| 构建 | tsc（lib/types 发射）+ tsdown（运行时打包），Host/Client 双编译面 |
| 测试 | vitest：单元、真实 API e2e、无键快照回放（keyless snapshot）、Web GUI 测试 |
| 质量门禁 | oxlint、knip、publint、jscpd 重复检测、覆盖率门禁（packages 逐文件 100%）、数十个 verify-*/gen-* 文档与产物一致性门禁 |
| 文档 | 双语（英文源 + 中文评审对侧），VitePress 站点，生成目录（工具 schema、配置、模块图、持久化目录）带新鲜度门禁 |
| 决策记录 | `.agents/notes/` Agent Notes 记录非平凡变更的 why 与放弃项 |

仓库对文档与代码的一致性要求非常严格：工具目录、配置目录等由生成器产出并由 CI 校验新鲜度；类型定义粘贴块（`ts type-equiv`）与源码逐符号对齐；文档有字数预算门禁。

## 7. 平台支持

| 平台 | 支持情况 |
|---|---|
| Linux | 完整支持；沙箱后端 bwrap / Landlock |
| macOS | 完整支持；沙箱后端 Seatbelt |
| Windows | 支持（仓库有专门 Windows CI 门禁与 wine 验证）；shell 使用 PowerShell 方言 `pwsh` 工具 |
| Python SDK | Linux x64/arm64、macOS 14+ arm64；不支持 Windows（持久 PTY 需要 POSIX） |

## 8. 版本状态与发布节奏

- 当前状态：**开发者预览**（0.1.0-rc.5），快速迭代，未来将出现破坏兼容性的变更。
- 预发布阶段立场：基础正确性优先于兼容垫片——可自由重命名或重新打包并同步更新所有引用；后端拒绝旧磁盘格式（SQLite 使用单调 `SCHEMA_VERSION`，会话格式版本不作兼容承诺）。
- npm 发布：包以 `@deepseek-ai/dsh-*` scope 发布，入口包为 `@deepseek-ai/dsh`。

## 9. 社区与支持

- GitHub Discussions：反馈与 bug 报告（https://github.com/deepseek-ai/deepseek-harness/discussions）
- 插件生态：为插件仓库添加 `dsh-plugin` 话题便于被发现（https://github.com/topics/dsh-plugin）
- 中文社区：企微群（扫码加企微小助手并填写入群问卷）、微信公众号
- 许可证：MIT

## 10. 适用场景

- **个人编码 agent**：Web UI + DeepSeek API，读改代码、运行命令、维护计划，带审批的人机协作。
- **自动化与 CI**：headless 一次性任务、ACP 服务器或 JSON-RPC/Python SDK 嵌入自有系统，无人值守执行任务。
- **平台化二次开发**：以组合包和 patch 层定制 agent 组合（工具集、权限、提示词、提供方），甚至让 agent 在运行时挂载新插件（`web-cordis` 自指示例）。
- **远程执行实验**：通过 seam 替换把文件系统、进程与终端指向远程沙箱（如 E2B POC）。

## 11. 延伸阅读（仓库内文档）

| 主题 | 文档 |
|---|---|
| 快速运行 | `README.zh.md` |
| Web UI 使用 | `docs/user/guide/index.zh.md` |
| 模型配置 | `docs/user/guide/providers.zh.md` |
| Python SDK | `docs/user/guide/python-sdk.zh.md`、`python/README.md` |
| 架构总览 | `docs/architecture.zh.md` |
| Cordis 入门与教程 | `docs/cordis-primer.zh.md`、`docs/cordis-tutorial/` |
| 子系统参考（40+ 页） | `docs/subsystems/` |
| 扩展实操手册 | `docs/cookbook/extension-cookbook.zh.md` |
| 工具 Schema 目录 | `docs/tool-catalog.zh.md` |
| 配置目录 | `docs/config-catalog.zh.md` |
| CLI 行为参考 | `apps/cli/reference/README.zh.md` |
| 开发指南 | `docs/development.zh.md` |
| Agent 约束 | 根目录 `AGENTS.md` |
