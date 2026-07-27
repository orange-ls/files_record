---
name: ops_deploy_to_test
description: |
  将 Odoo 模块远程部署到 Linux 测试机。通过 SSH 上传本地 xc_addons 下的模块文件到远程服务器，并重启 Odoo 服务。当用户提到"部署"、"部署模块"、"部署 xc_sn"、"上传到测试机"、"发到服务器"、"更新测试环境"、"同步到远程"、"推到测试机"等任何涉及将本地代码推送到远程测试服务器的场景时，都应该使用此技能。即使用户只是简单说"部署一下"而没有指定模块名，也应该触发此技能。
---

# 远程部署 Odoo 模块到测试机

这个技能的核心工作是：把本地开发好的 Odoo 模块通过 SSH 上传到远程 Linux 测试机，然后重启 Odoo 服务让改动生效。整个过程由 `scripts/deploy_module.py` 脚本完成，你只需要提取模块名并执行它。

## 远程测试机信息

| 项目 | 值 |
|------|-----|
| IP | 10.0.23.146 |
| 用户 | root |
| 服务名 | xc-test.service |
| 远程模块路径 | /opt/xc-test/xc-odoo-test/xc_addons/ |
| 本地模块路径 | {project_root}/xc_addons/ |

## 执行步骤

### 1. 提取模块名

从用户消息中提取要部署的模块名。常见模块包括：`xc_sn`、`xc_common`、`xc_material_manage`、`xc_order` 等。

如果用户没有明确指定模块名：
- 从当前对话上下文中查找最近修改过的模块
- 从用户打开的编辑器文件路径中提取（如 `xc_addons/xc_sn/...` → `xc_sn`）
- 如果无法推断，询问用户

### 2. 执行部署脚本

找到此技能的脚本路径，然后用 `executePwsh` 执行：

```bash
python <skill_path>/scripts/deploy_module.py --project-root <project_root> <module_name>
```

其中：
- `<skill_path>` 是此技能所在目录（即 `.kiro/skills/ops_deploy_to_test`）
- `<project_root>` 是项目根目录（`xinchuang-materiel` 的绝对路径）
- `<module_name>` 是模块名，多个用逗号分隔
- cwd 设为 `xinchuang-materiel`

**Example 1: 部署单个模块**
用户说: "部署 xc_dboms"
执行: `python .kiro/skills/ops_deploy_to_test/scripts/deploy_module.py --project-root . xc_dboms`
（cwd 为 xinchuang-materiel）

**Example 2: 部署多个模块**
用户说: "把 xc_sn 和 xc_common 部署到测试机"
执行: `python .kiro/skills/ops_deploy_to_test/scripts/deploy_module.py --project-root . xc_dboms,xc_common`

**Example 3: 只上传不重启**
用户说: "先把 xc_sn 传上去，不用重启"
执行: `python .kiro/skills/ops_deploy_to_test/scripts/deploy_module.py --project-root . xc_dboms --no-restart`

### 3. 报告结果

脚本会输出详细的部署过程日志，包括上传文件数、耗时、服务重启状态。将关键信息汇报给用户。

## 脚本做了什么

`scripts/deploy_module.py` 使用 paramiko 库通过 SSH 连接远程服务器，执行以下操作：

1. 连接到 10.0.23.146
2. 递归删除远程旧模块目录（确保干净部署）
3. 递归上传本地模块文件（排除 `__pycache__`、`.git`、`.kiro`、`.pyc` 等）
4. 执行 `systemctl restart xc-test.service` 重启服务

部署前不需要 git commit，脚本直接上传本地工作目录的文件。
