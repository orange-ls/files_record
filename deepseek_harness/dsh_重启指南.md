# DeepSeek Harness 重启指南

本说明用于在“所有 dsh 相关进程都已关闭”的场景下（例如重启电脑、手动结束 Node 进程），快速把项目重新跑起来。

## 前置条件

- 已完成首次安装：`pnpm install` + `pnpm run build`
- 已配置 API Key：`D:\Github\deepseek-harness\.env` 中填写了 `DEEPSEEK_API_KEY`
- Git Bash、cmd、PowerShell 均可运行，只有路径写法不同

## 终端选择

三种终端都能运行 dsh，命令本身完全相同，只有进入目录的写法不同：

| 终端 | 进入项目目录 |
|---|---|
| Git Bash | `cd /d/Github/deepseek-harness` |
| cmd | `cd /d D:\Github\deepseek-harness` |
| PowerShell | `cd D:\Github\deepseek-harness` |

建议：日常使用任选其一即可；若某些诊断命令涉及 `$`、`_` 等特殊字符，PowerShell 建议写成 `.ps1` 脚本再执行，避免内联解析问题。

## 重启步骤

任选上表中的一个终端，进入项目目录后执行对应命令。

### 1. 命令行 / 无头模式

适合单次任务，不启动 Web UI：

```bash
pnpm dsh --profile headless "你要执行的任务"
```

### 2. Web UI 模式

启动图形界面，默认监听 `127.0.0.1:3080`：

```bash
pnpm dsh --profile web
```

然后在浏览器打开：

```text
http://127.0.0.1:3080
```

## 如果 3080 端口被占用

查看占用端口的进程：

```bash
powershell.exe -Command "Get-NetTCPConnection -LocalPort 3080 -ErrorAction SilentlyContinue | Select-Object OwningProcess"
```

结束对应进程（替换 `<PID>`）：

```bash
powershell.exe -Command "Stop-Process -Id <PID> -Force"
```

然后再运行 `pnpm dsh --profile web`。

## 什么时候需要重新构建

以下情况才需要再次执行 `pnpm run build`：

- 拉取了新的代码变更
- 修改了 TypeScript 源码
- 清理过 `lib/` 或 `node_modules/`

单纯重启电脑、结束进程后不需要重新构建，直接启动即可。
