#### WMS超时流转单据

##### 基础数据抓取

在”收发货报表“菜单下的最后增加一个子菜单”WMS超时流转单据“

**字段**：”单据类型“、”相关单号“、”库房“、”单据状态“、”创建时间“

**页面**：导出按钮

**刷新方式**：设置定时任务，每天刷新一次。页面上不需要有刷新按钮

**刷新逻辑**：

一、先删除旧数据，再插入新数据

二、数据由下面四个部分组成

1、单据 - 物流单管理 - 出库单	k3_im.wm_do

| 字段（中文） | 取值                      | 字段名（英文）     | 取值                      |
| ------------ | ------------------------- | ------------------ | ------------------------- |
| 创建时间     | (当日0点 - 1月) ~ 当日0点 | create_time        | (当日0点 - 1月) ~ 当日0点 |
| 过账状态     | 未过账、待过账、部分过账  | post_status        | 0010、0015、0020          |
| 状态         | 正常                      | status             | 0                         |
| 单据类型     | 备件库间转储出库单        | ordertype_name     | 备件库间转储出库单        |
| 外部单据号   | -                         | cust_order_id_list | -                         |

post_status=0010未过账、0015待过账、0020部分过账、0030已过账、0040已冲销

---

2、单据 - 物流单管理 - 入库单	k3_im.wm_po

| 字段（中文） | 取值                     | 字段名（英文） | 取值                 |
| ------------ | ------------------------ | -------------- | -------------------- |
| 创建时间     | (当日3天前0点 - 1月)     | create_time    | (当日3天前0点 - 1月) |
| 过账状态     | 未过账、待过账、部分过账 | post_status    | 0010、0015、0020     |
| 状态         | 正常                     | status         | 0                    |
| 单据类型     | 备件库间转储入库单       | type_name      | 备件库间转储入库单   |
| 外部单据号   | -                        | cust_order_id  | -                    |

post_status=0010未过账、0015待过账、0020部分过账、0030已过账

---

3、维修 - 申请单	k3_repair.od_apply

ynflag = 1

| 字段（中文） | 取值                      | 字段名（英文） | 取值                      |
| ------------ | ------------------------- | -------------- | ------------------------- |
| 创建时间     | (当日0点 - 6月) ~ 当日0点 | create_time    | (当日0点 - 6月) ~ 当日0点 |
| 单据状态     | 已创建                    | order_status   | create                    |
| 外部换件单号 | -                         | ref_order_no   | -                         |

order_status=create已创建、auditPass已审核、revoke已撤单

---

4、维修 - 换件单	k3_repair.od_replace

ynflag = 1

| 字段（中文） | 取值                      | 字段名（英文） | 取值                      |
| ------------ | ------------------------- | -------------- | ------------------------- |
| 创建时间     | (当日0点 - 6月) ~ 当日0点 | create_time    | (当日0点 - 6月) ~ 当日0点 |
| 单据状态     | 已创建、备件待发货        | status         | create、readyToSend       |
| 外部换件单号 | -                         | ref_order_no   | -                         |

&&

| 字段（中文） | 取值                                | 字段名（英文） | 取值                                |
| ------------ | ----------------------------------- | -------------- | ----------------------------------- |
| 创建时间     | (当日1天前0点 - 6月) ~ 当日1天前0点 | create_time    | (当日1天前0点 - 6月) ~ 当日1天前0点 |
| 单据状态     | 备件已发货                          | status         | alreadySend                         |
| 外部换件单号 | -                                   | ref_order_no   | -                                   |

&&

| 字段（中文） | 取值                      | 字段名（英文） | 取值                      |
| ------------ | ------------------------- | -------------- | ------------------------- |
| 创建时间     | (当日0点 - 6月) ~ 当日0点 | create_time    | (当日0点 - 6月) ~ 当日0点 |
| 单据状态     | 备件更换中                | status         | replacing                 |
| 备件签收时间 | 空                        | signed_time    | null                      |
| 外部换件单号 | -                         | ref_order_no   | -                         |

status=create已创建、revoke已撤单、readyToSend备件待发货、alreadySend备件已发货、replacing备件更换中、alreadyReplace备件已更换、materSendBack旧件已寄回

5、sql语句参考：

```sql
-- K3_im
SELECT 
	'出库单' AS type,
	cust_order_id_list,
	house_name,
	CASE post_status
		WHEN '0010' THEN '未过账'
		WHEN '0015' THEN '待过账'
		WHEN '0020' THEN '部分过账'
		ELSE post_status
	END post_status,
	create_time
FROM `wm_do`
WHERE create_time BETWEEN '2026-07-04' AND '2026-08-04'
	AND post_status IN ('0010', '0015', '0020')
	AND status = '0'
	AND ordertype_name = '备件库间转储出库单'
```

```sql
-- K3_im
SELECT 
	'入库单' AS type,
	cust_order_id,
	house_name,
	CASE post_status
		WHEN '0010' THEN '未过账'
		WHEN '0015' THEN '待过账'
		WHEN '0020' THEN '部分过账'
		ELSE post_status
	END post_status,
	create_time
FROM `wm_po`
WHERE create_time BETWEEN '2026-07-01' AND '2026-08-01'
	AND post_status IN ('0010', '0015', '0020')
	AND status = '0'
	AND type_name = '备件库间转储入库单'
```

```sql
-- k3_repair
SELECT 
	'申请单' AS type,
	ref_order_no,
	house_name,
	'已创建' order_status,
	create_time
FROM `od_apply`
WHERE create_time BETWEEN '2026-02-04' AND '2026-08-04'
	AND order_status = 'create'
	AND ynflag  = '1'
```

```sql
-- k3_repair
SELECT 
	'换件单' AS type,
	ref_order_no,
	house_name,
	CASE status
		WHEN 'create' THEN '已创建'
		WHEN 'readyToSend' THEN '备件待发货'
		ELSE status
	END status,
	create_time
FROM `od_replace`
WHERE create_time BETWEEN '2026-02-04' AND '2026-08-04'
	AND `status` IN ('create', 'readyToSend')
	AND ynflag  = '1'
UNION ALL
SELECT 
	'换件单' AS type,
	ref_order_no,
	house_name,
	'备件已发货' status,
	create_time
FROM `od_replace`
WHERE create_time BETWEEN '2026-02-03' AND '2026-08-03'
	AND `status` = 'alreadySend'
	AND ynflag  = '1'
UNION ALL
SELECT 
	'换件单' AS type,
	ref_order_no,
	house_name,
	'备件更换中' status,
	create_time
FROM `od_replace`
WHERE create_time BETWEEN '2026-02-04' AND '2026-08-04'
	AND `status` = 'replacing'
	AND signed_time is NULL
	AND ynflag  = '1'
```

6、数据库连接参考：

```python
with self.env['wms.abutment']._get_db_connection('k3_im') as im_conn:
    with im_conn.cursor() as im_cur:
        im_cur.execute(sql)
        records = im_cur.fetchall()
```

```python
with self.env['wms.abutment']._get_db_connection('k3_repair') as im_conn:
    with im_conn.cursor() as im_cur:
        im_cur.execute(sql)
        records = im_cur.fetchall()
```

三、将查询结果中的”house_name“替换

```sql
SELECT DISTINCT storeroom_name, address
FROM wms_storeroom_table
```

```python
self._cr.execute(sql)
records = self._cr.dictfetchall()
```

​	house_name = storeroom_name，将house_name 替换成address

四、使用”INSERT INTO“将结果插入数据库

五、后续会增加邮件发送功能，请提前规划好代码结构





##### 增加邮件发送功能

在wms_timeout_document.py中增加中间表的定义：“WMS超时流转单据邮箱配置”

字段：城市、邮箱

更新方式：人工直接将数据导入到数据库，只需要模型定义，不需要前端页面，不需要权限控制。

数据样式：存在多个“城市”对应一个“邮箱”、也存在多个“邮箱”对应一个“城市”的情况

邮件发送逻辑：

​	1、在wms.timeout.document刷新完，数据入库后，进行邮件发送功能

​	2、将wms.timeout.document中的数据按“house_name”分组，并生成为一个个excel表格。

​	3、找出“城市” = house_name对应的邮箱，将对应house_name的excel发送给对应的邮箱。

​	4、邮箱地址以"@digitalchina.com"结尾时，使用xc_addons/xc_common/xc_utils.py XcMessage.send_mail_file()；

​		参考XcMessage.send_out_mail()和XcMessage.send_mail_file()，写一个带附件的外部邮件邮件发送方法。其余邮箱就按这个方法发送邮件

