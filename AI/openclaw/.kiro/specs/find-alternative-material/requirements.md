# Requirements Document

## Introduction

在"数据审视"菜单下增加"寻找替代料"功能，用于帮助用户通过导入物料清单，自动匹配查找可替代料号。系统将按照PLM替代表、工厂物料清单模糊匹配、物料描述相似度匹配三个优先级顺序执行匹配逻辑，返回疑似可替代物料信息。

## Glossary

- **Alternative_Material_Finder**: 寻找替代料系统，本功能的核心业务逻辑组件
- **Material_Code**: 物料代码，SAP系统中的物料编码，格式为 xxx-xxxxxx
- **Material_Description**: 物料描述，物料的中文名称或描述
- **Supplier_PN**: 供应商PN码，供应商提供的物料编码
- **Suspected_Alternative_Code**: 疑似可替代物料代码，系统匹配出的可能替代料号
- **Suspected_Alternative_Description**: 疑似可替子节点中文描述，替代物料的中文描述
- **Suspected_Alternative_PN**: 疑似可替供应商PN码，替代物料的供应商编码
- **PLM_Alternative_Table**: PLM替代表(plm.alternative)，存储PLM系统中的替代料号关系
- **Factory_Material_List**: 工厂物料清单(factory.material.list)，存储工厂物料的主数据信息
- **Industry_Standard_Desc**: 工业标准描述，工厂物料清单中的供应商PN码字段
- **Similarity_Matcher**: 相似度匹配器，使用difflib.SequenceMatcher进行文本相似度计算

## Requirements

### Requirement 1: 数据模型定义

**User Story:** 作为系统管理员，我希望创建"寻找替代料"数据模型，以便存储用户导入的物料数据和匹配结果。

#### Acceptance Criteria

1. THE Alternative_Material_Finder SHALL 创建名为 `find.alternative.material` 的Odoo模型，包含以下字段：物料代码(Char)、物料描述(Char)、供应商PN码(Char)、疑似可替代物料代码(Char)、疑似可替子节点中文描述(Char)、疑似可替供应商PN码(Char)
2. THE Alternative_Material_Finder SHALL 为物料代码字段创建数据库索引，以优化查询性能
3. THE Alternative_Material_Finder SHALL 实现active字段作为逻辑删除标志，默认值为True

### Requirement 2: Excel导入功能

**User Story:** 作为备件测算人员，我希望通过导入Excel文件批量录入待查找的物料清单，以便快速进行替代料匹配。

#### Acceptance Criteria

1. WHEN 用户点击"导入"按钮，THE Alternative_Material_Finder SHALL 弹出文件选择对话框，支持选择 .xlsx 或 .xls 格式的Excel文件
2. WHEN 用户选择Excel文件并确认，THE Alternative_Material_Finder SHALL 读取Excel中的"物料代码"、"物料描述"、"供应商PN码"三列数据
3. THE Alternative_Material_Finder SHALL 对导入的数据进行去重处理，以物料代码为唯一键保留第一条记录
4. WHEN Excel文件格式不符合要求（缺少必要列或无法解析），THE Alternative_Material_Finder SHALL 返回明确的错误提示信息
5. WHEN 导入成功完成，THE Alternative_Material_Finder SHALL 显示导入的记录数量

### Requirement 3: PLM替代表匹配

**User Story:** 作为备件测算人员，我希望系统优先从PLM替代表中查找替代料号，以便获取准确的替代关系。

#### Acceptance Criteria

1. WHEN 开始匹配流程，THE Alternative_Material_Finder SHALL 首先根据"物料代码"字段在 PLM_Alternative_Table 中匹配 sap_no 字段
2. WHEN 在 PLM_Alternative_Table 中找到匹配记录，THE Alternative_Material_Finder SHALL 将 bundling_number 字段值填入"疑似可替代物料代码"，root_description 字段值填入"疑似可替子节点中文描述"，"疑似可替供应商PN码"填入空字符串
3. WHEN 一个物料代码在 PLM_Alternative_Table 中匹配到多条记录，THE Alternative_Material_Finder SHALL 返回多条匹配结果
4. WHEN 在 PLM_Alternative_Table 中未找到匹配记录，THE Alternative_Material_Finder SHALL 进入工厂物料清单模糊匹配流程（Requirement 4）

### Requirement 4: 工厂物料清单模糊匹配

**User Story:** 作为备件测算人员，我希望系统能够根据供应商PN码进行模糊匹配，以便找到更多可能的替代料号。

#### Acceptance Criteria

1. WHEN 进入工厂物料清单匹配流程，THE Alternative_Material_Finder SHALL 根据"供应商PN码"字段在 Factory_Material_List 的 Industry_Standard_Desc 字段中进行模糊匹配
2. WHERE 供应商PN码以字符"0"开头，THE Alternative_Material_Finder SHALL 同时匹配原始值和去除开头一个"0"后的值，以及这两种值加上"-*"后缀的模式（"-"后仅允许一个字符）
3. WHERE 供应商PN码不以字符"0"开头，THE Alternative_Material_Finder SHALL 同时匹配原始值和增加开头一个"0"后的值，以及这两种值加上"-*"后缀的模式（"-"后仅允许一个字符）
4. WHEN 匹配到工厂物料清单记录，THE Alternative_Material_Finder SHALL 将 sap_no 字段值填入"疑似可替代物料代码"，material_desc 字段值填入"疑似可替子节点中文描述"，Industry_Standard_Desc 字段值填入"疑似可替供应商PN码"
5. WHEN 模糊匹配返回多条记录，THE Alternative_Material_Finder SHALL 返回所有匹配结果
6. WHEN 工厂物料清单模糊匹配未找到任何结果，THE Alternative_Material_Finder SHALL 进入物料描述相似度匹配流程（Requirement 5）

### Requirement 5: 物料描述相似度匹配

**User Story:** 作为备件测算人员，我希望系统能够根据物料描述进行相似度匹配，以便在精确匹配失败时找到近似替代料号。

#### Acceptance Criteria

1. WHEN 进入物料描述相似度匹配流程，THE Alternative_Material_Finder SHALL 使用 Similarity_Matcher 计算导入数据的"物料描述"与 Factory_Material_List 中 material_desc 字段的相似度
2. WHERE 相似度达到90%及以上，THE Alternative_Material_Finder SHALL 将匹配结果作为疑似可替代物料返回
3. WHEN 相似度匹配返回多条记录，THE Alternative_Material_Finder SHALL 返回所有符合条件的匹配结果
4. WHEN 相似度匹配未找到任何结果，THE Alternative_Material_Finder SHALL 保留原始导入数据，疑似替代字段保持为空

### Requirement 6: 匹配执行与结果展示

**User Story:** 作为备件测算人员，我希望系统能够自动执行匹配流程并展示结果，以便快速获取替代料号信息。

#### Acceptance Criteria

1. WHEN 用户完成Excel导入，THE Alternative_Material_Finder SHALL 自动触发匹配流程，按照 Requirement 3 → Requirement 4 → Requirement 5 的顺序执行
2. WHEN 某条物料在前一优先级匹配成功，THE Alternative_Material_Finder SHALL 跳过后续优先级的匹配
3. WHEN 匹配流程完成，THE Alternative_Material_Finder SHALL 在列表视图展示所有导入记录及其匹配结果
4. THE Alternative_Material_Finder SHALL 在列表视图中清晰区分已匹配成功和未匹配成功的记录

### Requirement 7: 数据导出功能

**User Story:** 作为备件测算人员，我希望能够导出匹配结果，以便在Excel中进行进一步分析和存档。

#### Acceptance Criteria

1. WHEN 用户点击"导出"按钮，THE Alternative_Material_Finder SHALL 将当前筛选条件下的所有记录导出为Excel文件
2. THE Alternative_Material_Finder SHALL 在导出的Excel中包含所有六个字段：物料代码、物料描述、供应商PN码、疑似可替代物料代码、疑似可替子节点中文描述、疑似可替供应商PN码
3. THE Alternative_Material_Finder SHALL 使用黄色背景样式设置表头行，并冻结首行
4. THE Alternative_Material_Finder SHALL 以"寻找替代料_{YYYYMMDD}.xlsx"格式命名导出文件

### Requirement 8: 权限控制

**User Story:** 作为系统管理员，我希望对"寻找替代料"功能的导入操作进行权限控制，以确保数据安全。

#### Acceptance Criteria

1. THE Alternative_Material_Finder SHALL 创建名为"备件测算导入权限"的权限组（group_spare_parts_import），用于控制导入按钮的访问权限
2. WHERE 用户属于"备件测算导入权限"组，THE Alternative_Material_Finder SHALL 在列表视图中显示"导入"按钮
3. WHERE 用户不属于"备件测算导入权限"组，THE Alternative_Material_Finder SHALL 隐藏"导入"按钮，不向用户展示
4. THE Alternative_Material_Finder SHALL 允许所有登录用户查看数据，无需特殊权限
5. THE Alternative_Material_Finder SHALL 允许所有登录用户导出数据，无需特殊权限

### Requirement 9: 菜单集成

**User Story:** 作为备件测算人员，我希望在"数据审视"菜单下看到"寻找替代料"入口，以便快速访问该功能。

#### Acceptance Criteria

1. THE Alternative_Material_Finder SHALL 在"信创备件测算系统 > 数据审视"菜单下创建"寻找替代料"菜单项
2. WHEN 用户点击"寻找替代料"菜单，THE Alternative_Material_Finder SHALL 展示替代料查询列表视图
3. THE Alternative_Material_Finder SHALL 在列表视图中提供"导入"和"导出"操作按钮

### Requirement 10: 性能优化

**User Story:** 作为备件测算人员，我希望系统在处理大批量数据时保持良好性能，以便高效完成工作。

#### Acceptance Criteria

1. WHEN 导入数据量超过100条，THE Alternative_Material_Finder SHALL 使用批量查询方式执行匹配，避免N+1查询问题
2. THE Alternative_Material_Finder SHALL 在匹配完成后清除不再需要的临时数据，释放系统资源
3. THE Alternative_Material_Finder SHALL 在匹配过程中记录执行日志，便于问题排查和性能分析

### Requirement 11: 错误处理

**User Story:** 作为备件测算人员，我希望系统在遇到异常情况时能够妥善处理，以便保证数据完整性。

#### Acceptance Criteria

1. WHEN 导入或匹配过程中发生异常，THE Alternative_Material_Finder SHALL 回滚所有数据库操作
2. WHEN 发生异常，THE Alternative_Material_Finder SHALL 记录详细的错误日志，包括错误类型、错误信息和堆栈跟踪
3. WHEN 发生异常，THE Alternative_Material_Finder SHALL 向用户显示友好的错误提示信息
