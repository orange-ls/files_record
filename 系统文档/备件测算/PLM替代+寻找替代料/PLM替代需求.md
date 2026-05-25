#### 寻找替代料

在备件测算系统-"数据审视"菜单下增加”寻找替代料“表。

字段：物料代码、物料描述、供应商PN码、疑似可替代物料代码、疑似可替子节点中文描述、疑似可替供应商PN码。

需求：
1、点击“导入”按钮，读取“物料代码”、“物料描述”、“供应商PN码”三列的数据，并去除重复数据。

2、数据匹配部分，if-elif的关系：

2.1、根据“物料代码”，在“PLM替代”表(plm.alternative)中匹配'子节点SAP.NO'。如果没匹配到，进入步骤2.2；如果匹配到：疑似可替代物料代码、疑似可替子节点中文描述、疑似可替供应商PN码 分别取“PLM替代”的'捆绑料号'、'根节点中文描述'、空字符串。

2.2、根据“供应商PN码”，在“工厂物料清单”(factory.material.list)中，按规则模糊匹配“工业标准描述”。

​	模糊匹配规则：

​		1、“供应商PN码”以0开头：匹配出原“供应商PN码”和去除开头一个0的原“供应商PN码”。例：“供应商PN码”为01234，匹配出01234、1234。

​		2、“供应商PN码”不以0开头：匹配出原“供应商PN码”和增加开头一个0的原“供应商PN码”。例：“供应商PN码”为1234，匹配出01234、1234。

​		3、在1和2的基础上，匹配出“供应商PN码” + "-*"的，-后只能是一个字符。例：“供应商PN码”为1234，匹配出01234、1234、01234-1、1234-2、1234-6。

​		抓取所有满足任何一个条件的数据。

​	模糊匹配出结果后：疑似可替代物料代码、疑似可替子节点中文描述、疑似可替供应商PN码 分别取“工厂物料清单”的'物料代码'、'物料描述'、”工业标准描述“。

如果匹配出多个结果就返回多条数据。匹配不到就进入2.3。

2.3、根据”物料描述”，在“工厂物料清单”(factory.material.list)中，模糊匹配“物料描述”，相识度达90%及以上。



##### 需求变更：

1、在最后一列增加字段“捆绑料号”

2、第一级：PLM替代表精确匹配部分需要修改，

原逻辑是：根据“物料代码”，在“PLM替代”表(plm.alternative)中匹配'子节点SAP.NO'，疑似可替代物料代码、疑似可替子节点中文描述、疑似可替供应商PN码 分别取“PLM替代”的'捆绑料号'、'根节点中文描述'、空字符串。

修改为：根据“物料代码”，在“PLM替代”表(plm.alternative)中匹配'子节点SAP.NO'，找出对应的'根节点SAP.No'，将这个'根节点SAP.No'对的的所有数据返回。

疑似可替代物料代码、疑似可替子节点中文描述、疑似可替供应商PN码、捆绑料号 分别对应'子节点SAP.NO'、'子节点中文描述'、'供应商PN码'、'捆绑料号'

3、第二级：工厂物料清单模糊匹配（供应商PN码变体匹配）修改：

按”供应商PN码“模糊抓到数据后，判断factory_row['sap_no']是否是'313-'、'303-'、'282-'、'304'、'309'开头，如果是，继续判断下一个抓取来的数据。

这里也要加上捆绑料号，取factory_material_list的bundling_number

4、在页面上增加三个输入的文本框，分别是：物料代码、物料描述、供应商PN码。增加一个查询按钮。

要求点击“查询”按钮 时，需要先判断三个框是否都有值，然后才调用调入时的匹配方法获取数据并入库。



---

#### PLM替代

阅读xc_addons/xc_spare_parts中的代码，完成下面的需求。

在"数据审视"菜单下增加”PLM替代“表

”PLM替代“表中的字段：根节点SAP.No、根节点中文描述、子节点SAP.NO、子节点中文描述、供应商PN码、捆绑料号、BOM总表是否存在、武汉库存量、WHBJ库存、产品Ⅱ级分类、产品Ⅲ级分类。



1、根节点SAP.No、根节点中文描述、子节点SAP.NO、子节点中文描述、产品Ⅱ级分类、产品Ⅲ级分类：

```sql
WITH material_map  as (
	SELECT sap_no, max(chinese_description) description, max(product_category2) category2, max(product_category3) category3
	FROM xc_plm_material
	WHERE sap_no is not null AND sap_no != ''
	GROUP BY sap_no
)

SELECT xppb.f_sap_no, sd.description as f_description, xppb.sap_no, xppb.chinese_description, sc.category2, sc.category3
FROM xc_plm_product_bom xppb
LEFT JOIN material_map sd ON xppb.f_sap_no = sd.sap_no
LEFT JOIN material_map sc ON xppb.sap_no = sc.sap_no
WHERE bom_type IN ('替换','组合','')
AND xppb.f_sap_no LIKE '%69-00%'
ORDER BY xppb.f_sap_no
```

2、供应商PN码：按”子节点SAP.NO“ 关联”物料基础数据“--物料代码，取"供应商PN码"；如果为空或取不到，”工厂物料清单“-物料代码 取”工业标准描述“，如果同一个”物料代码“对应多个”工业标准描述“，取字符最长那个。

3、捆绑料号：按”子节点SAP.NO“ 关联 ”捆绑料号“--物料代码，取"捆绑料号"，如果没匹配到，则为空字符串。

4、BOM总表是否存在：”子节点SAP.NO“若能关联上 ”BOM总表“--物料代码 则为”是“，否则为”否“

5、武汉库存量、WHBJ库存：

```sql
SELECT
	sap_no,
	sum(CASE city WHEN '武汉' THEN num ELSE 0 END) wh_num,
	sum(CASE city WHEN '武汉' THEN 0 ELSE num END) whbj_num
FROM reservoir_area_stock
GROUP BY sap_no
```

6、产品Ⅱ级分类、产品Ⅲ级分类：按”子节点SAP.NO“ 关联 ”物料基础数据“--物料代码 取'产品Ⅱ级分类'、'产品Ⅲ级分类'。如果有值就修改产品Ⅱ级分类、产品Ⅲ级分类，如果空值就保留原值。



重点：代码符合python代码规范，符合odoo14规范。有任何问题务必向我提问。



新增需求：
1、根节点SAP.No、根节点中文描述、子节点中文描述：改名为root_sap_no、root_description、description

2、refresh_data()方法中，不要使用一个sql查询所有数据。使用sql从xc_plm_product_bom中查询数据后，其他数据分别查询后，使用python的字典对数据进行更新，最后入库。

3、页面上只需要有导出按钮和刷新按钮，刷新按钮调用refresh_data()

4、重写search_read方法，在从数据库查询出数据时，按"根节点SAP.No" 分组，每一组间添加一行空行。
例如：数据库中有"根节点SAP.No"为1234、1234、2345、3456四条数据，页面展示时：

| 根节点SAP.No | 其他字段 |
| ------------ | -------- |
| 1234         |          |
| 1234         |          |
|              |          |
| 2345         |          |
|              |          |
| 3456         |          |



##### 需求变更：

增加字段：捆绑料号

从“物料基础数据”表中，按“子节点SAP.NO”匹配“捆绑料号”，取不到值填充为空字符串

```
SELECT DISTINCT material_code,bundling_number
FROM "base_material"
```



---

#### 欠料调拨总表

新增字段：

“采购在途”，“转储在途”，“RMA在途”，“WHBJ库存”

取值逻辑：

使用“捆绑料号”匹配下面sql的查询结果

1、“采购在途”：

```sql
SELECT bundling_number, sum(num) sum_num
FROM purchasing_transit
GROUP BY bundling_number
```

2、“转储在途”：

```sql
SELECT bundling_number, sum(material_num) sum_num
FROM dump_transit
GROUP BY bundling_number
```

3、“RMA在途”

```sql
SELECT bundling_number, sum(quantity) sum_num
FROM rma_transit
GROUP BY bundling_number
```

4、“WHBJ库存”

```sql
WITH reservoir_bundling AS (
	SELECT
		CASE
			WHEN bpn.bundling_number is null THEN ras.sap_no
			ELSE bpn.bundling_number
		END bundling_number,
		city, num
	FROM reservoir_area_stock ras
	LEFT JOIN bundling_part_number bpn ON ras.sap_no = bpn.material_mode
)

SELECT
	bundling_number,
	sum(
		CASE city
			WHEN '武汉' THEN 0
			ELSE num
		END
	) sum_num
FROM reservoir_bundling
GROUP BY bundling_number
```

---

信息来源 取值修改：

问题：现在的刷新逻辑中，信息来源 的值默认为“存量表”。这个设定需要修改。

方案：

按“物料代码”和“欠料城市”为键，匹配下面sql查询结果中的information_sources：

```sql
SELECT DISTINCT material_mode, stock_location, information_sources
FROM bom_total_table
UNION
SELECT DISTINCT bundling_number as material_mode, stock_location, information_sources
FROM bom_total_table
```

注意：上面这段sql查询结果可能存在同（material_mode, stock_location）有多个不同的information_sources，此时需要将他们合并为(material_mode, stock_location): '存量表/过保'。

---



#### 服务中心备件削价概览

问题：原product_lines是硬编码的，现在需要修改为动态获取。

product_lines的总类：从'material.inventory'表的system_product_line获取
方法1：使用sql查询

```sql
SELECT DISTINCT system_product_line
FROM material_inventory
WHERE system_product_line is not null
```

方法2：使用odoo14原生机制查询

注意：
1、我提供的两个方法可以参考，或者你有更优的方法。目的是尽可能缩短查询时间。

2、不要更改原有逻辑

3、“服务器汇总”行需要排在'服务器(鲲鹏)', '服务器(昇腾)'的后面。只有'服务器(鲲鹏)', '服务器(昇腾)'都存在是才添加“服务器汇总”。

4、没有'服务器(鲲鹏)', '服务器(昇腾)'时，也要正常计算其他类别的数据

---



#### 工厂物料清单

增加字段：捆绑料号

从“物料基础数据”表中，按“物料代码”匹配“捆绑料号”，取不到值填充为空字符串

```sql
SELECT DISTINCT material_code,bundling_number
FROM "base_material"
```

