---
name: test_playwright_report
description: |
  使用 MCP Playwright Server 交互式测试 Web 页面功能，并自动生成 xlsx 格式的测试报告。
  报告包含：测试功能、预期效果、实际效果、系统截图、测试结果（通过/不通过）、问题描述。
  当用户提到"测试并生成报告"、"测试用例报告"、"生成测试xlsx"、"边测试边记录"、
  "测试报告"、"功能验收报告"、"UAT测试"、"验收测试"等涉及 Web 页面测试 + 生成 Excel 报告的场景时触发。
  即使用户只是说"帮我测试一下xx功能并出报告"也应该触发此技能。
---

# Playwright 交互式测试 + XLSX 报告生成

这个技能的核心工作流：用 MCP Playwright Server 逐步测试 Web 页面功能，每完成一个测试步骤就记录结果，最后调用 `scripts/generate_report.py` 生成带截图的 xlsx 测试报告。

## 工作流程

### 第1步：确认测试信息

从用户消息中提取以下信息：
- 测试目标 URL（如 `http://10.0.23.146:8111/`）
- 登录账号密码（如果需要登录）
- 要测试的功能模块名称
- 报告输出路径（默认 `~/Downloads/测试报告_{模块名}_{日期}.xlsx`）

如果用户没有明确指定，从对话上下文推断；推断不出则询问。

### 第2步：使用 MCP Playwright 逐步测试

使用 `executeautomation-playwright-server` MCP 工具进行测试：

1. `playwright_navigate` — 打开目标 URL
2. `playwright_fill` + `playwright_click` — 登录（如需要）
3. 逐步导航到目标功能页面
4. 对每个测试点：
   - `playwright_screenshot` — 截图保存（设置 `savePng: true`）
   - `playwright_get_visible_html` / `playwright_get_visible_text` — 获取页面内容验证
   - `playwright_evaluate` — 执行 JS 检查 DOM 状态
   - `playwright_console_logs` — 检查控制台错误

### 第3步：记录测试用例

每完成一个测试点，在内存中记录一条测试用例，格式如下：

```json
{
  "test_id": 1,
  "module_name": "ES内存SN清单及与溯源匹配查询",
  "test_item": "菜单导航",
  "test_description": "从侧边栏进入信创溯源系统 → 最终鉴权查询 → ES内存SN清单",
  "expected_result": "成功打开ES内存SN列表页面，面包屑显示正确标题",
  "actual_result": "页面正常加载，面包屑显示'ES内存SN清单及与溯源匹配查询'",
  "screenshot_path": "C:/Users/15458/Downloads/es_memory_sn_page.png",
  "passed": true,
  "issue": ""
}
```

对于不通过的用例：
```json
{
  "test_id": 2,
  "module_name": "ES内存SN清单及与溯源匹配查询",
  "test_item": "搜索功能",
  "test_description": "在搜索栏输入项目编号进行搜索",
  "expected_result": "列表按项目编号过滤显示匹配记录",
  "actual_result": "搜索后页面报错，显示500错误",
  "screenshot_path": "C:/Users/15458/Downloads/search_error.png",
  "passed": false,
  "issue": "搜索接口返回500，可能是后端字段映射问题"
}
```

### 第4步：生成 XLSX 报告

所有测试完成后，将测试用例数据写入 JSON 文件，然后调用脚本生成报告：

```bash
python <skill_path>/scripts/generate_report.py --data <test_data.json> --output <报告路径.xlsx>
```

其中：
- `<skill_path>` 是此技能所在目录
- `<test_data.json>` 是测试用例 JSON 文件路径
- `<报告路径.xlsx>` 是输出的 xlsx 文件路径
- cwd 设为 `xinchuang-materiel`

### 第5步：报告结果

告诉用户报告已生成，包含：
- 测试用例总数
- 通过数 / 不通过数
- 报告文件路径

## 测试要点清单（Odoo 页面通用）

对于 Odoo 模块的页面测试，通常包含以下测试点：

1. 菜单导航 — 能否从菜单正确进入目标页面
2. 列表视图渲染 — tree 视图是否正常显示列头和数据（或空数据占位符）
3. 搜索功能 — 搜索栏各字段是否可用
4. 筛选器 — 预定义的 filter 是否正常工作
5. 分组功能 — 预定义的 group_by 是否正常
6. 表单视图 — 点击记录能否打开 form 视图（如果有数据）
7. 控制台错误 — 页面是否有 JS 报错
8. 权限检查 — 页面是否受权限控制

根据具体功能模块灵活增减测试点。

## 截图命名规范

截图文件名格式：`{模块名}_{测试项}_{时间戳}.png`

使用 `playwright_screenshot` 时设置：
- `name`: 描述性名称
- `savePng`: true
- `downloadsDir`: 用户指定的目录或默认 Downloads

## 注意事项

- 截图必须设置 `savePng: true` 才能保存为 PNG 文件供 xlsx 嵌入
- 测试过程中如果遇到页面加载慢，适当增加等待时间
- 每个测试步骤都要截图，即使是通过的用例也要截图作为证据
- 报告中的截图会自动调整大小嵌入到对应行的单元格中
