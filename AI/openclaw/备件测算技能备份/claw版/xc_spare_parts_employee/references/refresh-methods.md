# 数据刷新逻辑

本文件描述备件测算系统各数据表的数据来源和刷新逻辑。
当用户要求"最新数据"、"刷新"、"更新"时，需要按照本文件描述的逻辑重新抓取数据。

注意：由于数据刷新涉及连接外部系统（Oracle BI、WMS API、SAP RFC、CRM MySQL），
skill 本身无法直接执行刷新操作。当用户要求刷新时，应提示用户通过以下方式之一触发：
1. 在 Odoo 系统页面点击"刷新"按钮
2. 等待每日定时任务自动执行（每天22:30）

以下是各表数据的来源和刷新逻辑描述，供理解数据含义和判断数据时效性使用。

---

## 一、全量刷新流程

全量刷新按以下顺序依次执行：

### 步骤1：刷新BOM总表（bom_total_table）

数据来源：purchase_order_inventory（PO单与存量）+ material_bom（物料BOM）

处理逻辑：
1. 清空 bom_total_table 表
2. 从 purchase_order_inventory 读取所有PO单数据
3. 对每个物料代码，在 material_bom 中递归展开BOM（WITH RECURSIVE）
4. 应用物料转换：将 material_transformation 中的 69码替换为 302码
5. 过滤非电子物料：排除 non_electronic_materials 中的物料
6. 关联 base_material 获取产品分类和备件大类
7. 关联 bundling_part_number 获取捆绑料号
8. 关联 sn_service_complete_info 获取服务开始/结束时间
9. 根据服务结束时间判断信息来源：过保（结束时间<今天）或存量表
10. 相同物料+项目+城市+信息来源+服务时效+更新日期的记录合并数量

### 步骤2：同步CRM字段（crm_table）

数据来源：bom_total_table 的最新数据
处理逻辑：将BOM总表数据同步到 crm_table 供外部系统查询

### 步骤3：同步WMS库存（reservoir_area_stock + rma_transit）

数据来源：WMS系统 API（http://xcwms.digitalchina.com）

处理逻辑：
1. 从 bom_total_table 获取所有物料代码
2. 将物料代码转换为18位SAP格式（去横杠，前补零）
3. 调用 WMS API 获取库存数据
4. 将 WMS 返回的库存地编码映射为城市名称（通过 stock_params 映射表）
5. 清空 reservoir_area_stock 表，写入新数据
6. 从 WMS 返回数据中筛选 RMA 库存地（WHWXC-FCZT）的数据
7. 清空 rma_transit 表，写入 RMA 在途数据

库存地编码→城市映射（部分示例）：
```
KCDBJ-WHBJC → 武汉
KCDBJ-BJBJC → 北京
KCDBJ-SHBJC → 上海
KCDBJ-GZBJC → 广州
KCDBJ-CDBJC → 成都
... 共45个城市
```

RMA库存地编码：`WHWXC-FCZT`

### 步骤4：同步其他库区库存（other_reservoir_area_stock）

数据来源：同 WMS API，但使用不同的库存地编码映射
处理逻辑：与步骤3类似，但写入 other_reservoir_area_stock 表

### 步骤5：同步鲲鹏日报（kunpeng_daily）

数据来源：Oracle BI视图 DCDWS.VW_DCN_DIKCMX

处理逻辑：
1. 连接 Oracle 数据库查询 BI 视图
2. 清空 kunpeng_daily 表
3. 将 Oracle 返回的数据关联 bundling_part_number 补充捆绑料号
4. 写入 kunpeng_daily 表

Oracle 查询的字段映射：
```
事业部名称 → division_name
业务范围代码 → service_scope_code
业务类型 → service_category
工厂代码 → factory_code
工厂类型 → factory_category
物料代码 → material_code（转换为 xxx-xxxxxx 格式）
物料名称 → material_desc
库存地代码 → stock_address
实际库存数量 → stock_quantity
移动平均单价 → avg_price
...
```

---

## 二、单独刷新操作

### 仅刷新WMS库存

只执行上述步骤3，不影响其他表。
适用场景：用户说"更新库存"、"刷新库区库存"

### 仅刷新BI数据

只执行上述步骤5，不影响其他表。
适用场景：用户说"更新鲲鹏日报"、"刷新BI数据"

### 刷新出库单（material_stock_order）

数据来源：WMS MySQL 数据库（wm_do + wm_do_item + wm_do_item_detail 表）

处理逻辑：
1. 从 WMS MySQL 查询最近6个月的备件出库单（ordertype_name='备件出库单', post_status='0030'）
2. 将18位物料编码转换为 xxx-xxxxxx 格式
3. 关联 base_material 获取物料描述和分类
4. 关联 wms_storeroom_table 获取库房简称
5. 关联 bundling_part_number 获取捆绑料号
6. 关联 reservoir_area_stock 获取库存数量
7. 写入或更新 material_stock_order 表

### 刷新备货申请（compute_proj_apply）

数据来源：crm_compute_contract_stock + xc_quotation + xc_product 等表（PostgreSQL 本库）

处理逻辑：
1. 从 crm_compute_contract_stock 关联 xc_quotation、xc_product 等表查询PO通知单数据
2. 关联 bundling_part_number 获取捆绑料号
3. 过滤非电子物料
4. 关联 kunpeng_daily 获取公司库存和WHBJ库存
5. 按服务描述判断服务时效（白金→7*24*2H，金牌→7*24*4H，标准→7*24*ND）
6. 只保留库存不足的记录（公司库存=0且WHBJ库存=0，或公司库存<=数量且WHBJ库存=0）
7. 清空 compute_proj_apply 表，写入新数据

---

## 三、数据时效性判断

可以通过查询表的 write_date 或 create_date 判断数据最后更新时间：

```sql
-- 查看各表最后更新时间
SELECT 'bom_total_table' as 表名, max(write_date) as 最后更新 FROM bom_total_table
UNION ALL SELECT 'reservoir_area_stock', max(write_date) FROM reservoir_area_stock
UNION ALL SELECT 'kunpeng_daily', max(create_date) FROM kunpeng_daily
UNION ALL SELECT 'material_stock_order', max(write_date) FROM material_stock_order
UNION ALL SELECT 'rma_transit', max(write_date) FROM rma_transit
```

---

## 四、触发刷新的关键词

当用户消息中包含以下关键词时，应提示需要先刷新数据：
- "最新"、"最新数据"、"更新数据"、"刷新"、"同步"
- "实时"、"当前"（暗示需要最新数据）
- "重新获取"、"重新拉取"

不需要刷新的情况：
- 用户只是普通查询，没有强调"最新"
- 用户明确说"查现有数据"、"查库里的数据"

当需要刷新时的回复模板：
"数据刷新需要连接外部系统（WMS/Oracle BI/SAP），请在 Odoo 系统中点击'刷新BOM总表'按钮，
或等待每日22:30的定时任务自动执行。刷新完成后我可以为您查询最新数据。
当前数据库中的数据最后更新时间为：[查询 write_date 结果]"

---

## 五、定时任务配置

| 任务名 | 执行频率 | 执行时间 | 说明 |
|---|---|---|---|
| 鲲鹏日报同步BI数据 | 每天 | 22:30 | 同步 Oracle BI 视图 |
| 备件测算同步WMS数据 | 每天 | 22:30 | 同步各库区库存 |
| 备件测算其他库区库存同步 | 每天 | 22:50 | 同步其他库区库存 |
| 备件测算同步出库单 | 每天 | 22:30 | 同步400派件补库单 |
| 备件测算未测算项目通知 | 每天 | 22:30 | 发送未测算项目邮件通知 |
| 备件测算同步库存查询 | 每天 | 22:30 | 同步SAP库存 |
