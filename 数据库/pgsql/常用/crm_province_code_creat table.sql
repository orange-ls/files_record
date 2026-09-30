CREATE TABLE crm_province_code (
    id SERIAL PRIMARY KEY,
    type VARCHAR(255),
    name VARCHAR(255),
    code VARCHAR(255),
    parent_code VARCHAR(255),
    name_address VARCHAR(255),
    parent_code_address VARCHAR(255),
    admin_code VARCHAR(255),
    parent_admin_code VARCHAR(255)
		);
		
COMMENT ON COLUMN crm_province_code.id IS 'id';
COMMENT ON COLUMN crm_province_code.type IS '类型';
COMMENT ON COLUMN crm_province_code.name IS '名称';
COMMENT ON COLUMN crm_province_code.code IS '唯一编码';
COMMENT ON COLUMN crm_province_code.parent_code IS '上级唯一编码';
COMMENT ON COLUMN crm_province_code.name_address IS '名称全路径';
COMMENT ON COLUMN crm_province_code.parent_code_address IS '唯一编码全路径';
COMMENT ON COLUMN crm_province_code.admin_code IS '行政编码';
COMMENT ON COLUMN crm_province_code.parent_admin_code IS '上级行政编码';