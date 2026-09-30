
WITH bom_num AS (
	SELECT 
		material_mode,
		TO_CHAR(server_stare_time, 'YYYY/MM') stare_month,
		TO_CHAR(server_end_time, 'YYYY/MM') end_month,
		sum_count
	FROM bom_total_table
	ORDER BY material_mode
),
bom_base AS (
	SELECT
		material_mode,
		TO_CHAR(gs.natural_month, 'YYYY/MM') AS natural_month
	FROM (
			SELECT DISTINCT material_mode
			FROM bom_total_table
	) rd
	CROSS JOIN LATERAL generate_series(
			to_date('2024/01', 'YYYY/MM')::timestamp,
			date_trunc('month', CURRENT_DATE),
			interval '1 month'
	) AS gs(natural_month)
)

SELECT
    a.material_mode,
    a.natural_month,
    COALESCE(SUM(b.sum_count), 0) AS total_sum_count   -- 无匹配时返回 0
FROM bom_base a
LEFT JOIN bom_num b
    ON a.material_mode = b.material_mode
    AND b.stare_month <= a.natural_month
    AND a.natural_month <= b.end_month
GROUP BY a.material_mode, a.natural_month
ORDER BY a.material_mode, a.natural_month;

