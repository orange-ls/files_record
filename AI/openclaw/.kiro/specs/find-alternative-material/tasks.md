# Implementation Plan: 寻找替代料功能

## Overview

本任务列表实现"寻找替代料"功能，该功能集成在 xc_spare_parts 模块中。功能包括 Excel 导入物料清单、三级匹配逻辑（PLM精确匹配 → 工厂清单模糊匹配 → 相似度匹配）、匹配结果导出。

## Tasks

- [x] 1. 创建数据模型和数据库结构
  - [x] 1.1 创建 find_alternative_material.py 模型文件
    - 定义 `find.alternative.material` 模型及六个业务字段
    - 为 `material_code` 字段添加数据库索引
    - _Requirements: 1.1, 1.2, 1.3_
  
  - [x] 1.2 更新 models/__init__.py 导入新模型
    - 在 `xc_addons/xc_spare_parts/models/__init__.py` 中添加导入
    - _Requirements: 1.1_

- [x] 2. 实现Excel导入解析和去重逻辑
  - [x] 2.1 实现 Excel 解析方法
    - 读取 .xlsx/.xls 格式文件
    - 解析"物料代码"、"物料描述"、"供应商PN码"三列
    - 验证 Excel 格式，缺少必要列时返回明确错误
    - _Requirements: 2.1, 2.2, 2.4_
  
  - [x] 2.2 实现数据去重方法
    - 以物料代码为唯一键去重
    - 保留第一次出现的记录
    - _Requirements: 2.3_

- [x] 3. 实现三级匹配算法
  - [x] 3.1 实现 PLM 替代表精确匹配
    - 根据 material_code 在 plm.alternative 中匹配 sap_no
    - 返回 bundling_number、root_description 字段
    - suspected_alternative_pn 设为空字符串
    - 支持一对多匹配（返回多条结果）
    - _Requirements: 3.1, 3.2, 3.3_
  
  - [x] 3.2 实现供应商PN码变体生成算法
    - 以"0"开头：原始值 + 去除一个"0" + 两者加"-*"后缀（"-"后仅一个字符）
    - 不以"0"开头：原始值 + 加"0"前缀 + 两者加"-*"后缀（"-"后仅一个字符）
    - _Requirements: 4.2, 4.3_
  
  - [x] 3.3 实现工厂物料清单模糊匹配
    - 使用供应商PN码变体在 industry_standard_desc 字段模糊匹配
    - 返回 sap_no、material_desc、industry_standard_desc 字段
    - 支持返回多条匹配结果
    - _Requirements: 4.1, 4.4, 4.5_
  
  - [x] 3.4 实现物料描述相似度匹配
    - 使用 difflib.SequenceMatcher 计算相似度
    - 相似度阈值 ≥90%
    - 返回所有符合条件的匹配结果
    - _Requirements: 5.1, 5.2, 5.3_
  
  - [x] 3.5 实现三级匹配流程编排
    - 按 PLM → 工厂清单 → 相似度 顺序执行
    - 任一级匹配成功则跳过后续匹配
    - 未匹配成功时保留原始数据，疑似替代字段为空
    - _Requirements: 6.1, 6.2, 5.4_

- [x] 4. 实现批量查询优化
  - [x] 4.1 实现批量匹配方法
    - 一次性提取所有物料代码、供应商PN码、物料描述
    - 批量查询 PLM 替代表和工厂物料清单
    - 在内存中进行匹配，避免 N+1 查询
    - _Requirements: 10.1_
  
  - [x] 4.2 实现相似度匹配预筛选优化
    - 提取关键词进行 SQL 预筛选
    - 仅对候选集计算完整相似度
    - _Requirements: 10.1_

- [x] 5. 实现导入接口和事务处理
  - [x] 5.1 创建 HTTP Controller
    - 创建 `FindAlternativeMaterialController` 类
    - 定义路由 `/find_alternative_material/import`
    - _Requirements: 2.1_
  
  - [x] 5.2 实现导入接口方法
    - 接收上传的 Excel 文件
    - 调用解析、去重、匹配方法
    - 使用 savepoint 实现事务回滚
    - 返回导入记录数量或错误信息
    - 自动触发匹配流程
    - _Requirements: 2.1, 2.5, 6.1, 11.1_
  
  - [x] 5.3 实现错误处理和日志记录
    - 捕获并处理各类异常（FileNotFoundError、ValueError、InvalidFileException等）
    - 记录导入开始、匹配过程、导入完成日志
    - 错误时记录详细日志（错误类型、错误信息、堆栈跟踪）
    - 向用户显示友好错误提示
    - _Requirements: 2.4, 10.3, 11.1, 11.2, 11.3_

- [x] 6. 实现导出功能
  - [x] 6.1 实现导出接口方法
    - 定义路由 `/find_alternative_material/export`
    - 根据筛选条件导出所有记录
    - 包含全部六个业务字段
    - _Requirements: 7.1, 7.2_
  
  - [x] 6.2 实现 Excel 样式设置
    - 表头行使用黄色背景（#FFFF00）
    - 冻结首行
    - 文件命名格式：`寻找替代料_{YYYYMMDD}.xlsx`
    - _Requirements: 7.3, 7.4_

- [-] 7. 创建视图和菜单
  - [x] 7.1 创建列表视图 XML
    - 展示六个业务字段
    - 区分已匹配和未匹配记录的显示样式
    - _Requirements: 6.3, 6.4_
  
  - [x] 7.2 创建搜索视图 XML
    - 支持按物料代码、物料描述、供应商PN码搜索
    - 支持按匹配状态筛选
    - _Requirements: 6.3_
  
  - [x] 7.3 创建 Action 和菜单项
    - 在"信创备件测算系统 > 数据审视"菜单下添加"寻找替代料"菜单项
    - 配置列表视图 Action
    - _Requirements: 9.1, 9.2_
  
  - [x] 7.4 添加导入导出按钮
    - 在列表视图工具栏添加"导入"按钮
    - 在列表视图工具栏添加"导出"按钮
    - _Requirements: 9.3_

- [-] 8. 配置权限和安全
  - [x] 8.1 创建权限组
    - 在 spare_parts_security.xml 中添加"备件测算导入权限"组（group_spare_parts_import）
    - _Requirements: 8.1_
  
  - [x] 8.2 配置模型访问权限
    - 在 ir.model.access.csv 中添加 find.alternative.material 的访问权限
    - 允许所有登录用户读取、导出
    - _Requirements: 8.4, 8.5_
  
  - [x] 8.3 实现导入按钮权限控制
    - 导入按钮仅对"备件测算导入权限"组成员可见
    - _Requirements: 8.2, 8.3_

- [x] 9. Checkpoint - 验证核心功能
  - 确保所有单元测试通过，如有问题请询问用户。

- [ ] 10. 编写单元测试
  - [ ] 10.1 测试数据模型字段定义
    - 验证模型字段定义正确
    - 验证索引创建成功
    - _Requirements: 1.1, 1.2_
  
  - [ ] 10.2 测试去重逻辑
    - 验证物料代码去重正确
    - 验证保留第一条记录
    - _Requirements: 2.3_
  
  - [ ] 10.3 测试 PLM 匹配逻辑
    - 验证精确匹配正确
    - 验证一对多匹配返回多条
    - 验证字段映射正确
    - _Requirements: 3.1, 3.2, 3.3_
  
  - [ ] 10.4 测试工厂清单模糊匹配
    - 验证"0"开头PN码变体生成
    - 验证非"0"开头PN码变体生成
    - 验证模糊匹配结果正确
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_
  
  - [ ] 10.5 测试相似度匹配
    - 验证相似度计算正确
    - 验证阈值≥90%过滤
    - _Requirements: 5.1, 5.2, 5.3_
  
  - [ ] 10.6 测试三级匹配优先级
    - 验证 PLM 匹配成功后跳过后续匹配
    - 验证工厂清单匹配成功后跳过相似度匹配
    - 验证匹配短路逻辑
    - _Requirements: 6.1, 6.2_

- [ ] 11. 编写属性测试
  - [ ]* 11.1 编写 Excel 导入去重属性测试
    - **Property 1: Excel导入数据去重**
    - **Validates: Requirements 2.3**
    - 验证去重后物料代码唯一性
  
  - [ ]* 11.2 编写 PLM 匹配优先级属性测试
    - **Property 2: PLM替代表精确匹配优先级**
    - **Validates: Requirements 3.1, 6.1, 6.2**
    - 验证 PLM 匹配存在时不执行后续匹配
  
  - [ ]* 11.3 编写 PLM 匹配字段映射属性测试
    - **Property 3: PLM匹配字段映射正确性**
    - **Validates: Requirements 3.2**
    - 验证字段映射正确性
  
  - [ ]* 11.4 编写供应商PN码变体属性测试
    - **Property 5: 供应商PN码"0"前缀变体匹配**
    - **Property 6: 供应商PN码非"0"前缀变体匹配**
    - **Validates: Requirements 4.2, 4.3**
    - 验证变体生成规则正确
  
  - [ ]* 11.5 编写相似度阈值属性测试
    - **Property 8: 相似度匹配阈值**
    - **Validates: Requirements 5.2**
    - 验证相似度≥90%
  
  - [ ]* 11.6 编写匹配短路属性测试
    - **Property 9: 匹配短路逻辑**
    - **Validates: Requirements 6.2**
    - 验证匹配成功后不执行后续匹配
  
  - [ ]* 11.7 编写事务回滚属性测试
    - **Property 11: 事务回滚一致性**
    - **Validates: Requirements 11.1**
    - 验证异常时数据库无部分数据

- [x] 12. Checkpoint - 最终验证
  - 确保所有测试通过，验证完整流程，如有问题请询问用户。

## Notes

- 任务标记 `*` 表示可选任务，可跳过以加快 MVP 开发
- 每个任务都引用了具体的需求条目，确保可追溯性
- 检查点确保增量验证
- 属性测试验证通用正确性属性
- 单元测试验证具体示例和边界情况
