WITH res_stock AS (
	SELECT sap_no, bundling_number, city, sum(num) num, max(material_desc) material_desc, max(supplier_pn) supplier_pn
	FROM reservoir_area_stock
	WHERE num > 1
	GROUP BY sap_no, bundling_number, city
),
sum_table_data AS (
	SELECT DISTINCT material_code, bundling_number, stock_location, information_sources
	FROM summary_kanban
	WHERE information_sources = '过保'
)
SELECT sap_no, rs.bundling_number, city, num, material_desc, supplier_pn, information_sources
FROM res_stock rs
LEFT JOIN sum_table_data std ON rs.sap_no = std.material_code AND rs.bundling_number = std.bundling_number AND rs.city = stock_location
WHERE information_sources = '过保'