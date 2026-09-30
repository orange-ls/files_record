-- 1. 找到权限组的数据库 ID
SELECT res_id FROM ir_model_data 
WHERE module = 'xc_report' AND name = 'spare_parts_test_data_menu_group';

-- 2. 删除引用该组的 ir.model.access 记录（用上面查到的 res_id 替换）
-- DELETE FROM ir_model_access 
-- WHERE group_id = 11056;
-- 
-- -- 3. 删除权限组本身
-- DELETE FROM ir_model_data 
-- WHERE module = 'xc_report' AND name = 'spare_parts_test_data_menu_group';
-- 
-- DELETE FROM res_groups 
-- WHERE id = 11056;