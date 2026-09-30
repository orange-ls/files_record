-- 以 WMS库房分配表为例，处理自增id重复问题

SELECT * FROM "call_statistics_report"


-- 1、检查自增序列：
-- 自增id名：表名_id_seq
SELECT is_called, last_value FROM xc_quotwise_category_spec_attribute_id_seq;

-- 2、重置自增序列：
-- SELECT setval('xc_quotwise_category_spec_attribute_id_seq', (SELECT MAX(id) FROM xc_quotwise_category_spec_attribute) + 1);




-- 查找重复的 id：
SELECT id, COUNT(*)
FROM material_inventory
GROUP BY id
HAVING COUNT(*) > 1;



-- 智能报价 新增规格标签
-- SELECT setval('xc_quotwise_category_spec_attribute_id_seq', (SELECT MAX(id) FROM xc_quotwise_category_spec_attribute));
