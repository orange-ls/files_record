-- 以 WMS库房分配表为例，处理自增id重复问题

SELECT * FROM "wms_storeroom_table"


-- 1、检查自增序列：
-- 自增id名：表名_id_seq
SELECT is_called, last_value FROM wms_storeroom_table_id_seq;

-- 2、重置自增序列：
SELECT setval('wms_storeroom_table_id_seq', (SELECT MAX(id) FROM wms_storeroom_table) + 1);

-- 查找重复的 id：
SELECT id, COUNT(*)
FROM material_inventory
GROUP BY id
HAVING COUNT(*) > 1;