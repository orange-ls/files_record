WITH plm_mat as (
	SELECT sap_no, product_category1, product_category2, product_category3
	FROM xc_plm_material
	WHERE product_category1 = '服务器配件'
		AND product_category1 IS NOT NULL AND product_category2 IS NOT NULL AND product_category3 IS NOT NULL
		AND product_category1 != '' AND product_category2 != '' AND product_category3 != ''
		AND item_type NOT IN ('PSEITEMFWWL', 'PSEITEMFINISHRDGOODS', 'PSEITEMSEMIFINISHED')
	ORDER BY product_category1, product_category2, product_category3
)

SELECT DISTINCT product_category1, product_category2, xpc.en as product_category2_en, product_category3, attribute_label as spec_attr, attribute_key as spec_attr_en, value_display as spec_attr_value
FROM plm_mat pm
LEFT JOIN xc_quotwise_product_spec_option xq ON pm.sap_no = xq.sample_sap_no
LEFT JOIN xc_plm_category2_mapping xpc ON pm.product_category2 = xpc.cn
WHERE attribute_label is not NULL