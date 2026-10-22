---
name: xc_spare_parts_employee
description: >
  备件测算系统（xc_spare_parts）统一数据助手。整合 py 脚本（fetcher）和 MCP SQL 两种查询方式，
  py 脚本优先执行，MCP SQL 作为兜底。覆盖查询、刷新、导出、脚本逻辑修改的完整闭环。

  当用户提到以下任何场景时，立即使用本 skill：
  - 查询备件测算相关数据（BOM总表、备料总表、各库区库存、采购在途、转储在途、RMA在途、不良率、鲲鹏日报等）
  - 查询某个物料的库存、缺口、备货量、不良率
  - 需要刷新/更新备件测算数据
  - 导出备件数据为 Excel
  - 对备件数据做分析（超出预定义查询范围时用 MCP SQL）
  - 修改某个 fetcher 脚本的字段取值逻辑
  - 提到"备料"、"备件"、"BOM"、"库区库存"、"在途"、"不良率"、"鲲鹏日报"、"派件补库"等关键词
---

# 备件测算系统统一数据助手

## 核心原则

```
用户请求
  ↓
判断请求类型：
  ├── 查询/刷新/导出 → 匹配表名 → 有 fetcher？
  │     ├── 是 → 执行 fetcher 脚本的 query() / refresh()
  │     └── 否 → 走 MCP SQL 查询
  ├── 数据分析（不在预定义范围内）→ MCP SQL 自由查询
  └── 修改脚本逻辑 → 直接修改对应 fetcher py 文件
```

---

## 一、表名映射与执行方式

| 用户说的名称 | 数据库表名 | 执行方式 | fetcher 文件 |
|---|---|---|---|
| BOM总表 | bom_total_table | fetcher | fetchers/bom_total_table.py |
| 鲲鹏日报、BI库存 | kunpeng_daily | fetcher | fetchers/kunpeng_daily.py |
| 各库区库存、WMS库存 | reservoir_area_stock | fetcher | fetchers/reservoir_area_stock.py |
| 其他库区库存 | other_reservoir_area_stock | fetcher | fetchers/other_reservoir_area_stock.py |
| 汇总看板 | summary_kanban | fetcher | fetchers/summary_kanban.py |
| 欠料调拨总表 | material_shortage | fetcher | fetchers/material_shortage.py |
| 生产系统PO单 | production_stock | fetcher | fetchers/production_stock.py |
| 工厂物料清单 | factory_material_list | fetcher | fetchers/factory_material_list.py |
| 备料总表 | prepare_materials | fetcher(query仅) | fetchers/prepare_materials.py |
| 替代料备料总表 | alternative_prepare_materials | fetcher(query仅) | fetchers/alternative_prepare_materials.py |
| 生产批次明细 | production_batch_detail | MCP SQL | — |
| 本周项目测算 | week_estimates | MCP SQL | — |
| 400派件补库单 | material_stock_order | MCP SQL | — |
| 网络产品测算 | network_spare_trs | MCP SQL | — |
| 物料基础数据 | base_material | MCP SQL | — |
| 捆绑料号 | bundling_part_number | MCP SQL | — |
| 采购在途 | purchasing_transit | MCP SQL | — |
| 转储在途 | dump_transit | MCP SQL | — |
| RMA在途 | rma_transit | MCP SQL | — |
| 不良率 | reject_ratio | MCP SQL | — |
| 物料BOM | material_bom | MCP SQL | — |
| 计算产品备货申请 | compute_proj_apply | MCP SQL | — |
| SAP库存查询 | inventory_query | MCP SQL | — |
| 非电子物料 | non_electronic_materials | MCP SQL | — |
| 物料转换 | material_transformation | MCP SQL | — |
| PO单与存量 | purchase_order_inventory | MCP SQL | — |
| 溯源PO单 | purchase_order_inventory_new | MCP SQL | — |
| 库区分配表 | warehouse_allocation | MCP SQL | — |
| WMS库房分配表 | wms_storeroom_table | MCP SQL | — |
| 本地库存查询 | replenishment_order | MCP SQL | — |
| 现场备件项目对应表 | scene_project_table | MCP SQL | — |
| CRM市级ID | crm_city_id | MCP SQL | — |
| crm数据表 | crm_table | MCP SQL | — |
| 延保项目BOM总表 | extend_warranty_bom_table | MCP SQL | — |
| 备件&ASP上门成本 | spare_parts_labor_cost | MCP SQL | — |
| 版本管控&定制化 | version_ctrl_customization | MCP SQL | — |

用户说的名称不在上表中时，先问用户确认要查哪个表。

---

## 二、fetcher 执行（py 脚本优先）

当表有对应的 fetcher 时，通过 Python 脚本执行。

### 调用方式

直接用 `python -c` 内联执行，禁止创建临时 py 文件：

```bash
# 查询（Windows bash 环境，用双引号包裹，内部用单引号）
python -c "import sys,os,json; sys.path.insert(0,os.path.join('.kiro','skills','xc_spare_parts_employee')); from fetchers._base import get_connection; from fetchers import bom_total_table; conn=get_connection(); r=bom_total_table.query(conn,limit=10,offset=0); conn.close(); print(json.dumps({'total':r['total'],'records':r['records'],'fields':r['fields'],'field_labels':r['field_labels']},ensure_ascii=False,default=str))"

# 带筛选条件
python -c "import sys,os,json; sys.path.insert(0,os.path.join('.kiro','skills','xc_spare_parts_employee')); from fetchers._base import get_connection; from fetchers import bom_total_table; conn=get_connection(); r=bom_total_table.query(conn,limit=10,offset=0,filters={'material_code':'302-123456'}); conn.close(); print(json.dumps({'total':r['total'],'records':r['records'],'fields':r['fields'],'field_labels':r['field_labels']},ensure_ascii=False,default=str))"

# 刷新
python -c "import sys,os,json; sys.path.insert(0,os.path.join('.kiro','skills','xc_spare_parts_employee')); from fetchers._base import get_connection; from fetchers import bom_total_table; conn=get_connection(); r=bom_total_table.refresh(conn,on_progress=lambda s,t,m:print(f'[{s}/{t}] {m}')); conn.close(); print(json.dumps(r,ensure_ascii=False,default=str))"
```

关键规则：
- **禁止**创建临时 py 文件再删除，直接 `python -c` 内联执行
- **禁止**使用 `&&` 连接命令，Windows PowerShell/bash 环境必须用 `;` 分隔多条命令
- 输出统一用 `json.dumps` 格式，由 agent 解析后自行构建 Markdown 表格
- 替换 `bom_total_table` 为目标 fetcher 模块名即可（如 `prepare_materials`、`alternative_prepare_materials`）
- `limit` 和 `offset` 按分页规则传入

### 返回格式

query() 返回：
```python
{
    'total': 5000,
    'records': [{'字段名': '值', ...}, ...],
    'fields': ['字段名1', '字段名2', ...],
    'field_labels': {'字段名': '中文名', ...},
    'markdown': '...',  # 直接输出给用户的 Markdown 表格
}
```

refresh() 返回：
```python
{'success': True, 'count': 1234, 'message': '刷新成功，共写入 1234 条'}
```

### 刷新依赖链

```
【主数据链 - 刷新BOM总表时按此顺序】
bom_total_table.refresh()
    ├── crm_table（同步）
    ├── reservoir_area_stock.refresh()   ← 同时写入 rma_transit
    ├── other_reservoir_area_stock.refresh()
    └── kunpeng_daily.refresh()

【独立刷新（无顺序依赖）】
production_stock.refresh()
material_shortage.refresh()
summary_kanban.refresh()
material_stock_order.refresh()
factory_material_list.refresh()
```

---

## 三、MCP SQL 兜底

两种场景走 MCP SQL：
1. 表没有 fetcher（上方映射表中标记为"MCP SQL"的表）
2. 用户的分析需求超出 fetcher 预定义的查询范围（如跨表关联分析、自定义聚合统计等）

使用 `mcp` 工具执行 SQL。

### MCP 查询约束

生成 SQL 前必须参考以下文件：

| 文件 | 内容 | 何时查阅 |
|---|---|---|
| #[[file:skills/xc_spare_parts_employee/references/database-schema.md]] | 表结构、字段定义、表间关系 | 生成 SQL 前必读 |
| #[[file:skills/xc_spare_parts_employee/references/sql-generation-rules.md]] | SQL 生成规则 | 生成 SQL 时按规则执行 |
| #[[file:skills/xc_spare_parts_employee/references/business-formulas.md]] | 业务计算公式 | 涉及计算型查询时必读 |
| #[[file:skills/xc_spare_parts_employee/references/refresh-methods.md]] | 刷新逻辑和数据来源 | 判断数据时效性时参考 |

### MCP 查询的字段顺序

MCP SQL 查询时，SELECT 的字段和顺序见 #[[file:skills/xc_spare_parts_employee/references/mcp-query-fields.md]]，严格按定义执行，不要自己选字段、不要改顺序。

### 回复中的 SQL 说明规范（重要）

在回复中向用户解释查询逻辑时，**禁止**贴出完整 SQL 语句。应使用概括性说明：
- 说明查询了哪些表（如"从 bom_total_table 关联 base_material"）
- 说明使用了什么方法（如"通过 LEFT JOIN 关联捆绑料号"、"用 SUM 聚合各城市库存"）
- 说明过滤条件（如"按物料代码 302-xxx 筛选"）
- 说明排序方式（如"按物料代码和城市排序"）

错误示例：❌ 贴出 50 行完整 SQL
正确示例：✅ "从备料总表查询物料 302-123456，关联 reservoir_area_stock 获取各城市库存，按城市排序"


## 四、结果展示规则

无论用 fetcher 还是 MCP，查询后都必须在回复正文中以分页方式展示 Markdown 表格。

### 分页展示格式

每页固定显示 10 条数据，格式如下：

```
**<表中文名>**（第 1 页，共 N 页）

| 列1 | 列2 | ... |
|-----|-----|-----|
| ... | ... | ... |
（共 10 条 / 总计 XXX 条）

输入"下一页"或"第N页"查看更多数据，输入"导出"生成 Excel 文件。
```

### 分页规则

- 每页 10 条，首次查询展示第 1 页
- 总页数 = ceil(总记录数 / 10)
- 用户说"下一页" → 展示当前页 +1
- 用户说"第N页" → 展示第 N 页
- 用户说"上一页" → 展示当前页 -1
- fetcher 查询时通过 `limit=10, offset=(页码-1)*10` 实现分页
- MCP SQL 查询时通过 `LIMIT 10 OFFSET (页码-1)*10` 实现分页，同时用 `COUNT(*)` 获取总数
- 不能只说"查询完成"而不展示数据
- MCP 返回的 JSON 需转为 Markdown 表格并附加分页提示

### 展示数据的构建规则（重要）

- **禁止**直接复制终端输出的 `result['markdown']` 或原始终端文本到回复中，因为列数多时终端会换行导致格式错乱、数据丢失
- **必须**从 `result['records']`、`result['fields']`、`result['field_labels']` 三个字段自行构建 Markdown 表格：
  1. 用 `result['field_labels']` 按 `result['fields']` 顺序生成表头行
  2. 遍历 `result['records']`，按 `result['fields']` 顺序逐字段取值，空值显示为空字符串
  3. 每个单元格值转为字符串，超过 30 字符截断并加 `…`
- 脚本中只需 `print(json.dumps(result, ensure_ascii=False, default=str))` 输出 JSON，由 agent 自行解析并构建表格
- 同样适用于 MCP SQL 查询结果

---

## 五、导出 Excel

当用户说"导出"时，使用通用导出工具 `fetchers/_export.py` 生成 Excel 文件。

### 导出流程

1. 从 #[[file:skills/xc_spare_parts_employee/references/mcp-query-fields.md]] 找到对应表的字段列表和中文表头
2. 直接用 `python -c` 内联脚本，通过 psycopg2 连接数据库查询全部数据（不加 LIMIT，用户指定筛选条件时加 WHERE），然后将查询结果直接喂给 `export_to_excel()` 生成 .xlsx，一步完成查询+导出
3. 告知用户文件完整路径和记录数

### 关键原则

- **禁止**先用 MCP SQL 查全量数据再用 psycopg2 重复查询，避免同一份数据查两遍
- 有 fetcher 的表：用 fetcher 的 `query(conn, limit=999999, offset=0)` 获取数据，直接喂给导出函数
- 无 fetcher 的表（MCP SQL 类型）：在 `python -c` 脚本中用 psycopg2 构建 SQL 查询，拿到结果后直接喂给导出函数
- 整个导出过程在一个 `python -c` 脚本中完成：连接数据库 → 查询 → 导出 → 关闭连接

### 调用方式

```python
from fetchers._export import export_to_excel

# 方式一：有 fetcher 的表，配合 fetcher query() 使用
result = bom_total_table.query(conn, limit=999999, offset=0, filters=filters)
path = export_to_excel(
    records=result['records'],
    fields=result['fields'],
    field_labels=result['field_labels'],
    sheet_title='BOM总表',
)

# 方式二：无 fetcher 的表，用 psycopg2 直接查询后导出（禁止先用 MCP 查再用 psycopg2 重复查）
conn = get_connection()
with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
    cur.execute('SELECT field1, field2, ... FROM table_name ORDER BY ...')
    records = [dict(r) for r in cur.fetchall()]
conn.close()
path = export_to_excel(
    records=records,
    fields=['field1', 'field2', ...],  # 从 mcp-query-fields.md 获取
    field_labels={'field1': '中文名1', ...},
    sheet_title='表中文名',
)
```

### 导出样式

统一使用黄色表头 + 微软雅黑加粗，数据行白底 + 宋体，首行冻结，自动列宽。

---


## 六、数据视图切换（信息来源过滤）

系统页面上有一个切换按钮，控制数据的信息来源过滤范围：

| 按钮状态 | 含义 | information_sources 值 | 数据范围 |
|---|---|---|---|
| PO与存量（开） | 查看全部数据 | `''`（空字符串，不过滤） | 存量表 + 过保 + 其他所有来源 |
| 存量表（关） | 只看存量表数据 | `'存量表'` | 仅存量表 |

### 默认行为

用户没有指定时，默认使用"PO与存量"（即 `information_sources=''`，不过滤）。

### 影响的表

以下表的查询受此开关影响：

| 表名 | fetcher 参数 | MCP SQL 条件 |
|---|---|---|
| BOM总表 | query() 的 filters 中加 information_sources | WHERE information_sources = '存量表' |
| 备料总表 | query() 的 information_sources 参数 | 内嵌在 SQL 构建函数中 |
| 替代料备料总表 | query() 的 information_sources 参数 | 内嵌在 SQL 构建函数中 |
| 汇总看板 | query() 的 filters 中加 information_sources | WHERE information_sources = '存量表' |
| 欠料调拨总表 | query() 的 filters 中加 information_sources | WHERE information_sources = '存量表' |
| 本周项目测算 | MCP SQL 中加 WHERE 条件 | WHERE information_sources = '存量表' |

### 用户表达识别

| 用户说 | 对应操作 |
|---|---|
| "查存量表的xxx" / "只看存量表" | information_sources = '存量表' |
| "查全部" / "查PO与存量" / 未指定 | information_sources = ''（默认） |

---

## 七、业务术语

| 术语 | 说明 |
|---|---|
| 捆绑料号 | 多个物料代码映射到同一个捆绑料号 |
| BOM展开 | 将整机物料递归拆解为最小可替换备件 |
| 不良率 | 物料的理论故障率，用于计算备货量 |
| 备货量 | 基于销量×不良率的分段公式计算 |
| 缺口 | 库存量 - 备货量，负数表示不足 |
| 库存预警 | 充足/补货/急需补货/无库存 |
| 信息来源 | 只有"存量表"和"过保"两种 |

---

## 八、数据分析知识库

当用户提出分析类问题（如"哪些物料缺口最大"、"各城市库存分布"、"不良率趋势"等）时，按以下流程处理：

### 知识库结构

```
knowledge/
├── index.md              # 索引文件：关键词 → 主题文件映射（必须先读）
├── stock-analysis.md     # 库存类：缺口、预警、库存分布、各库区对比
├── material-analysis.md  # 物料类：不良率、BOM、捆绑料号、备货量
├── transit-analysis.md   # 在途类：采购/转储/RMA在途
├── project-analysis.md   # 项目类：项目维度备货、销量、城市分布
└── report-analysis.md    # 报表类：汇总统计、趋势对比、Top N 排名
```

### 执行流程

1. 先读取索引文件 #[[file:skills/xc_spare_parts_employee/knowledge/index.md]]，根据用户问题中的关键词定位到具体主题文件
2. 读取匹配的主题文件，查找是否有类似的分析条目
3. **有匹配**：按知识库中记录的分析方式执行，如用户无异议则直接复用
4. **无匹配**：按自己的理解进行分析，分析完成后将问题和分析方式记录到对应主题文件，并更新 index.md 的关键词索引

### 知识库更新规则

| 场景 | 操作 |
|---|---|
| 知识库中无类似问题 | 分析完成后，追加新条目到对应主题文件，同时更新 index.md 关键词索引 |
| 用户对分析结果不满意并提出改正方案 | 按用户方案重新分析，更新对应主题文件中的条目 |
| 用户确认分析结果正确 | 无需操作 |

### 知识库条目格式

每条记录使用二级标题，包含以下内容。**`<问题简述>` 必须是概括性的短语**，不要写具体的物料代码、城市名等细节，要抽象为通用场景描述。

```markdown
## <问题简述>（概括性短语，如"物料缺口 Top N 排名"而非"查302-123456在武汉的缺口"）
- tags: 关键词1, 关键词2, 关键词3
- 问题：<通用化的分析需求描述，不含具体物料/城市等参数>
- 数据来源：<用了哪个表/fetcher，单表还是多表关联>
- 计算方式：<聚合方式（SUM/AVG/COUNT）、分组维度（按城市/按物料/按时间）、排序方式>
- 过滤条件：<特殊的 WHERE 条件类型，如"负缺口过滤"、"按备件大类筛选">
- 呈现方式：<排名列表 / 对比表格 / 汇总数字>
- 备注：<注意事项、业务背景等>
```

正确示例：
```markdown
## 各城市库存缺口排名
- tags: 缺口, 城市, 排名, 库存不足
- 问题：查看哪些城市的库存缺口最严重
- 数据来源：prepare_materials fetcher，关联 reservoir_area_stock
- 计算方式：按城市 GROUP BY，SUM(gap_quantity) 取负值，降序排列取 Top N
- 过滤条件：gap_quantity < 0（只看缺货的）
- 呈现方式：排名列表
- 备注：缺口=库存量-备货量，负数表示不足
```

错误示例：
```markdown
## 查302-123456在武汉的缺口   ← ❌ 太具体，不可复用
## SELECT material_code, gap_quantity FROM ...  ← ❌ 不要贴 SQL
```

### 注意事项

- 查询时只需先读 index.md（很小），精准定位到目标主题文件，不要把所有文件都读一遍
- 记录要简略，重点是分析思路，不要贴完整 SQL
- 同一类问题只保留一条记录，避免重复
- 新增条目时必须同步更新 index.md 的关键词索引表


## 九、修改 fetcher 脚本逻辑

当用户要求修改某个表的查询或刷新逻辑时（如"把字段 a 的来源从 B 表改为 C 表"），直接修改对应的 fetcher py 文件。

### 执行步骤

1. 确认用户要修改哪个表 → 找到对应的 `fetchers/<表名>.py`
2. 读取该 fetcher 文件，定位到需要修改的字段逻辑
3. 按用户要求修改取值逻辑（可能涉及 `refresh()` 中的 SQL 查询、字段赋值、`TREE_FIELDS`、`FIELD_LABELS`）
4. 保存文件，告知用户变更内容

### 修改时的代码规范

- 共享常量从 `_constants.py` 导入（`CITY_FIELDS`、`STOCK_ADDRESSES`、`ALERT_MAP`、`get_service_level`），禁止在 fetcher 中重复定义
- 批量写入用 `psycopg2.extras.execute_values`，禁止循环内逐条 INSERT
- SQL 过滤条件用 `%s` 占位符，禁止 f-string 拼接用户输入
- `import` 语句放文件顶部，禁止函数内局部导入
- 空值直接用 `None`，禁止 `AsIs('NULL')`
- 修改后的代码必须保留原有的文件头注释、未变化字段的逻辑、`query()` 的过滤字段列表

### 常见修改场景

| 用户说 | 操作 |
|---|---|
| "字段 a 改为从 C 表取" | 修改 `refresh()` 中该字段的 SELECT 和赋值逻辑 |
| "新增一个字段 x" | 在 `TREE_FIELDS`、`FIELD_LABELS`、`refresh()` 插入逻辑、`query()` SELECT 中新增 |
| "删除字段 y" | 从 `TREE_FIELDS`、`FIELD_LABELS`、`refresh()` 中移除 |
| "查询时增加按 z 字段过滤" | 在 `query()` 的 `allowed` 集合中新增该字段 |
| "刷新逻辑加一步 xxx" | 在 `refresh()` 中新增对应步骤，调整 `TOTAL_STEPS` |



## 十、执行流程总结


1. 用户提出需求
2. 判断请求类型：
   ├── 查询/刷新/导出 → 匹配表名
   │     ├── 有 fetcher → 执行 py 脚本，展示结果
   │     └── 无 fetcher → 读 MCP 约束文件，生成 SQL 查询
   ├── 数据分析（跨表/自定义）→ MCP SQL 自由查询
   └── 修改脚本逻辑 → 直接改 fetcher py 文件
3. 展示结果（Markdown 表格）
4. 用户说"导出" → 读 export-rules.md 生成 Excel
5. 用户说"刷新" → 执行 fetcher.refresh()（按依赖链顺序）
