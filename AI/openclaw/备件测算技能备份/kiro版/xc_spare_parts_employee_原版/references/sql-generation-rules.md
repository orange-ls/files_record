# SQL 生成规则

本文件定义了所有查询场景的 SQL 生成规则。AI 根据用户需求，按照这些规则动态生成 SQL。
规则按查询复杂度分为四个级别。

---

## 级别一：简单表查询

适用于：直接查询单张表的数据，不需要复杂计算。

### 规则 1.1：SELECT 语句

每个表的完整 SELECT 语句（含全部字段、中文别名、正确列顺序）已在 SKILL.md 的"各表标准查询 SELECT 语句"中定义。
生成 SQL 时直接复制 SKILL.md 中对应表的 SELECT 语句，追加 WHERE 和 LIMIT 即可。
不要自己选字段，不要改变列顺序，不要省略任何列。

### 规则 1.3：WHERE 条件生成

用户说"查某个物料"→ 用物料代码字段精确匹配：
```
WHERE <物料代码字段> = '用户提供的值'
```

用户说"查某类物料"→ 用分类字段匹配：
```
WHERE name = '主板'                    -- 产品Ⅱ级分类
WHERE spare_parts_category = '服务器'   -- 备件大类
```

用户说"模糊查询"或给出部分名称→ 用 LIKE：
```
WHERE material_desc LIKE '%内存%'
WHERE proj_name LIKE '%国网%'
```

### 规则 1.4：排序和分页

- 默认按主业务字段排序（物料代码 ASC 或日期 DESC）
- 大表（>1000条）必须加 LIMIT 10
- 如果用户要求"前N条"或"TOP N"，用 LIMIT N
- 如果用户要求翻页或"继续"，用 LIMIT 10 OFFSET M（M 为已展示的行数）
- 如果用户要求"导出"，不加 LIMIT，查询全部数据后生成 Excel 文件

### 规则 1.5：适用的表

以下表可以直接用简单 SELECT 查询：

| 表名 | 默认排序 | 是否需要 LIMIT |
|---|---|---|
| base_material | material_code ASC | 是(~7200条) |
| bom_total_table | write_time DESC, material_mode ASC | 是(~14.4万条) |
| bundling_part_number | bundling_number ASC | 否(~1250条) |
| purchasing_transit | material_mode ASC | 否(~80条) |
| dump_transit | sap_no ASC | 否(~190条) |
| rma_transit | material_code ASC | 否(~120条) |
| reject_ratio | sap_no ASC | 是(~1940条) |
| kunpeng_daily | material_code ASC | 是(~1.3万条) |
| material_bom | material_code ASC, assembly ASC | 是(~2270条) |
| material_stock_order | dispatch_date DESC | 是(~1.6万条) |
| compute_proj_apply | update_date DESC | 视数据量 |

### 规则 1.6：特殊字段处理

- purchasing_transit 的供应商PN码字段名是 `"supplier_PN"`（带双引号，大写PN），SKILL.md 的 SELECT 语句中已正确处理
- material_stock_order 的枚举字段 CASE WHEN 转换已在 SKILL.md 的 SELECT 语句中包含
- reject_ratio 的 theoretical_defect_rate 是 numeric(16,8)，输出时保留合理精度

---

## 级别二：各库区库存行转列查询

适用于：查询 reservoir_area_stock 表，需要将行数据转为列显示。

### 规则 2.1：行转列原理

数据库中每行存储一个物料在一个城市的库存：
```
sap_no='302-001115', city='武汉', num=52
sap_no='302-001115', city='北京', num=3
```

系统展示时转为一行多列：
```
物料代码=302-001115, 武汉=52, 北京=3, ...
```

### 规则 2.2：行转列 SQL 生成步骤

第一步：内层查询 — 按 sap_no 分组，用 CASE WHEN 将每个城市转为一列

```
SELECT
    ras.sap_no,
    MAX(COALESCE(bn.bundling_number, ras.sap_no)) AS bundling_number,
    max(ras.material_desc) as material_desc,
    max(ras.supplier_pn) as supplier_pn,
    max(ras.spare_parts_category) as spare_parts_category,
    max(ras.material_type) as material_type,
    max(ras.product_category3) as product_category3,
    -- 对每个城市生成一个 sum(case when ...) 列
    sum(case when city='<城市名>' then num else 0 end) as "<城市名>"
    -- 重复上面这行，替换为45个城市中的每一个
FROM reservoir_area_stock ras
LEFT JOIN bundling_part_number bn ON ras.sap_no = bn.material_mode
GROUP BY ras.sap_no
```

第二步：外层查询 — 添加中文别名和筛选条件

```
SELECT
    ta.sap_no as 物料代码,
    ta.bundling_number as 捆绑料号,
    ta.material_desc as 物料描述,
    ta.supplier_pn as 供应商PN码,
    ta.spare_parts_category as 备件大类,
    ta.material_type as "产品Ⅱ级分类",
    ta.product_category3 as "产品Ⅲ级分类",
    ta."武汉", ta."北京", ...  -- 城市列
FROM (<内层查询>) ta
WHERE ...  -- 筛选条件
LIMIT 50
```

### 规则 2.3：城市列的选择

- 如果用户没有指定城市，默认只显示有库存的主要城市（武汉、北京、上海、广州、成都等），
  不要一次性显示全部45个城市（表格太宽）
- 如果用户指定了城市（如"查武汉和北京的库存"），只生成指定城市的列
- 如果用户说"查所有城市"或"完整库存"，才生成全部45个城市列

### 规则 2.4：whbj 列的计算

whbj = 除武汉以外所有城市库存之和。
如果用户需要 whbj 列，在外层 SELECT 中加：
```
(ta."北京" + ta."福州" + ta."上海" + ... 所有非武汉非whbj城市) as "whbj"
```

### 规则 2.5：筛选条件

- 按物料代码：`WHERE ta.sap_no = '302-001115'`
- 按物料描述：`WHERE ta.material_desc LIKE '%内存%'`
- 按分类：`WHERE ta.material_type = '主板'`
- 按某城市有库存：`WHERE ta."武汉" > 0`

---

## 级别三：备料总表计算查询

适用于：查询备料总表数据，需要实时计算备货量、缺口、库存预警等。
这是最复杂的查询，涉及 8 张表关联和多个业务公式。

### 规则 3.1：备料总表的数据来源

备料总表不是一张真实的数据库表（表存在但数据为空），它的数据由以下步骤实时计算：

1. 从 bom_total_table 获取物料列表和使用量
2. 通过 bundling_part_number 展开捆绑料号下的所有物料
3. 关联 base_material 获取物料描述、分类
4. 关联 reject_ratio 获取不良率
5. 交叉连接城市列表，关联 bom_total_table 获取各城市销量
6. 关联 reservoir_area_stock 获取各城市库存
7. 关联 kunpeng_daily 获取 XC02/XC16/XC17 库存
8. 关联 purchasing_transit/dump_transit/rma_transit 获取在途数据
9. 用业务公式计算备货量、缺口、库存预警、各库区总缺口、最终缺口

### 规则 3.2：简化查询（推荐）

当用户查询特定物料或少量物料的备料信息时，使用简化版查询。
不需要交叉连接45个城市，直接关联需要的表即可。

生成步骤：
1. 以 base_material 为主表
2. LEFT JOIN bundling_part_number 获取捆绑料号
3. LEFT JOIN reject_ratio 获取不良率
4. LEFT JOIN (bom_total_table 按 material_mode 聚合 sum(sum_count)) 获取总使用量
5. LEFT JOIN reservoir_area_stock (city='武汉') 获取武汉库存
6. LEFT JOIN purchasing_transit 获取采购在途
7. LEFT JOIN dump_transit 获取转储在途
8. LEFT JOIN rma_transit 获取RMA在途
9. 在 SELECT 中用 CASE WHEN 计算备货量和库存预警（公式见 business-formulas.md）

### 规则 3.3：完整查询（按城市展开）

当用户需要按城市维度查看备料数据时，需要完整查询。

生成步骤：

第一步：构建物料+信息来源基础集

```
-- 从 bom_total_table 获取物料列表，通过捆绑料号展开
SELECT A.information_sources, A.material_mode, COALESCE(C.total_usage, 0) as total_usage
FROM (
    SELECT information_sources,
           CASE WHEN b2.bundling_number IS NOT NULL THEN b3.material_mode
                ELSE b1.material_mode
           END AS material_mode
    FROM bom_total_table b1
    LEFT JOIN bundling_part_number b2 ON b1.material_mode = b2.material_mode
    LEFT JOIN bundling_part_number b3 ON b2.bundling_number = b3.bundling_number
    GROUP BY b1.material_mode, b3.material_mode, b2.bundling_number, information_sources
) A
LEFT JOIN (
    SELECT information_sources, material_mode, sum(sum_count) as total_usage
    FROM bom_total_table GROUP BY material_mode, information_sources
) C ON A.information_sources = C.information_sources AND A.material_mode = C.material_mode
GROUP BY A.material_mode, C.total_usage, A.information_sources
```

第二步：关联基础数据表

在第一步结果上依次 LEFT JOIN：
- bundling_part_number（获取捆绑料号）
- base_material（获取描述、分类）
- reject_ratio（获取不良率）

第三步：交叉连接城市列表

```
LEFT JOIN (
    SELECT * FROM (VALUES
        ('whbj'),('北京'),('福州'),('上海'),... -- 除武汉外的44个城市
    ) as t(city)
) E ON 1=1
```

注意：城市列表不包含"武汉"，因为武汉的销量在系统中被映射为"武汉项目"。

第四步：关联各城市销量

```
LEFT JOIN (
    SELECT material_mode, sum(sum_count) as sales, stock_location, information_sources
    FROM (
        SELECT material_mode, sum_count,
               CASE WHEN stock_location = '武汉' THEN '武汉项目'
                    ELSE stock_location
               END AS stock_location,
               information_sources
        FROM bom_total_table
    ) T
    GROUP BY material_mode, stock_location, information_sources
) F ON A.material_mode = F.material_mode
      AND F.stock_location = E.city
      AND A.information_sources = F.information_sources
```

关键规则：bom_total_table 中 stock_location='武汉' 的记录，在备料总表中映射为城市='武汉项目'。

第五步：关联库存和在途

```
LEFT JOIN reservoir_area_stock G ON G.sap_no = A.material_mode AND G.city = E.city
LEFT JOIN reservoir_area_stock L ON L.sap_no = A.material_mode AND L.city = '武汉'  -- 武汉库存单独取
LEFT JOIN purchasing_transit I ON I.material_mode = A.material_mode
LEFT JOIN dump_transit J ON J.sap_no = A.material_mode
LEFT JOIN rma_transit K ON K.material_code = A.material_mode
```

第六步：关联 XC02/XC16/XC17 库存

```
LEFT JOIN (
    SELECT material_mode,
           sum(CASE WHEN factory_code='MHMU' AND stock_address='XC02' THEN stock_quantity ELSE 0 END) as XC02_quantity,
           sum(CASE WHEN factory_code='MHMU' AND stock_address='XC16' THEN stock_quantity ELSE 0 END) as XC16_quantity,
           sum(CASE WHEN factory_code='MH48' AND stock_address='XC17' THEN stock_quantity ELSE 0 END) as XC17_quantity
    FROM (
        -- 同第一步的物料展开逻辑，但不需要 information_sources
        SELECT CASE WHEN b2.bundling_number IS NOT NULL THEN b3.material_mode
                    ELSE b1.material_mode
               END AS material_mode
        FROM bom_total_table b1
        LEFT JOIN bundling_part_number b2 ON b1.material_mode = b2.material_mode
        LEFT JOIN bundling_part_number b3 ON b2.bundling_number = b3.bundling_number
        GROUP BY b1.material_mode, b3.material_mode, b2.bundling_number
    ) bom_materials
    LEFT JOIN kunpeng_daily ON kunpeng_daily.material_code = bom_materials.material_mode
        AND stock_category != '借用在途库'  -- 排除借用在途库
    GROUP BY material_mode
) H ON H.material_mode = A.material_mode
```

第七步：在 SELECT 中计算业务字段

使用 business-formulas.md 中的公式计算：
- reserve_quantity（备货量）
- gap_quantity（缺口）= stock_quantity - reserve_quantity
- wuhan_stock_quantity（武汉库存量）
- stock_alert_status（库存预警）
- sum_each_gap（各库区总缺口）— 需要额外的子查询
- final_gap（最终缺口）= sum_each_gap + XC17_quantity + purchase_in_transit + dump_in_transit + rma_in_transit

第八步：各库区总缺口子查询

各库区总缺口 = 所有城市的(库存量 - 备货量)之和。
这需要一个独立的子查询，结构与主查询类似但只计算缺口：

```
LEFT JOIN (
    SELECT information_sources, material_code, sum(gap_quantity) as sum_each_gap
    FROM (
        -- 对每个城市计算：库存量 - 备货量
        SELECT information_sources, material_code, city,
               (stock_quantity - reserve_quantity) as gap_quantity
        FROM (
            -- 与主查询相同的物料+城市+销量+库存关联
            -- 计算 reserve_quantity 和 stock_quantity
        ) T
    ) T
    GROUP BY material_code, information_sources
) H ON T.material_code = H.material_code AND T.information_sources = H.information_sources
```

### 规则 3.5：NULL 处理

- 当 theoretical_defect_rate 为 NULL 时，备货量、缺口、库存预警、各库区总缺口、最终缺口 都应为 NULL
- 数值字段用 COALESCE(..., 0) 处理 NULL
- 字符串字段 NULL 输出为空字符串

---

## 级别四：分析型查询

适用于：数据汇总、统计分析、趋势分析等。

### 规则 4.1：分析查询的通用模式

```
SELECT <分组维度> as 中文名,
       count(*) as 记录数,
       count(DISTINCT <物料代码字段>) as 物料种类数,
       sum(<数量字段>) as 总数量,
       avg(<数值字段>) as 平均值
FROM <表名>
WHERE <筛选条件>
GROUP BY <分组维度>
ORDER BY <排序字段> DESC
```

### 规则 4.2：常见分析维度

| 用户说 | 分组维度 | 涉及的表 |
|---|---|---|
| "按城市分析" | city 或 stock_location | reservoir_area_stock 或 bom_total_table |
| "按备件大类分析" | spare_parts_category | base_material |
| "按产品分类分析" | name 或 spare_parts_type | base_material 或 bom_total_table |
| "按项目分析" | proj_name | bom_total_table |
| "按信息来源分析" | information_sources | bom_total_table |
| "在途分析" | 三张在途表 UNION ALL | purchasing_transit + dump_transit + rma_transit |

### 规则 4.3：跨表分析

当分析需要跨表关联时，以 base_material 或 bom_total_table 为主表，
LEFT JOIN 其他表获取补充信息。

### 规则 4.4：在途综合分析

三张在途表结构不同，需要用 UNION ALL 统一：
```
SELECT '采购在途' as 类型, count(*) as 物料数, COALESCE(sum(num), 0) as 总数量
FROM purchasing_transit
UNION ALL
SELECT '转储在途', count(*), COALESCE(sum(material_num), 0)
FROM dump_transit
UNION ALL
SELECT 'RMA在途', count(*), COALESCE(sum(quantity), 0)
FROM rma_transit
```

注意三张表的数量字段名不同：num / material_num / quantity。

### 规则 4.5：物料综合信息查询

当用户问"某个物料的全面信息"时，需要关联多张表：

以 base_material 为主表，LEFT JOIN：
- bundling_part_number（捆绑料号）
- reject_ratio（不良率）
- bom_total_table 聚合（总使用量、覆盖项目数）
- reservoir_area_stock 聚合（各城市库存）
- purchasing_transit（采购在途）
- dump_transit（转储在途）
- rma_transit（RMA在途）
- kunpeng_daily 聚合（BI库存）

### 规则 4.6：BOM 递归展开

当用户问"某个物料的BOM展开"时，使用 PostgreSQL 的 WITH RECURSIVE：

```
WITH RECURSIVE bom_tree AS (
    -- 起始层：直接子组件
    SELECT material_code, assembly, bom_assembly, bom_quantity, 1 as level
    FROM material_bom
    WHERE material_code = '<父物料代码>'

    UNION ALL

    -- 递归层：子组件的子组件
    SELECT m.material_code, m.assembly, m.bom_assembly,
           m.bom_quantity * bt.bom_quantity as bom_quantity,
           bt.level + 1
    FROM material_bom m
    JOIN bom_tree bt ON m.material_code = bt.assembly
)
SELECT assembly as 组件代码, bom_assembly as 组件描述,
       bom_quantity as 数量, level as 层级
FROM bom_tree
ORDER BY level, assembly
```

---

## 通用规则

### 规则 G1：SQL 安全

- 所有用户输入的值必须用单引号包裹
- 不要拼接用户输入到表名或字段名中
- 只查询本文件列出的表，不查询其他表

### 规则 G2：性能

- 大表查询必须加 LIMIT
- 避免 SELECT *，只选需要的列
- 聚合查询优先用 GROUP BY 而非子查询

### 规则 G3：输出格式

- 所有列名必须用中文别名
- 数值保留合理精度（不良率保留6位小数，金额保留2位）
- 日期字段直接输出（PostgreSQL 会返回 YYYY-MM-DD 格式）
- NULL 值在 Markdown 表格中显示为空

### 规则 G4：查询结果呈现

结果展示的详细规则见 SKILL.md 的"结果展示规则"段落。核心要求：
- 必须将查询结果转为 Markdown 表格直接展示在回复正文中
- 不能只说"查询完成"而不展示数据
- 默认展示前10条，超出时提示用户可以"继续"或"导出"
- 用户说"导出"时生成 .xlsx 文件
