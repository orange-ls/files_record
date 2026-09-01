# 重新安装 DSH（DeepSeek Harness）—— 完整清理与重装指南

一套**完全彻底的重装流程**，并增加了 `pnpm clean` 步骤以确保构建前清理干净。

---

## 📋 前提条件
- 确认你已安装 **Node.js**（建议 v18+）和 **pnpm**（建议 v8+）。
- 确保网络可以访问 GitHub 和 npm registry（可配置镜像源）。

---

## 🧹 第一步：彻底删除所有 DSH 相关文件

### 1.1 退出当前目录
如果你当前正处在 `deepseek-harness` 源码目录内，请先退出，否则 Windows 会锁定该目录导致删除失败。
```bash
cd /d/Workspace   # 或 cd ~
```

### 1.2 删除源码目录
```bash
rm -rf /d/Workspace/deepseek-harness
```
> 若提示 `Device or resource busy`，请关闭所有占用该目录的程序（终端、VS Code、Node 进程等），或重启电脑后再试。

### 1.3 删除用户配置目录（~/.dsh）
这会清除所有 profile、已安装的插件和缓存。
```bash
rm -rf ~/.dsh
```
（Windows 下对应 `C:\Users\你的用户名\.dsh`）

### 1.4 卸载全局安装的 DSH（如果有）
检查是否全局安装过：
```bash
npm list -g --depth=0 | grep @deepseek-ai/dsh
```
如果存在，执行卸载：
```bash
npm uninstall -g @deepseek-ai/dsh
```
若使用 `pnpm` 全局安装：
```bash
pnpm uninstall -g @deepseek-ai/dsh
```

### 1.5（可选）清理 npm 缓存
```bash
npm cache clean --force
```

---

## 🔄 第二步：重新获取源码并安装依赖

### 2.1 克隆最新源码
```bash
cd /d/Workspace
git clone https://github.com/deepseek-ai/deepseek-harness.git
cd deepseek-harness
```

### 2.2 安装项目依赖
项目使用 `pnpm` 作为包管理器，执行：
```bash
pnpm install
```
- 如果下载速度慢，可配置 `pnpm` 镜像源（见附录）。
- 该步骤会下载大量依赖，请耐心等待（约 2-5 分钟，视网络而定）。

### 2.3 清理之前的构建产物（确保干净构建）
```bash
pnpm clean
```
- 此命令会删除所有子包中的 `dist`、`build` 等输出目录，避免残留文件影响新的构建。
- 如果项目中没有定义 `clean` 脚本，可以手动删除各包的 `dist` 目录，但通常官方脚手架已包含该命令。

### 2.4 构建所有包
```bash
pnpm -r run build
```
- 这会编译所有子包（包括 web 前端）。
- 若构建过程中出现 `apps/web` 失败（如之前遇到的 worker 依赖缺失），可尝试更新源码或查看 GitHub Issues，也可先构建核心包再单独构建 web（后续步骤会说明）。

---

## 🚀 第三步：启动 DSH

### 3.1 启动 Web 服务
在项目根目录执行：
```bash
pnpm run start:web
```
或根据 `package.json` 中定义的脚本，可能是：
```bash
pnpm web
```
DSH 的 Web 界面通常会在 `http://localhost:3000` 打开。

### 3.2 验证启动是否成功
- 浏览器能正常打开界面，且没有插件加载错误。
- 终端日志中无 `dsh-plugin-market` 相关报错。

---

## 🔧 备选方案：如果源码构建仍然失败

如果你不希望折腾复杂的构建过程，可以**直接使用全局安装的预构建版本**（无需源码）：

```bash
npm install -g @deepseek-ai/dsh
dsh web
```
这会直接运行官方发布的稳定版，省去编译时间。

---

## 📌 附录：常见问题与解决

### A. 删除目录时提示“Device or resource busy”
- 关闭所有使用该目录的程序（终端、编辑器、Node 进程）。
- 在任务管理器中结束 `node.exe` 进程（注意备份其他服务）。
- 如果仍不行，重启电脑后直接手动删除文件夹。

### B. pnpm 安装依赖慢
设置镜像源（以淘宝镜像为例）：
```bash
pnpm config set registry https://registry.npmmirror.com
```

### C. 构建时遇到 `apps/web` 报错
- 尝试只构建核心包：`pnpm -r --filter=!apps/web run build`，然后单独构建 web：`pnpm --filter=apps/web build`。
- 检查 Node 版本是否满足要求（建议 v18+）。
- 搜索 GitHub Issues 中类似报错，或等待官方修复。

### D. `dsh` 命令找不到（即使全局安装后）
将 npm 全局安装路径添加到系统 PATH：
- 执行 `npm config get prefix`，复制路径。
- 在 Windows 环境变量中，将路径添加到 `Path`，重启终端。

---

## ✅ 完成

至此，你已拥有一个干净、无插件残留的 DSH 环境。如果仍有问题，请提供具体的错误日志，以便进一步排查。





---

附：

问题一：

```


apps/web build: Failed
D:\project\aibms-dsh\apps\web:
[ERR_PNPM_RECURSIVE_RUN_FIRST_FAIL] @deepseek-ai/dsh-web-frontend@0.1.2-alpha.3 build: `vite build`
Exit status 1
```

