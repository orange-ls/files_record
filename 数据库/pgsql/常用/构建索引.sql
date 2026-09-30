-- 递归 JOIN 的核心字段，必须建索引
CREATE INDEX IF NOT EXISTS idx_mfm_material_code ON material_find_manage(material_code);
CREATE INDEX IF NOT EXISTS idx_mfm_bom_component_code ON material_find_manage(bom_component_code);

-- 更新统计信息，让优化器选择正确的执行计划
ANALYZE material_find_manage;