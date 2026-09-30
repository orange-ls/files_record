
-- 分片
WITH CTE AS (
    SELECT 
        ID,
        write_date,
        ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) AS RowNum
    FROM 
        sn_service_bom_info
    WHERE 
        write_date >= '2025-04-02'
)
UPDATE CTE
SET write_date = DATEADD(DAY, (RowNum - 1) / 50000, '2025-04-02');



-- 查询分片
SELECT 
    write_date,
    COUNT(*) AS RecordCount
FROM 
    sn_service_bom_info
WHERE 
    write_date >= '2025-04-29'
GROUP BY 
    write_date
ORDER BY 
    write_date;
		
		
		
		
		
SELECT 
    COUNT(*) AS RecordCount
FROM 
    sn_service_bom_info
WHERE 
    write_date >= '2025-04-29'	
		AND write_date < '2025-04-30'	
		
		
		
		
		
-- 把4月20号的时间改为25号，然后再把其中的一万条数据改为21号
UPDATE sn_service_bom_info
SET write_date = '2025-04-25'
WHERE write_date = '2025-04-20'


UPDATE TOP (10000) sn_service_bom_info
SET write_date = '2025-04-21'
WHERE write_date = '2025-04-25'


-- 往26号放2万的数据（包含1万的删除数据）
SELECT COUNT(1) FROM sn_service_bom_info WHERE write_date = '2025-04-25' AND del_flag!=1


UPDATE TOP (10000) sn_service_bom_info
SET write_date = '2025-04-26'
WHERE write_date = '2025-04-25'
		AND del_flag=1

UPDATE TOP (10000) sn_service_bom_info
SET write_date = '2025-04-26'
WHERE write_date = '2025-04-25'
		AND del_flag!=1
		
SELECT 
	sum(
		CASE del_flag
			WHEN 1 THEN 1
			ELSE 0
		END) as flag1,
	sum(
		CASE del_flag
			WHEN 0 THEN 1
			ELSE 0
		END) as flag0
FROM
	sn_service_bom_info
WHERE write_date = '2025-04-26'


-- 往27号搞100万，剩下的搞到28号
UPDATE TOP (1000000) sn_service_bom_info
SET write_date = '2025-04-27'
WHERE write_date = '2025-04-25'

UPDATE sn_service_bom_info
SET write_date = '2025-04-28'
WHERE write_date = '2025-04-25'


		