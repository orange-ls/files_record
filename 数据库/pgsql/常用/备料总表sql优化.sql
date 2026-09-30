SELECT DISTINCT
	information_sources,
	CASE WHEN b2.bundling_number IS NOT NULL THEN b2.material_mode
			 WHEN b2.bundling_number IS NULL THEN b1.material_mode
	END AS material_mode,
	b2.bundling_number 
FROM bom_total_table b1 
LEFT JOIN bundling_part_number b2 ON b1.bundling_number = b2.bundling_number
GROUP BY b1.material_mode,b2.material_mode,b2.bundling_number,information_sources
ORDER BY material_mode