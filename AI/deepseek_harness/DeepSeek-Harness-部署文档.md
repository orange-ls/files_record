# DeepSeek Harness（dsh）部署文档

- 上游仓库：https://github.com/deepseek-ai/deepseek-harness
- 适用版本：0.1.0-rc.5（开发者预览阶段）
- 文档编写日期：2026-08-14
- 依据来源：仓库根 README、`apps/cli/reference/README.zh.md`（CLI 行为参考）、`docs/user/guide/`（用户指南）、`docs/development.zh.md`（开发指南）、`packages/boot/app-boot/README.zh.md`（Profile 机制）等官方文档

> 注意：DeepSeek Harness 目前处于**开发者预览**阶段，官方明确声明未来将出现破坏兼容性的变更。生产环境部署前请锁定版本并关注 Release Notes。

---

## 1. 项目简介与部署形态

DeepSeek Harness（命令名 `dsh`）是 DeepSeek AI 开发的开源 agent harness（智能体运行框架），采用"一切皆插件"架构，由 Cordis 框架驱动。一次 `dsh` 运行就是一棵按配置叠加组装起来的插件树。

它提供以下几种可部署的运行形态，可按需选择：

| 形态 | 命令/入口 | 说明 |
|---|---|---|
| Web UI（推荐） | `dsh web` | 启动 HTTP 服务 + 浏览器界面，默认 `http://127.0.0.1:3080` |
| Headless 一次性任务 | `dsh --profile headless "任务文本"` | 无交互运行一个任务，打印最终答案后退出；不开监听端口 |
| ACP 自动化服务器 | Agent Client Protocol，JSON-RPC stdio | 面向程序化客户端的自动化会话（见 `examples/acp-agent`） |
| JSON-RPC SDK | `packages/sdk`（protocol/client/server） | 从另一进程以 stdio JSON-RPC 驱动运行时，配套 TypeScript 客户端 |
| Python SDK | `pip install deepseek-harness-sdk` | 内置运行时，供 Python 程序内嵌调用 |

---

## 2. 环境要求

### 2.1 通过 npm 部署（仅运行，不做二次开发）

| 依赖 | 要求 |
|---|---|
| Node.js | `^22.19.0` 或 `>=24.0.0`（`package.json` engines 声明） |
| 网络 | 可访问 npm registry；运行时需要可访问所配置的模型 API 端点 |
| API 密钥 | DeepSeek API Key（或其他已配置提供方的凭据） |

### 2.2 从源码部署（完整构建）

| 依赖 | 要求 |
|---|---|
| Node.js | `^22.19.0` 或 `>=24.0.0`；CI 覆盖 22.19、24、26 |
| pnpm | 固定 `pnpm@11.7.0`（由 `packageManager` 字段声明），建议 `corepack enable` 后由 Corepack 解析 |
| Git | 2.26 或更高版本（安装钩子需要 worktree 配置扩展） |
| DeepSeek API Key | 可选；真实 API 的 e2e 测试与 agent 演示需要 |

### 2.3 Python SDK（可选）

| 依赖 | 要求 |
|---|---|
| Python | 3.10 或更高版本 |
| 平台 | Linux x64、Linux arm64、macOS 14+ arm64。**不支持 Windows**（持久 PTY 后端需要 POSIX 终端环境） |
| Node.js | 不需要，SDK 自带内置运行时 |

### 2.4 平台与沙箱说明

进程沙箱后端按平台提供：Linux 使用 bubblewrap（bwrap）或 Landlock（仓库附带原生模块 `@deepseek-ai/node-addon-landlock-run`），macOS 使用 Seatbelt（sandbox-exec）。Windows 下 shell 工具使用 PowerShell 方言（`pwsh` 工具）。新会话默认使用 `workspace-write` 权限预设。

---

## 3. 部署方式 A：npm 快速部署（推荐）

只需安装 Node.js，然后执行：

```sh
npx @deepseek-ai/dsh web
```

该命令会启动 Web UI，默认地址 `http://127.0.0.1:3080`，命令输出中也会打印访问地址。

如需全局安装后使用：

```sh
npm install -g @deepseek-ai/dsh
dsh web
```

指定端口：

```sh
dsh web --port 8080
```

> 注意：`dsh web` 的 flag（如 `--port`、`--host`、`--trusted-host`）属于 web 应用而非启动器，必须写在 `web` 之后。启动器自身无法识别的第一个 token 标志着应用参数的开始。

---

## 4. 部署方式 B：从源码部署

```sh
git clone https://github.com/deepseek-ai/deepseek-harness.git
cd deepseek-harness
corepack enable          # 若 pnpm 未通过 Corepack 解析
pnpm install             # 同时会安装 Lefthook 钩子与翻译配对合并驱动
pnpm run build           # tsc 发射 + tsdown 打包 + Web 前端构建
pnpm dsh web             # 启动 Web UI
```

构建说明：

- `pnpm run build` 依次执行 Host 侧 tsc + tsdown、Client 侧 tsc + tsdown 与 Web 前端构建（`build:lib:host` → `build:lib:client` → `build:web`）。
- 生产运行需要已构建的包与前端产物；`pnpm dsh <args...>` 通过 tsx 启动 TypeScript 入口并转发所有参数。
- 前端或 Client 插件产物缺失时启动会失败并提示先运行 `pnpm run build`；启动器不会检查产物是否最新，代码更新后需重新构建，否则可能继续运行旧版浏览器代码。

源码部署时如需运行真实 API 的演示或测试，在仓库根目录创建被 gitignore 的 `.env`：

```sh
DEEPSEEK_API_KEY=sk-...
DEEPSEEK_BASE_URL=https://...   # 可选，默认为公开 API
```

---

## 5. 首次配置

### 5.1 配置模型密钥（Web UI）

1. 打开 `http://127.0.0.1:3080`，进入 **设置 → 模型**。
2. 在 DeepSeek 卡片中输入 API 密钥并保存。模型路由立即可用，**无需重启服务器**。
3. 点击 **选择工作区**，添加并选中要操作的项目目录。选中工作区前会话输入框不可用。

密钥是只写的：保存后页面只会收到脱敏描述符，永远不会收到明文密钥。密钥存储在 `$DSH_HOME/.credentials.yaml`，settings 只保留凭据引用。

其他提供方：

- **目录提供方**：**添加提供方**，选取 Anthropic、OpenAI 等，输入 API 密钥保存。Bedrock、Vertex、Azure、Codex 使用各自原生凭据（AWS 凭据与区域、ADC 项目、`api-version`、OAuth），只填 API 密钥字段无法完成配置。
- **自定义提供方**：公司网关、自建服务器等选择 **添加自定义提供方**，提供小写 Provider ID、基础 URL、API 协议、凭据和至少一个模型。Provider ID 永久不可改（请求、会话、凭据引用都使用它）。
- 视觉模型需要在 `$DSH_HOME/settings.yaml` 中为模型声明 `input: [text, image]`，或在路由上设置 `defaultInput`，详见官方文档 `docs/user/guide/providers.zh.md`。

### 5.2 Harness Home（DSH_HOME）

所有用户态数据集中在 Harness home 目录：

- 解析规则：优先取环境变量 `$DSH_HOME`，否则为 `~/.dsh`。
- 目录内容：

| 路径 | 用途 |
|---|---|
| `$DSH_HOME/profiles/<name>/` | 各个 profile 目录（`package.json` + `cordis.patch.yml`） |
| `$DSH_HOME/profiles/node_modules` | dsh 维护的扁平符号链接后备目录，启动时自动修复 |
| `$DSH_HOME/cordis.patch.yml` | home 级用户 patch 层（所有 profile 共享的机器本地偏好，优先级高于逐 profile 层） |
| `$DSH_HOME/.env` | 产品 CLI 的普通环境层（低于调用目录 `.env` 与继承环境） |
| `$DSH_HOME/.credentials.yaml` | 受管凭据存储 |
| `$DSH_HOME/settings.yaml` | 用户设置（模型路由、权限等） |

### 5.3 凭据解析顺序

提供方凭据按以下优先级依次解析：

1. 继承环境（进程已有的环境变量）
2. `$DSH_HOME/.credentials.yaml`（Web UI 保存的密钥）
3. 调用目录的 `.env`
4. `$DSH_HOME/.env`

---

## 6. 运行模式与命令

### 6.1 命令总览

| 命令 | 用途 |
|---|---|
| `dsh --profile <name>` | 启动位于 `$DSH_HOME/profiles/<name>` 的 profile |
| `dsh web` | `--profile web` 的硬编码别名 |
| `dsh --profile headless "任务"` | 运行一次性任务，打印最终答案后退出 |
| `dsh plugin --profile <name> <pnpm 参数>` | 管理 profile 的树外插件（转发给 pnpm） |
| `dsh --profile web --dump-default-config` | 只打印组合包各层配置（不启动） |
| `dsh --profile web --dump-config` | 打印叠加用户 patch 与 overlay 后的完整配置树（不启动） |
| `dsh --help` / `dsh web --help` | 启动器帮助 / web 应用帮助 |

### 6.2 Web UI 部署细节

- 默认服务地址：`http://127.0.0.1:3080`。
- 支持的参数：`--host`、`--port`、可重复的 `--trusted-host`。
- **CLI 目前有意不支持 `--host 0.0.0.0`**，指定会以用法错误退出。如需对外提供服务，请保持本机绑定并通过反向代理转发（见第 10 节建议）。
- `--trusted-host` 可为 `/api` 浏览器信任围栏添加具名 authority。
- 运行命令时所在目录作为默认 workspace 根目录。
- 每次启动会加载适用的 `AGENTS.md` 或 `CLAUDE.md` 指令（65,536 字节渲染预算）。
- 会话内容索引使用内存 SQLite。

### 6.3 Headless 一次性任务

```sh
dsh --profile headless "summarize this workspace"
```

- 创建全新持久化 Agent，提交任务、等待完全停稳并 flush 会话，从持久化事件区间推导最后一个非空 assistant 文本与最终 `turn/end` 原因。
- 最终答案输出到 stdout；原因为 `completed` 时退出码 0，否则 1。无任务调用是用法错误。
- 不挂载 HTTP 服务器、Web 运行时和浏览器客户端，成功运行不写 stderr、不开端口。适合 CI/脚本/批处理集成。

### 6.4 ACP 与 SDK（自动化集成）

- **ACP 服务器**：Agent Client Protocol，通过 JSON-RPC stdio 提供全新 agent 会话，支持会话、权限和取消操作。源码演示：`pnpm run demo:acp`；可运行叶子配置：`examples/acp-agent/`。
- **JSON-RPC SDK**（`packages/sdk`）：protocol 定义运行时通信协议，server 通过 stdio JSON-RPC 服务进程外客户端，client 提供 TypeScript API。调用方提供运行时可执行文件及其 `cordis.yml`。
- **Python SDK**：

```sh
python -m venv .venv
. .venv/bin/activate                # Windows: .venv\Scripts\activate
pip install deepseek-harness-sdk
export DEEPSEEK_API_KEY=sk-your-key-here
python examples/jsonrpc-agent/minimal.py \
  --workspace /absolute/path/to/workspace \
  --session-root /absolute/path/to/sessions \
  --session-id example-001 \
  "Inspect the repository and fix the failing tests."
```

  安装后的运行时不需要系统提供 Node.js。只能运行于 Linux x64/arm64 与 macOS arm64；示例组合使用 `danger-full-access`，请在可丢弃的 checkout 或容器内运行。

---

## 7. 配置系统与自定义

### 7.1 组装机制（Profile 与组合包）

一个运行中的 `dsh` 是插件树，由启动时按序叠加的配置层组成。配置树以空根为起点，依次叠加：

1. profile manifest（`dsh.profile.bundles`）列出的各组合包 patch（内置：`@deepseek-ai/dsh-base`、`@deepseek-ai/dsh-web-app`、`@deepseek-ai/dsh-headless`）
2. profile 自身的 `cordis.patch.yml`
3. home 级 `$DSH_HOME/cordis.patch.yml`（机器本地偏好，优先级高于逐 profile 层）
4. 命令行按序指定的 `--patch <path>` 覆盖层

对同一配置行，后应用的层优先；patch 按 id 定位条目并**替换其整个 config**（不是深度合并），也可以插入新条目。

`web` 与 `headless` profile 首次使用时自动从随附模板初始化；其他 profile 需通过 `dsh plugin --profile <name> add <包>` 创建。

### 7.2 插件管理

```sh
# 安装树外插件组合包（git 依赖或 npm 包）
dsh plugin --profile tui add github:deepseek-harness/turtle-ui
dsh plugin --profile tui remove turtle-ui
dsh plugin --profile web add ./my-local-plugin    # 相对路径锚定调用目录
```

- `dsh plugin` 在 profile 缺失时先初始化，然后以 profile 目录为工作目录把参数转发给 pnpm（`add`/`remove`/`update`/`why` 等均可用，pnpm 必须在 PATH 上）。
- 每次成功运行后根据安装状态自动更新 `dsh.profile.bundles`；声明了 `"dsh": { "bundle": { "patch": "./cordis.patch.yml" } }` 的依赖会加入配置层栈。
- 从 Git 安装的插件需要在 profile 的 `pnpm-workspace.yaml` 中按其提示添加 `allowBuilds` 许可后重试；已构建好的 tarball 或本地 checkout 无需此步骤。
- CLI 随附 `@deepseek-ai/dsh-mcp-client` 作为 patch 层可用依赖，但**默认不启用任何 MCP 服务器**（每条服务器命令都是沙箱之外的受信任可执行代码）。

### 7.3 配置审查

```sh
dsh --profile web --dump-default-config          # 仅组合包层
dsh --profile web --patch ./extra.yml --dump-config  # 含全部用户层与 overlay
```

输出会注释标明每行由哪个文件提供、哪些 overlay 修改过它；`!!js` 表达式保持未求值；找不到目标的 patch 报告到 stderr。dump 不接受应用参数（如 `--port`）。

### 7.4 热更新

每次 profile 启动都会持续监视 profile 与 home 两个 `cordis.patch.yml` 的有效变更，并以事务方式重新应用。在线编辑 `cordis.patch.yml` 时，运行时读取的表达式（如端口）会根据仍在运行的服务重新计算，不会重置当前端口。读取/解析失败时最后一个可用树继续运行，并通过 HMR 服务广播配置更新失败事件。

---

## 8. 权限、沙箱与安全

- 新会话默认使用 **`workspace-write`** 权限预设：Bash 和文件系统修改仅限于会话 workspace 与平台临时根目录；读取、网络访问和进程可见性不受限制。环境变量 `DSH_PERMISSION_MODE` 可更改进程后备值；Web 设置中存储的权限影响后续新会话，不改变已打开的会话。
- 需要审批的操作会先向用户询问（Web UI 中弹出审批）。
- 进程沙箱后端：Linux bwrap/Landlock、macOS Seatbelt，由 `ctx.sandbox` 后端在启动进程前包装 argv。
- 会话遥测**默认留在本地**。`DSH_TELEMETRY_MODE=FULL` 将每条已投影会话事件作为 OTLP/HTTP 日志外发，`FEEDBACK_ONLY` 仅在记录反馈时上传会话日志后缀；`DSH_TELEMETRY_OTLP_URL` 指定其他 collector；任何非空 `DSH_TELEMETRY_DISABLED` 是具有最终效力的强制关闭开关。官方提醒：基础配置没有脱敏规则，显式启用的导出可能包含消息文本、工具参数与结果、workspace 路径。
- 密钥永不回显：Web UI 保存后只返回脱敏描述符。请勿提交任何真实凭证到版本库。

---

## 9. 运维管理

### 9.1 启动与关闭行为

- 收到 `SIGINT` 或 `SIGTERM` 时，挂载的插件树先 dispose（资源释放）再退出，最多 5 秒。
- `SIGTERM` 为监督进程发出的常规停止请求，所有运行模式都以退出码 **0** 结束；`SIGINT` 报告 **130**。
- 第二次收到信号时立即强制退出；一次性运行若已卡在 dispose 阶段，第一次 `Ctrl+C` 即升级为强制退出。
- systemd 集成建议（非官方，供参考）：以 `SIGTERM` 作为停止信号，`TimeoutStopSec` 不小于 10 秒，进程类型 simple，按退出码 0 判定正常停止。

### 9.2 升级

- npm 部署：重新执行 `npx @deepseek-ai/dsh@latest web` 或更新全局安装版本。
- 源码部署：`git pull` 后重新执行 `pnpm install && pnpm run build`。
- 项目处于开发者预览阶段，升级前请阅读 Release Notes，备份 `$DSH_HOME`（含 profiles、settings、凭据与会话数据）。

### 9.3 数据与备份

需要持久保护的数据集中在 `$DSH_HOME`（默认 `~/.dsh`）：profiles、`settings.yaml`、`.credentials.yaml`、`.env`、`cordis.patch.yml` 与会话持久化数据（JSONL / SQLite 后端）。备份该目录即可迁移部署。

---

## 10. 网络暴露建议（非官方，供参考）

`dsh web` 默认绑定 `127.0.0.1` 且有意拒绝 `--host 0.0.0.0`。如需让局域网或公网用户访问，推荐在本机或容器内保持默认绑定，由反向代理转发，例如 nginx：

```nginx
server {
    listen 80;
    server_name dsh.example.com;

    location / {
        proxy_pass http://127.0.0.1:3080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;      # WebSocket/长连接
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

注意要点：

- Web 服务承载 agent 的文件读写与命令执行能力，**对外暴露前必须配置认证**（反向代理层 Basic Auth / OAuth2 Proxy / 企业网关均可），并严格限制可访问人群。
- 必要时用 `--trusted-host` 把代理的 authority 加入 `/api` 浏览器信任围栏。
- 建议在专用机器、容器或虚拟机中运行，并理解所选权限预设的边界（默认 `workspace-write`）。

---

## 11. 常见问题排查

| 现象 | 处理 |
|---|---|
| `MISSING_CREDENTIAL` | 通过模型页存储提供方密钥，或提供被引用的环境变量 |
| `UNKNOWN_MODEL` | 选择已配置的模型，或向自定义提供方添加缺失的模型 |
| 获取可用模型返回 401 | 检查密钥；模型发现调用 OpenAI 兼容 `GET /models`，不提供该端点的服务请手动输入模型 |
| 图片在发送前被拒绝 | 该模型未声明图片模态；给自定义提供方模型加 `input: [text, image]`。DeepSeek 自身的 chat-completions 路由是纯文本且无法通过配置改变 |
| 提供方拒绝带图片的请求 | 模型声明了端点实际没有的图片能力；从授予其图片能力的列表（`input` 或 `defaultInput`）中移除 `image` 并开启新会话 |
| `--host 0.0.0.0` 启动失败 | 属有意设计；请保持本机绑定并用反向代理转发 |
| 源码启动报模块解析错误 | Typert Host 产物缺失，先在仓库根目录运行 `pnpm run build` |
| 更新代码后页面仍是旧版 | 启动器不检查产物新旧，重新 `pnpm run build` 后重启 |
| 模型发现 401 之外的端点问题 | 检查 `DEEPSEEK_BASE_URL` 是否指向了错误的网关 |
| 保存的默认模型指向已删除提供方 | 输入框显示"选择模型"并阻止输入，选择其他模型即可 |

---

## 12. 附录：环境变量速查

| 变量 | 作用 |
|---|---|
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥（模型与 `web_search` 共用） |
| `DEEPSEEK_BASE_URL` | 可选，自定义 DeepSeek 兼容端点，默认公开 API |
| `DEEPSEEK_SEARCH_BASE_URL` | 可选，web 搜索端点 |
| `DSH_HOME` | 指定 Harness home 目录，默认 `~/.dsh` |
| `DSH_MODEL` | 模型名（Python SDK 示例组合等场景使用） |
| `DSH_SYSTEM_PROMPT` | 覆盖系统提示词（Python SDK 示例组合等场景使用） |
| `DSH_SESSION_ROOT` | 会话日志目录（Python SDK 示例组合） |
| `DSH_PERMISSION_MODE` | 更改进程的默认权限预设后备值 |
| `DSH_TOOLS_MODE` | `native` / `code` / `both`，其他值启动失败 |
| `DSH_TELEMETRY_MODE` | `FULL` / `FEEDBACK_ONLY`，默认本地不外发 |
| `DSH_TELEMETRY_OTLP_URL` | 指定 OTLP collector |
| `DSH_TELEMETRY_DISABLED` | 非空即最终关闭遥测 |
| `NODE_USE_ENV_PROXY` | 需要 Node 遵循 `HTTP_PROXY`/`HTTPS_PROXY` 时设置为 1 |

## 13. 参考资料

- 根 README（运行入口）：`README.zh.md`
- Web UI 指南：`docs/user/guide/index.zh.md`
- 模型配置指南：`docs/user/guide/providers.zh.md`
- Python SDK 快速上手：`docs/user/guide/python-sdk.zh.md`
- CLI 行为参考（flag、关闭行为、部署默认值）：`apps/cli/reference/README.zh.md`
- 架构文档：`docs/architecture.zh.md`
- 配置目录（自动生成，全部受支持字段与默认值）：`docs/config-catalog.zh.md`
- 工具 Schema 目录：`docs/tool-catalog.zh.md`
- 开发指南：`docs/development.zh.md`
- 社区支持：GitHub Discussions https://github.com/deepseek-ai/deepseek-harness/discussions
