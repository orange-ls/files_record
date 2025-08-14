在 Bash 中使用 Git 命令非常方便，以下是一些常用的 Git 操作及其对应的命令：

### 1. **初始化仓库**
```bash
git init
```

### 2. **克隆远程仓库**
```bash
git clone <远程仓库URL>
```
例如：
```bash
git clone https://github.com/username/repository.git
```

### 3. **查看当前状态**
```bash
git status
```

### 4. **添加文件到暂存区**
- 添加单个文件：
  ```bash
  git add <文件名>
  ```
- 添加所有更改的文件：
  ```bash
  git add .
  ```

### 5. **提交更改**
```bash
git commit -m "提交信息"
```
例如：
```bash
git commit -m "修复了某个bug"
```

### 6. **拉取远程仓库的更新**
```bash
git pull
```
如果当前分支有设置上游分支，可以直接使用 `git pull`，否则需要指定远程和分支：
```bash
git pull origin <分支名>
```

### 7. **推送更改到远程仓库**
```bash
git push
```
如果当前分支有设置上游分支，可以直接使用 `git push`，否则需要指定远程和分支：
```bash
git push origin <分支名>
```

### 8. **查看提交历史**
```bash
git log
```

### 9. **创建分支**
```bash
git branch <分支名>
```

### 10. **切换分支**
```bash
git checkout <分支名>
```
或者创建并切换到新分支：
```bash
git checkout -b <新分支名>
```

### 11. **合并分支**
```bash
git merge <分支名>
```

### 12. **删除分支**
- 删除本地分支：
  ```bash
  git branch -d <分支名>
  ```
- 强制删除本地分支（如果分支未合并）：
  ```bash
  git branch -D <分支名>
  ```
- 删除远程分支：
  ```bash
  git push origin --delete <分支名>
  ```

### 13. **撤销更改**
- 撤销工作区的修改（未 `git add`）：
  ```bash
  git checkout -- <文件名>
  ```
- 撤销暂存区的修改（已 `git add` 但未 `git commit`）：
  ```bash
  git reset HEAD <文件名>
  ```
- 撤销提交（已 `git commit`）：
  ```bash
  git reset --soft HEAD^  # 撤销提交但保留更改
  git reset --hard HEAD^  # 彻底撤销提交和更改
  ```

### 14. **查看远程仓库**
```bash
git remote -v
```

### 15. **添加远程仓库**
```bash
git remote add <远程名称> <远程仓库URL>
```
例如：
```bash
git remote add origin https://github.com/username/repository.git
```

### 16. **从远程仓库获取更新（不自动合并）**
```bash
git fetch
```

### 示例工作流程
```bash
# 克隆仓库
git clone https://github.com/username/repository.git
cd repository

# 创建并切换到新分支
git checkout -b feature-branch

# 修改文件后添加并提交
git add .
git commit -m "添加了新功能"

# 推送到远程仓库
git push origin feature-branch

# 拉取最新更改
git pull origin main

# 合并分支
git checkout main
git merge feature-branch
git push origin main
```

这些是 Git 在 Bash 中最常用的命令，熟练掌握后可以高效地进行版本控制。