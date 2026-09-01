# DSH 插件开发指南与解耦架构方案

本文说明 DSH 插件的定义、配置、安装、加载和升级方式，并给出适合 AIBMS 业务插件的长期解耦方案。

本文参考 DSH 仓库中的开发手册与 CLI 行为参考，参考版本为 `0.1.2-alpha.3`。DSH 当前属于预发布版本，具体 API 以目标发行包的 `exports`、TypeScript 声明和对应 README 为准。

## 1. 推荐方案

把自定义插件交付为独立的 npm 包或 tarball，并让它包含一个 DSH Bundle：

```text
@dcg/aibms-dsh-bundle/
  ├── package.json          # dsh.bundle 声明、exports、版本约束
  ├── cordis.patch.yml      # DSH 配置层
  ├── lib/runtime.js        # DSH Host 适配入口
  ├── lib/client.js         # 可选，Web Client 入口
  └── README.md
```

推荐依赖方向：

```text
业务核心 core
    ↑
DSH 适配层 adapter  ── 公开 DSH API
    ↑
Bundle 分发层      ── package.json + cordis.patch.yml
```

业务规则、数据模型、AIBMS 后端客户端和错误码放在不依赖 DSH 的核心包中。只有适配层直接依赖 `@deepseek-ai/cordis`、`@deepseek-ai/dsh-tools` 等公开包。Bundle 只负责安装和挂载，不承载业务逻辑。

这套方案不能承诺插件永远兼容任意 DSH 版本。它的目标是把版本变化限制在适配层，并通过 peer dependency、兼容矩阵和打包安装测试提前发现不兼容。

## 2. DSH 的插件模型

### 2.1 Cordis Plugin

Cordis Plugin 是运行时插件模块。最小形式是导出 `apply`：

```ts
import type { Context } from '@deepseek-ai/cordis'

export const name = 'hello-plugin'

export function apply(ctx: Context) {
  console.log('[hello-plugin] loaded')
}
```

DSH 加载模块后调用 `apply(ctx)`。`ctx` 是插件注册服务、工具、事件监听器和资源的入口。

函数插件的推荐导出约定是：

```ts
export const name = 'my-plugin'
export const inject = ['tools']
export const Config = /* Schemastery schema */
export function apply(ctx: Context, config: Config) { /* ... */ }
```

函数插件使用命名导出，不要额外提供 default export。服务类插件是另一种形式：它通常 default-export 一个 Cordis `Service` 子类。

### 2.2 Bundle

Bundle 是可以安装到 profile 的 npm 包。它通过 `dsh.bundle.patch` 指向一个 Cordis patch：

```json
{
  "name": "@dcg/aibms-dsh-bundle",
  "version": "1.0.0",
  "type": "module",
  "dsh": {
    "bundle": {
      "patch": "./cordis.patch.yml"
    }
  }
}
```

patch 再引用真正的插件入口：

```yaml
- insert:
    - id: dcg-aibms-runtime
      name: '@dcg/aibms-dsh-bundle/runtime'
      config:
        apiBaseUrl: 'https://aibms.example.com'
        timeoutMs: 30000
```

没有 `dsh.bundle` 的包仍可以安装，但只是普通依赖，不会自动成为配置层。

### 2.3 Profile

Profile 是一套可运行的 DSH 组合，目录为：

```text
$DSH_HOME/profiles/<profile-name>/
  ├── package.json
  ├── pnpm-workspace.yaml
  ├── cordis.patch.yml
  └── node_modules/
```

Profile 的 `package.json` 由 `dsh plugin` 维护：

```json
{
  "dependencies": {
    "@dcg/aibms-dsh-bundle": "1.0.0"
  },
  "dsh": {
    "profile": {
      "bundles": [
        "@deepseek-ai/dsh-base",
        "@deepseek-ai/dsh-web-app",
        "@dcg/aibms-dsh-bundle"
      ],
      "patchReload": "live"
    }
  }
}
```

不要手工维护 `dsh.profile.bundles`，使用 `dsh plugin --profile <name> add/remove/update`。

### 2.4 动态 Cordis Plugin

DSH 的 `@deepseek-ai/dsh-tool-cordis` 可以在当前进程中动态定义 JavaScript 插件。这类插件重启后消失，适合临时实验，不适合生产交付。

| 类型 | 生命周期 | 安装位置 | 用途 |
|---|---|---|---|
| 外部 Bundle | Profile 和版本管理 | profile 的 `node_modules` | 测试、生产、可重复部署 |
| 动态 Plugin | 当前进程/会话 | 进程内存 | 临时实验 |

## 3. 插件如何被加载

DSH 不会扫描任意 `plugins` 目录。实际流程如下：

```text
dsh plugin --profile web add <package>
  ├─ 在 $DSH_HOME/profiles/web 中执行 pnpm add
  ├─ 读取已安装依赖的 package.json
  ├─ 找到 dsh.bundle.patch
  └─ 把 Bundle 加入 dsh.profile.bundles

dsh web
  ├─ 读取 profile 的 dsh.profile.bundles
  ├─ 按顺序应用 Bundle 的 cordis.patch.yml
  ├─ 应用 profile/cordis.patch.yml
  ├─ 应用 $DSH_HOME/cordis.patch.yml
  ├─ 应用命令行 --patch overlay
  ├─ Loader 解析每个 row 的 name
  ├─ 等待 inject 声明的服务
  ├─ 校验 Config schema
  ├─ 调用 apply(ctx, config)
  └─ 退出或 reload 时释放 ctx.effect / ctx.on
```

配置层顺序是：

1. `dsh.profile.bundles` 中的 Bundle patch，按列表顺序。
2. Profile 自己的 `cordis.patch.yml`。
3. `$DSH_HOME/cordis.patch.yml`。
4. 命令行中的 `--patch` 文件，按参数顺序。

后应用的 patch 优先级更高。同一个 row 被覆盖时，`config` 是整体替换，不是深度合并。覆盖时必须重新写出该 row 需要的完整配置。

Bundle 名称先从 DSH 安装解析，外部 Bundle 再从 profile 的 `node_modules` 解析。每个 profile 可以独立安装和升级外部插件。

## 4. 开发一个最小插件

### 4.1 目录

建议将插件放在 DSH 仓库之外，例如：

```text
/opt/aibms-dsh-plugins/aibms-dsh-bundle/
  ├── package.json
  ├── tsconfig.json
  ├── tsdown.config.ts
  ├── cordis.patch.yml
  ├── src/runtime.ts
  ├── src/types.ts
  ├── tests/
  └── README.md
```

不要把生产插件放入 DSH 源码仓库的 `local-plugins`。DSH 升级时替换 DSH 安装目录，插件包单独升级。

### 4.2 插件入口

```ts
// src/runtime.ts
import type { Context } from '@deepseek-ai/cordis'
import Schema from '@deepseek-ai/schemastery'

export const name = 'aibms-dsh-runtime'
export const inject = []

export interface Config {
  apiBaseUrl: string
  timeoutMs: number
}

export const Config: Schema<Config> = Schema.object({
  apiBaseUrl: Schema.string().required(),
  timeoutMs: Schema.number().default(30000),
})

export function apply(ctx: Context, config: Config) {
  console.log('[aibms-dsh] connected to ' + config.apiBaseUrl)

  ctx.effect(() => {
    // 创建连接、timer、watcher 等资源。
    return () => {
      // 关闭连接并释放资源。
    }
  })
}
```

### 4.3 Patch

```yaml
# cordis.patch.yml
- insert:
    - id: dcg-aibms-runtime
      name: '@dcg/aibms-dsh-bundle/runtime'
      config:
        apiBaseUrl: 'https://aibms.example.com'
        timeoutMs: 30000
```

发布包中使用包名或 exported subpath。只有开发 overlay 才使用绝对源码路径：

```yaml
- insert:
    - id: dcg-aibms-runtime
      name: '/absolute/path/to/aibms-dsh-bundle/src/runtime.ts'
```

开发启动：

```sh
pnpm dsh web --patch /absolute/path/to/aibms-dsh-bundle/cordis.dev.patch.yml
```

正式环境使用构建后的 Bundle，不要依赖 `tsx`、TypeScript 源码路径或开发机目录。

## 5. 服务、工具、配置和生命周期

### 5.1 用 inject 表达依赖

不要依赖 YAML 行顺序保证启动顺序。Loader 可能并发处理条目，依赖关系通过 `inject` 表达：

```ts
import type { Context } from '@deepseek-ai/cordis'
import { defineTool } from '@deepseek-ai/dsh-tools'

export const name = 'aibms-business-tools'
export const inject = ['tools']

export function apply(ctx: Context) {
  ctx.tools.register(defineTool({
    name: 'aibms_query',
    description: 'Query AIBMS business data.',
    parameters: {
      keyword: {
        type: 'string',
        required: true,
        description: 'Search keyword',
      },
    },
    output: {
      schema: { type: 'string' },
      render: (_args, value) => [{ type: 'text', text: value }],
    },
    async execute(args) {
      return 'query: ' + args.keyword
    },
  }))
}
```

可选服务使用 `ctx.get('serviceName')`，不要假设 `ctx.serviceName` 一定存在。

### 5.2 配置 schema

```ts
import Schema from '@deepseek-ai/schemastery'

export interface Config {
  endpoint: string
  timeoutMs: number
  enabled: boolean
}

export const Config: Schema<Config> = Schema.object({
  endpoint: Schema.string().required(),
  timeoutMs: Schema.number().default(30000),
  enabled: Schema.boolean().default(true),
})
```

规则：

- 所有随部署变化的参数都定义为配置字段。
- 无效配置在加载阶段失败，不允许半配置启动。
- API key 不放入 patch、npm 包和 Git。
- 密钥优先使用环境变量引用或 DSH credentials 能力。
- patch 覆盖 row 时重新写出完整配置。

### 5.3 生命周期

`ctx.on()` 和 `ctx.effect()` 注册的副作用绑定当前插件实例。配置 HMR 或卸载时，DSH 会释放这些注册：

```ts
export function apply(ctx: Context) {
  const timer = setInterval(() => {
    console.log('[aibms-dsh] heartbeat')
  }, 5000)

  ctx.effect(() => () => clearInterval(timer))
}
```

网络连接、文件 watcher、子进程、定时器和临时目录必须有 disposer。

### 5.4 事件

对 waterfall 事件进行拦截、包装或放行时必须调用 `next()`：

```ts
export function apply(ctx: Context) {
  ctx.on('tools/pre-execute', async (execution, next) => {
    if (!isAllowed(execution)) {
      return { kind: 'deny', reason: 'AIBMS policy denied this call.' }
    }
    return next()
  })
}
```

能通过服务或工具注册完成的功能，不要修改 agent loop。

## 6. 打包和安装

### 6.1 Bundle package.json

```json
{
  "name": "@dcg/aibms-dsh-bundle",
  "version": "1.0.0",
  "type": "module",
  "exports": {
    ".": {
      "types": "./lib/types.d.ts",
      "default": "./lib/index.js"
    },
    "./runtime": {
      "types": "./lib/runtime.d.ts",
      "default": "./lib/runtime.js"
    }
  },
  "files": ["lib", "cordis.patch.yml", "README.md"],
  "scripts": {
    "build": "tsdown",
    "test": "vitest run",
    "prepare": "pnpm run build"
  },
  "dependencies": {
    "@dcg/aibms-core": "^1.0.0"
  },
  "peerDependencies": {
    "@deepseek-ai/cordis": ">=0.1.2-alpha.3 <0.2.0",
    "@deepseek-ai/dsh-tools": ">=0.1.2-alpha.3 <0.2.0"
  },
  "dsh": {
    "bundle": {
      "patch": "./cordis.patch.yml"
    }
  }
}
```

要求：

- 外部包使用正常 semver，不要发布 `workspace:^`。
- DSH 运行时包作为 peer dependency，避免插件带入第二份运行时。
- `files` 必须包含构建产物和 patch。
- `exports` 只暴露真正需要的入口，不暴露源码内部文件。

### 6.2 构建和安装

```sh
pnpm install
pnpm run build
pnpm pack
dsh plugin --profile web add /absolute/path/to/dcg-aibms-dsh-bundle-1.0.0.tgz
dsh --profile web --dump-config
dsh web --no-open
```

正式流程使用 `dsh plugin`，因为它会在 pnpm 成功后识别 `dsh.bundle` 并维护 `dsh.profile.bundles`。添加、移除或更新 Bundle 后要重启 profile。

### 6.3 npm、tarball 和 Git

推荐顺序：

1. npm 发布已构建产物。
2. 发布固定版本的 tarball。
3. Git 安装并使用自包含的 `prepare` 构建脚本。

Git 安装获取源码。若没有 `lib`，启动会因入口缺失失败；pnpm 还可能要求在 profile 的 `pnpm-workspace.yaml` 中配置 `allowBuilds`。这等同于允许安装包在本机执行构建代码，只允许可信包，并固定 commit SHA：

```sh
dsh plugin --profile web add github:dcg/aibms-dsh-bundle#<commit-sha>
```

不希望安装阶段执行构建时，使用包含 `lib` 的 npm 包或 tarball。

## 7. AIBMS 解耦架构

### 7.1 包划分

简单功能可以先使用一个 Bundle。持续扩展的业务建议拆成：

```text
@dcg/aibms-dsh-contract
  └── 业务请求、结果、错误码和 port；不依赖 DSH

@dcg/aibms-core
  └── 业务用例、校验、编排；不依赖 DSH

@dcg/aibms-dsh-adapter
  └── apply、inject、Config、工具注册、DSH 生命周期

@dcg/aibms-dsh-bundle
  └── package.json、cordis.patch.yml、构建产物和版本声明
```

依赖方向：

```text
contract  ←  core  ←  dsh-adapter  ←  bundle
                         ↑
                 DSH public packages
```

禁止：

```text
core     ──> @deepseek-ai/dsh-*
任何包   ──> apps/cli/src/*
adapter  ──> ../../packages/*/*/src/*
任何包   ──> /opt/aibms-dsh 的绝对路径
```

### 7.2 职责表

| 层 | 可以依赖 | 负责 | 不负责 |
|---|---|---|---|
| Contract | TypeScript 标准库 | DTO、错误码、port | Cordis、工具 schema、UI |
| Core | Contract、HTTP/JSON 库 | 业务规则和用例 | Context、profile、prompt |
| Adapter | Core、公开 DSH 包 | apply、工具、事件、配置 | 业务规则实现 |
| Bundle | Adapter 入口 | manifest、patch、发行文件 | 运行时业务逻辑 |
| Client | 公开 Web API | 浏览器 UI 和用户交互 | API key 和服务器文件 |

### 7.3 业务核心示例

```ts
// @dcg/aibms-dsh-contract
export interface AibmsQuery {
  keyword: string
}

export interface AibmsQueryResult {
  items: readonly { id: string; title: string }[]
}

export interface AibmsGateway {
  query(request: AibmsQuery, signal?: AbortSignal): Promise<AibmsQueryResult>
}
```

```ts
// @dcg/aibms-core
import type { AibmsGateway, AibmsQuery, AibmsQueryResult } from '@dcg/aibms-dsh-contract'

export function createAibmsUseCases(gateway: AibmsGateway) {
  return {
    async query(request: AibmsQuery, signal?: AbortSignal): Promise<AibmsQueryResult> {
      const keyword = request.keyword.trim()
      if (keyword.length === 0) throw new Error('AIBMS_QUERY_KEYWORD_REQUIRED')
      return gateway.query({ keyword }, signal)
    },
  }
}
```

这两个包不需要安装 DSH，可以被 HTTP API、批处理、测试程序和 DSH Adapter 复用。

### 7.4 DSH Adapter 示例

```ts
// @dcg/aibms-dsh-adapter/src/runtime.ts
import type { Context } from '@deepseek-ai/cordis'
import Schema from '@deepseek-ai/schemastery'
import { defineTool } from '@deepseek-ai/dsh-tools'
import { createAibmsUseCases } from '@dcg/aibms-core'
import { createAibmsHttpGateway } from './aibms-http-gateway.js'

export const name = 'aibms-dsh-adapter'
export const inject = ['tools']

export interface Config {
  apiBaseUrl: string
  apiKeyEnv: string
  timeoutMs: number
}

export const Config: Schema<Config> = Schema.object({
  apiBaseUrl: Schema.string().required(),
  apiKeyEnv: Schema.string().default('AIBMS_API_KEY'),
  timeoutMs: Schema.number().default(30000),
})

export function apply(ctx: Context, config: Config) {
  const apiKey = process.env[config.apiKeyEnv]
  if (!apiKey) throw new Error('Missing ' + config.apiKeyEnv)

  const gateway = createAibmsHttpGateway({
    baseUrl: config.apiBaseUrl,
    apiKey,
    timeoutMs: config.timeoutMs,
  })
  const useCases = createAibmsUseCases(gateway)

  ctx.tools.register(defineTool({
    name: 'aibms_query',
    description: 'Query AIBMS business data by keyword.',
    parameters: {
      keyword: { type: 'string', required: true, description: 'Business keyword' },
    },
    output: {
      schema: { type: 'string' },
      render: (_args, value) => [{ type: 'text', text: value }],
    },
    async execute(args, execution) {
      const result = await useCases.query({ keyword: args.keyword }, execution.signal)
      return JSON.stringify(result)
    },
  }))

  ctx.effect(() => () => gateway.close())
}
```

DSH 只负责把模型工具调用转换为 `AibmsQuery`。核心包负责业务校验和用例，Gateway 负责 AIBMS 后端协议。

### 7.5 Bundle patch

```yaml
- insert:
    - id: dcg-aibms-dsh-adapter
      name: '@dcg/aibms-dsh-adapter'
      inject: [tools]
      config:
        apiBaseUrl: !!js process.env.AIBMS_API_BASE_URL
        apiKeyEnv: 'AIBMS_API_KEY'
        timeoutMs: 30000
```

`apiKeyEnv` 是环境变量名称，不是密钥本身。

## 8. 版本兼容策略

### 8.1 只依赖公开出口

可以依赖的范围包括：

- `@deepseek-ai/cordis` 的 `Context`、`Service`、事件和生命周期原语。
- `@deepseek-ai/dsh-tools` 的工具定义和注册 API。
- `@deepseek-ai/dsh-cmdline` 的插件参数解析 API。
- 目标能力的 Service Definition 包，例如 LLM、Session、FS。
- DSH 明确公开的 Web Client module / conversation API。

不要导入 `apps/cli/src`、任意包的 `src` 私有实现、`vendor/cordis` 内部文件或 profile 的 `node_modules` 相对路径。公开包也必须以其 README 和 `exports` 为准。

### 8.2 兼容矩阵

| 插件版本 | 支持的 DSH 版本 | 适配层 |
|---|---|---|
| `1.x` | `0.1.x` | `adapter-v1` |
| `2.x` | `0.2.x` | `adapter-v2` |
| `3.x` | `1.x` | `adapter-v3` |

peer dependency 范围代表已经测试过的集合，不要为了让安装通过而盲目放宽。

### 8.3 适配层隔离

发生不兼容变化时，保留 Core，只新增 Adapter：

```text
src/
  core/
  adapter/
    dsh-0.1.ts
    dsh-0.2.ts
    select.ts
```

更稳妥的方式是不同 DSH 兼容线发布不同 Bundle，例如 `@dcg/aibms-dsh-bundle-0.1` 和 `@dcg/aibms-dsh-bundle-0.2`。不要在业务核心中散落 `if (dshVersion)`。

### 8.4 peer dependency

```json
{
  "peerDependencies": {
    "@deepseek-ai/cordis": ">=0.1.2-alpha.3 <0.2.0",
    "@deepseek-ai/dsh-tools": ">=0.1.2-alpha.3 <0.2.0"
  },
  "engines": {
    "node": ">=22.19.0"
  }
}
```

如果 Adapter 使用其他 DSH Service Definition，也将其列为 peer dependency，并在干净 profile 中验证由当前 DSH 提供，而不是插件自己带入第二份。

## 9. Web Client 插件

纯工具、后端连接和事件审计插件只做 Host 侧，不需要 `dsh.client`。需要浏览器 UI 时才增加 Client 入口：

1. `package.json` 声明 `dsh.client`。
2. `exports` 暴露 `./client`。
3. 构建 Host 和 Client bundle。
4. 用 `dsh.client.external` 声明基座之外的模块。
5. 使用公开的 Web Client conversation/module API。

示例声明：

```json
{
  "exports": {
    ".": "./lib/index.js",
    "./client": "./lib/client.js"
  },
  "dsh": {
    "client": {
      "platform": "web",
      "inject": ["@deepseek-ai/dsh-client-connection"],
      "external": []
    }
  }
}
```

浏览器代码不能读取服务器环境变量、API key 或 `.dsh` 文件。Host 侧返回经过授权和裁剪的数据。

## 10. 测试和交付

核心包测试：

- 业务输入校验、后端响应转换、超时、取消、重试、错误码和空结果。

Adapter 测试：

- 工具 schema、工具执行、取消信号传递、配置失败、dispose 后资源释放。

至少增加一次真实 Loader 组合测试：

```text
临时 DSH home
  └── 临时 profile
       ├── 安装构建后的 tarball
       ├── dsh plugin --profile test add <tarball>
       ├── dsh --profile test --dump-config
       └── 启动并验证真实工具/用户输出
```

发布前：

```sh
pnpm install
pnpm run test
pnpm run build
pnpm pack
```

不要只测试源码启动。源码可以依赖 `tsx` 和 workspace 路径，发布包必须在没有 DSH monorepo 源码目录的环境中加载。

## 11. 测试、生产和 DSH 升级

测试和生产使用独立的 DSH home、profile、凭据和端口：

```text
测试：/home/openclaw-test/.dsh
生产：/home/aibms-prod/.dsh
```

分别设置：

```ini
Environment=HOME=/home/openclaw-test
Environment=DSH_HOME=/home/openclaw-test/.dsh
```

```ini
Environment=HOME=/home/aibms-prod
Environment=DSH_HOME=/home/aibms-prod/.dsh
```

不要共用 profile 或 `.dsh`。其中可能包含 token、模型配置、会话和插件安装状态。

部署清单固定三类版本：

```text
DSH:    0.1.2-alpha.3
Plugin: @dcg/aibms-dsh-bundle@1.0.0
Node:   24.x
pnpm:   11.x
```

升级顺序：

1. 测试 profile 安装新 DSH。
2. 根据兼容矩阵选择插件版本。
3. 在测试 profile 更新 Bundle。
4. 执行 `dsh --profile test --dump-config`。
5. 启动 Web 并执行真实业务流程。
6. 备份生产 `$DSH_HOME` 后再升级。
7. Bundle 版本变化后重启 DSH。

生产不要直接覆盖插件目录。使用不可变版本目录或版本化 tarball，回滚时恢复上一个 profile manifest 和插件版本。

## 12. 安全要求

DSH 插件是受信任的 Node 代码，安装和启动插件等同于允许其在 DSH 进程权限下执行代码。

- 只安装可审计、可追溯来源的包。
- 生产固定 npm 版本、tarball 哈希或 Git commit SHA。
- Git 安装的 `prepare` 脚本经过审核后再配置 `allowBuilds`。
- API key、DSH token、数据库凭据不进入 Git、npm 包、patch 和普通日志。
- HTTP 请求设置超时、取消和响应大小限制。
- 工具参数在业务核心再次校验。
- 文件、子进程和网络权限通过 DSH 已有能力和策略控制。
- 日志脱敏 URL query、Authorization header、请求体和异常对象。

## 13. 常见问题

### Bundle 已安装但没有加载

确认包包含：

```json
"dsh": {
  "bundle": {
    "patch": "./cordis.patch.yml"
  }
}
```

然后运行：

```sh
dsh --profile web --dump-config
```

如果没有 Bundle 层，检查 `dsh.bundle`、`files`、patch 是否在发布包中，并确认安装使用的是 `dsh plugin`。

### apply 没执行

检查 patch 的 `name`、package `exports`、构建产物、`inject` 服务、Config schema，以及修改 Bundle 后是否重启 profile。

### Git 安装提示 allowBuilds

优先改用 npm 包或预构建 tarball。必须使用 Git 时，审核源码，把 pnpm 输出的精确包名加入 profile 的 `pnpm-workspace.yaml`，再重复安装。

### DSH 升级后启动失败

执行：

```sh
dsh --version
node --version
pnpm --version
dsh --profile web --dump-config
```

先确认 DSH 和插件版本在兼容矩阵内，再检查 Adapter 使用的公开包导出。不要重新导入 DSH 私有源码来绕过问题，应发布新的 Adapter。

## 14. 官方参考资料

以下路径相对于 DSH 仓库根目录：

| 主题 | 文件 |
|---|---|
| CLI、profile、Bundle 加载 | `apps/cli/reference/README.zh.md` |
| 最小插件和 `apply(ctx)` | `docs/user/develop/basic/index.zh.md` |
| 配置和 schema | `docs/user/develop/basic/config.zh.md` |
| 打包、安装和 `dsh.bundle` | `docs/user/develop/basic/publish.zh.md` |
| Tool 插件 | `docs/user/develop/basic/tool.zh.md` |
| Cordis 插件形态 | `docs/cordis-tutorial/01-first-plugin.zh.md` |
| 服务和生命周期 | `docs/cordis-tutorial/03-services.zh.md`、`02-lifecycle-and-effects.zh.md` |
| Definition / Provider / Consumer | `docs/user/develop/practice/index.zh.md` |
| 扩展点映射 | `docs/architecture.zh.md`、`docs/cookbook/extension-cookbook.zh.md` |
| Web Client bundle | `packages/client/modules/README.zh.md` |

## 15. 落地清单

1. 定义不依赖 DSH 的业务 Contract 和 Core。
2. 决定功能属于工具、服务提供方、事件观察器还是 Web Client。
3. 在 Adapter 中实现 `name`、`inject`、`Config` 和 `apply`。
4. 通过 `ctx.effect()` 和 `ctx.on()` 管理可逆副作用。
5. 用 `cordis.patch.yml` 插入 Adapter。
6. 在 `package.json` 声明 `dsh.bundle.patch`、`exports`、`files` 和 peer dependencies。
7. 构建并 `pnpm pack`，在干净 profile 中通过 `dsh plugin add` 安装。
8. 用 `dsh --profile <name> --dump-config` 验证 Bundle 层。
9. 执行真实工具和用户流程测试。
10. 为每个 DSH 兼容线维护 Adapter、peer dependency 和发布版本。
11. 测试和生产分别使用独立的 `DSH_HOME`、profile、凭据和端口。
12. DSH 升级时先验证测试环境，再升级生产。
