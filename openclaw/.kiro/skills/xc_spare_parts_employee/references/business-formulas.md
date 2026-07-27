# 业务计算公式

本文件定义了备件测算系统中所有业务计算公式。
生成涉及备货量、缺口、库存预警等计算字段的 SQL 时，必须按照这些公式生成 CASE WHEN 表达式。

---

## 一、备货量（reserve_quantity）

备货量根据"销量 × 不良率"的值分段计算。

### 输入变量
- `sales`：某物料在某城市的销量（来自 bom_total_table 按 material_mode + stock_location 聚合的 sum(sum_count)）
- `theoretical_defect_rate`：理论不良率（来自 reject_ratio 表，numeric(16,8) 类型，如 0.002 表示 0.2%）

### 计算规则

| 条件 | 备货量 |
|---|---|
| 不良率为 NULL | NULL（不计算） |
| 销量 × 不良率 >= 8 | ceil(销量 × 不良率 / 4) |
| 1 < 销量 × 不良率 < 8 | 2 |
| 0 < 销量 × 不良率 <= 1 | 1 |
| 销量 × 不良率 = 0 | 0 |

### SQL 表达式

```sql
CASE
    WHEN theoretical_defect_rate IS NULL THEN NULL
    WHEN sales * theoretical_defect_rate::float >= 8
        THEN ceil((sales * theoretical_defect_rate::float / 4)::numeric)
    WHEN sales * theoretical_defect_rate::float < 8
        AND sales * theoretical_defect_rate::float > 1 THEN 2
    WHEN sales * theoretical_defect_rate::float <= 1
        AND sales * theoretical_defect_rate::float > 0 THEN 1
    WHEN sales * theoretical_defect_rate::float = 0 THEN 0
    ELSE 0
END AS reserve_quantity
```

注意：`theoretical_defect_rate` 在数据库中是 numeric 类型，SQL 中需要 `::float` 转换。

---

## 二、缺口（gap_quantity）

缺口 = 库存量 - 备货量。

### 输入变量
- `stock_quantity`：某物料在某城市的库存量（来自 reservoir_area_stock 表的 num 字段）
- `reserve_quantity`：备货量（上面公式计算的结果）

### 计算规则

| 条件 | 缺口 |
|---|---|
| 不良率为 NULL | NULL |
| 其他 | stock_quantity - reserve_quantity |

缺口为负数表示库存不足，正数表示库存充足。

### SQL 表达式

```sql
CASE
    WHEN theoretical_defect_rate IS NULL THEN NULL
    ELSE COALESCE(stock_quantity - reserve_quantity, 0)
END AS gap_quantity
```

---

## 三、库存预警（stock_alert_status）

库存预警基于"武汉库存量"与"安全库存阈值"的比较。

### 输入变量
- `wuhan_stock_quantity`：武汉库存量（来自 reservoir_area_stock 表 city='武汉' 的 num）
- `total_usage`：总使用量（来自 bom_total_table 按 material_mode 聚合的 sum(sum_count)）
- `theoretical_defect_rate`：理论不良率

### 安全库存阈值
```
安全库存 = ceil(总使用量 × 不良率 / 6)
```

### 计算规则

| 条件 | 预警状态 | 中文 |
|---|---|---|
| 不良率为 NULL | NULL | 不显示 |
| 武汉库存 >= 安全库存 且 > 0 | adequate | 充足 |
| 武汉库存 >= 安全库存/2 且 < 安全库存 | replenished | 补货 |
| 武汉库存 > 0 且 < 安全库存/2 | urgently_replenished | 急需补货 |
| 武汉库存 <= 0 | out_of_stock | 无库存 |

### SQL 表达式

```sql
CASE
    WHEN theoretical_defect_rate IS NULL THEN NULL
    WHEN wuhan_stock_quantity >= ceil(total_usage * theoretical_defect_rate::float / 6)
        AND wuhan_stock_quantity > 0 THEN 'adequate'
    WHEN wuhan_stock_quantity >= ceil(total_usage * theoretical_defect_rate::float / 6) / 2
        AND wuhan_stock_quantity < ceil(total_usage * theoretical_defect_rate::float / 6) THEN 'replenished'
    WHEN wuhan_stock_quantity > 0
        AND wuhan_stock_quantity < ceil(total_usage * theoretical_defect_rate::float / 6) / 2 THEN 'urgently_replenished'
    WHEN wuhan_stock_quantity <= 0 THEN 'out_of_stock'
    ELSE 'out_of_stock'
END AS stock_alert_status
```

输出时需要将英文值转为中文：
```sql
CASE stock_alert_status
    WHEN 'adequate' THEN '充足'
    WHEN 'replenished' THEN '补货'
    WHEN 'urgently_replenished' THEN '急需补货'
    WHEN 'out_of_stock' THEN '无库存'
    ELSE ''
END
```

---

## 四、各库区总缺口（sum_each_gap）

各库区总缺口 = 所有城市的缺口之和（不含武汉）。

### 计算逻辑
对每个城市分别计算 `库存量 - 备货量`，然后按物料代码和信息来源汇总求和。

### SQL 表达式（概念）

```sql
-- 对每个城市计算缺口，然后按物料汇总
SELECT material_code, information_sources, sum(stock_quantity - reserve_quantity) as sum_each_gap
FROM (
    -- 每个物料×每个城市的库存量和备货量
    ...
) T
GROUP BY material_code, information_sources
```

注意：当不良率为 NULL 时，sum_each_gap 也应为 NULL。

---

## 五、最终缺口（final_gap）

最终缺口 = 各库区总缺口 + XC17库存 + 采购在途 + 转储在途 + RMA在途。

### 输入变量
- `sum_each_gap`：各库区总缺口（上面公式计算的结果）
- `XC17_quantity`：XC17库存（来自 kunpeng_daily 表 factory_code='MH48' AND stock_address='XC17' 的 sum(stock_quantity)）
- `purchase_in_transit`：采购在途（来自 purchasing_transit 表的 num）
- `dump_in_transit`：转储在途（来自 dump_transit 表的 material_num）
- `rma_in_transit`：RMA在途（来自 rma_transit 表的 quantity）

### SQL 表达式

```sql
CASE
    WHEN theoretical_defect_rate IS NULL THEN NULL
    ELSE COALESCE(
        COALESCE(sum_each_gap, 0)
        + COALESCE(XC17_quantity, 0)
        + COALESCE(purchase_in_transit, 0)
        + COALESCE(dump_in_transit, 0)
        + COALESCE(rma_in_transit, 0),
    0)
END AS final_gap
```

---

## 六、XC02/XC16/XC17 库存

这三个库存来自 kunpeng_daily 表，按工厂代码+库存地代码聚合。

### 计算规则

| 字段 | 工厂代码 | 库存地代码 | 排除条件 |
|---|---|---|---|
| XC02_quantity | MHMU | XC02 | stock_category != '借用在途库' |
| XC16_quantity | MHMU | XC16 | stock_category != '借用在途库' |
| XC17_quantity | MH48 | XC17 | stock_category != '借用在途库' |

### SQL 表达式

```sql
sum(CASE WHEN factory_code = 'MHMU' AND stock_address = 'XC02' THEN stock_quantity ELSE 0 END) as XC02_quantity,
sum(CASE WHEN factory_code = 'MHMU' AND stock_address = 'XC16' THEN stock_quantity ELSE 0 END) as XC16_quantity,
sum(CASE WHEN factory_code = 'MH48' AND stock_address = 'XC17' THEN stock_quantity ELSE 0 END) as XC17_quantity
```

---

## 七、捆绑料号展开规则

BOM总表中的物料代码需要通过捆绑料号展开为实际的备件物料代码。

### 展开逻辑

1. 从 bom_total_table 获取 material_mode
2. 在 bundling_part_number 中查找该 material_mode 是否有对应的 bundling_number
3. 如果有捆绑料号，则找到该捆绑料号下的所有 material_mode（展开）
4. 如果没有捆绑料号，则物料代码就是它自己

### SQL 表达式

```sql
SELECT
    CASE WHEN b2.bundling_number IS NOT NULL THEN b3.material_mode
         ELSE b1.material_mode
    END AS material_mode
FROM bom_total_table b1
LEFT JOIN bundling_part_number b2 ON b1.material_mode = b2.material_mode
LEFT JOIN bundling_part_number b3 ON b2.bundling_number = b3.bundling_number
GROUP BY b1.material_mode, b3.material_mode, b2.bundling_number
```

获取物料的捆绑料号（如果没有则用物料代码本身）：
```sql
COALESCE(bn.bundling_number, <物料代码字段>) AS bundling_number
```

---

## 八、武汉→武汉项目 映射规则

在 bom_total_table 中，stock_location='武汉' 的记录在备料总表中映射为城市='武汉项目'。

### SQL 表达式

```sql
CASE WHEN stock_location = '武汉' THEN '武汉项目'
     ELSE stock_location
END AS stock_location
```

这个映射在计算销量时使用：bom_total_table 中 stock_location='武汉' 的 sum_count 会被归入城市='武汉项目'。

---

## 九、替代料备料总表的不良率计算

替代料备料总表（alternative.prepare.materials）中，不良率是按捆绑料号下所有物料的不良率取平均值。

### SQL 表达式

```sql
round(
    sum(COALESCE(theoretical_defect_rate, 0))::numeric
    / NULLIF(count(bundling_number), 0)::numeric,
    8
) AS theoretical_defect_rate
```

---

## 十、BOM 递归展开

物料BOM支持递归展开，将整机物料拆解为最小可替换备件。

### SQL 表达式（PostgreSQL WITH RECURSIVE）

```sql
WITH RECURSIVE bom_tree AS (
    SELECT material_code, assembly, bom_assembly, bom_quantity
    FROM material_bom
    WHERE material_code = '<父物料代码>'

    UNION ALL

    SELECT m.material_code, m.assembly, m.bom_assembly,
           m.bom_quantity * bt.bom_quantity as bom_quantity
    FROM material_bom m
    JOIN bom_tree bt ON m.material_code = bt.assembly
)
-- 只取叶子节点（不再有子组件的物料）
SELECT assembly, material_code, bom_quantity, bom_assembly
FROM bom_tree
WHERE assembly NOT IN (SELECT material_code FROM bom_tree)
```
