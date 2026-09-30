WITH comp_repair_num AS (
	SELECT
		gzjwlh,
		TO_CHAR(cpr.create_time, 'YYYY/MM') AS repair_month,
		count(*) AS repair_num
	FROM compute_product_report cpr
	LEFT JOIN base_material bm ON cpr.gzjwlh = bm.material_code
	WHERE TO_CHAR(cpr.create_time, 'YYYY') IN ('2024', '2025', '2026')
	GROUP BY gzjwlh, repair_month
),
comp_base AS (
	SELECT
			rd.gzjwlh AS material_mode,
			rd.bundling_number,
			rd.big_category,
			rd.big_category1,
			rd.pro2,
			rd.pro3,
			TO_CHAR(gs.natural_month, 'YYYY/MM') AS natural_month
	FROM (
			SELECT
					cpr.gzjwlh,
					max(bm.bundling_number) bundling_number,
					max(bm.spare_parts_category) AS big_category,
					max(bm.spare_parts_category_1) AS big_category1,
					max(bm.name) AS pro2,
					max(bm.product_category3) AS pro3
			FROM compute_product_report cpr
			LEFT JOIN base_material bm ON bm.material_code = cpr.gzjwlh
			WHERE cpr.gzjwlh IS NOT NULL
					AND TO_CHAR(cpr.create_time, 'YYYY') IN ('2024', '2025', '2026')
			GROUP BY cpr.gzjwlh
	) rd
	CROSS JOIN LATERAL generate_series(
			to_date('2024/01', 'YYYY/MM')::timestamp,
			date_trunc('month', CURRENT_DATE),
			interval '1 month'
	) AS gs(natural_month)
)
SELECT
	material_mode,
	bundling_number,
	big_category,
	big_category1,
	pro2, pro3,
	natural_month,
	COALESCE(repair_num, 0) repair_num
FROM comp_base cb
LEFT JOIN comp_repair_num crn ON cb.material_mode = crn.gzjwlh AND cb.natural_month = crn.repair_month
ORDER BY material_mode




