# 实现计划：备件测算系统 v1322

## 概述

基于需求文档和设计文档，将7个需求拆分为增量式编码任务。任务按依赖关系排序：先完成权限组定义（需求7），再依次完成各模型字段新增、逻辑修改和视图更新。所有变更均在 `xc_addons/xc_spare_parts/` 模块内完成。

## 任务

- [x] 1. 新增延保成本核算权限组与ACL调整（需求7）
  - [x] 1.1 在 `spare_parts_security.xml` 中新增 `group_extended_warranty_user` 和 `group_extended_warranty_manager` 权限组
    - 在 `spare_parts_module_category` 分类下新增延保成本核算普通用户权限组（仅查看）
    - 新增延保成本核算管理员权限组，继承普通用户权限组（`implied_ids`），默认分配给 `base.user_root` 和 `base.user_admin`
    - _需求: 7.1, 7.2_
  - [x] 1.2 修改 `ir.model.access.csv` 中 `extended_warranty_base_data` 和 `asp_cost_per_visit` 的ACL
    - 将原 `base.group_user` 的两行替换为四行：普通用户只读(1,0,0,0)，管理员完整CRUD(1,1,1,1)
    - _需求: 7.3, 7.4, 7.5, 7.6, 7.7_
  - [ ]* 1.3 编写权限隔离属性测试
    - **Property 8: 延保成本核算权限隔离**
    - **验证: 需求 7.3, 7.4, 7.5, 7.6**

- [x] 2. PO与存量表新增 `industry_area` 字段（需求1 - 模型与导入部分）
  - [x] 2.1 在 `purchase_order_inventory.py` 中新增 `industry_area` ORM 字段
    - 新增 `industry_area = fields.Char(string="项目所属行业/区域")`
    - _需求: 1.1_
  - [x] 2.2 修改 `excel_import()` 方法支持17列导入
    - 列数校验从 `cols != 16` 改为 `cols != 17`
    - _需求: 1.1, 1.2_
  - [x] 2.3 修改 `get_excel_data()` 方法处理第17列（索引16）的 `industry_area` 数据
    - _需求: 1.1_
  - [x] 2.4 修改 INSERT SQL 语句，在字段列表和 ON CONFLICT DO UPDATE SET 中新增 `industry_area`
    - _需求: 1.1_
  - [x] 2.5 修改 `excel_export()` 方法，在 `sheet_fields` 和导出数据中新增"项目所属行业/区域"
    - _需求: 1.1_
  - [x] 2.6 修改 `purchasing_order_inventory_views.xml`，在 tree 视图和 search 视图中新增 `industry_area` 字段
    - _需求: 1.1_
  - [ ]* 2.7 编写Excel导入17列数据完整性属性测试
    - **Property 1: Excel导入17列数据完整性**
    - **验证: 需求 1.1**

- [x] 3. BOM总表新增 `industry_area` 字段及回退逻辑（需求1 - BOM总表部分 + 需求5 CRM逻辑）
  - [x] 3.1 在 `bom_total_table.py` 中新增 `industry_area` ORM 字段
    - 新增 `industry_area = fields.Char(string="项目所属行业/区域")`
    - _需求: 1.3_
  - [x] 3.2 修改 `refresh_bom_total()` 中的 `sql_v2` 查询，追加 `industry_area` 字段
    - 在 `sn_service_complete_info` 查询中增加 `max(industry_area) as industry_area`
    - 将 `industry_area` 存入 `sale_datas` 字典
    - _需求: 1.4_
  - [x] 3.3 在 `refresh_bom_total()` 遍历 `material_list` 构建 `result_list` 时实现 `industry_area` 三级回退逻辑
    - 优先取溯源系统值（非空且非"#N/A"），其次取PO与存量表值，最后为空字符串
    - _需求: 1.4, 1.5, 1.6_
  - [x] 3.4 重写 `refresh_bom_total()` 中的CRM立项编号获取逻辑为三级回退策略
    - 第一级：从 `sn_service_bom_info` 按项目名取 `crm_no`
    - 第二级：从 `sn_service_bom_info` 按增配整机项目名称取 `crm_no`
    - 第三级：从 `purchase_order_inventory` 按项目名取 `proj_number`
    - 替换现有的 `crm_datas` 相关逻辑
    - _需求: 5.1, 5.2, 5.3, 5.4_
  - [x] 3.5 修改 BOM总表 INSERT SQL，在字段列表中新增 `industry_area`
    - 同步修改 `bins_dict` 构建逻辑，加入 `industry_area` 键值
    - _需求: 1.3_
  - [x] 3.6 修改 `bom_total_table_views.xml`，在 tree 视图和 search 视图中新增 `industry_area` 字段
    - _需求: 1.3_
  - [x] 3.7 修改 BOM总表 `excel_export()` 方法，在 `sheet_fields` 和导出数据中新增"项目所属行业/区域"
    - _需求: 1.3_
  - [ ]* 3.8 编写 industry_area 三级回退优先级属性测试
    - **Property 2: industry_area 三级回退优先级**
    - **验证: 需求 1.4, 1.5, 1.6**
  - [ ]* 3.9 编写 CRM立项编号三级回退属性测试
    - **Property 6: CRM立项编号三级回退**
    - **验证: 需求 5.1, 5.2, 5.3, 5.4**

- [x] 4. 检查点 - 确保需求1/5/7的变更正确
  - 确保所有测试通过，如有疑问请询问用户。

- [x] 5. XC02/XC16/XC17库存取所有工厂汇总（需求2）
  - [x] 5.1 修改 `prepare_materials.py` 的 `search_sql()` 方法中 `addr_case` 构建逻辑
    - 移除 `factory_code` 限定，仅按 `stock_address` 过滤
    - 将 `"sum(CASE WHEN factory_code='" + address['stock'] + "' AND stock_address='" + address['name'] + "' ..."` 改为 `"sum(CASE WHEN stock_address='" + address['name'] + "' ..."`
    - _需求: 2.1, 2.2, 2.3_
  - [x] 5.2 修改 `alternative_prepare_materials.py` 的 `search_sql()` 方法中 `addr_case` 构建逻辑
    - 同样移除 `factory_code` 限定，仅按 `stock_address` 过滤
    - _需求: 2.4_
  - [ ]* 5.3 编写XC库存汇总不限定工厂属性测试
    - **Property 3: XC库存汇总不限定工厂**
    - **验证: 需求 2.1, 2.2, 2.3, 2.4, 2.5, 2.6**

- [x] 6. 过滤whbj虚拟城市（需求3）
  - [x] 6.1 修改 `prepare_materials.py` 的 `search_sql()` 方法中 `city_case` 构建逻辑
    - 在 `if c != '武汉':` 条件中增加 `and c != 'whbj'`
    - _需求: 3.1, 3.3_
  - [x] 6.2 修改 `alternative_prepare_materials.py` 的 `search_sql()` 方法中 `city_case` 构建逻辑
    - 同样增加 `and c != 'whbj'` 过滤条件
    - _需求: 3.2, 3.4_
  - [ ]* 6.3 编写whbj城市过滤属性测试
    - **Property 4: whbj城市过滤**
    - **验证: 需求 3.1, 3.2, 3.3, 3.4**

- [x] 7. 其他库区库存名称与编码调整（需求4）
  - [x] 7.1 修改 `other_reservoir_area_stock.py` 中的 `stock_params` 列表
    - 删除原有的"超时硬盘"、"武汉废品"、"武汉借用仓"、"维修在途"、"委外维修"5条记录
    - 保留"武汉测试仓"不变
    - 在原位置新增8条记录：武汉维修仓-测试在途(WHWXC-CSZT)、武汉维修仓-返厂在途(WHWXC-FCZT)、武汉环境仓(KCDBJ-WHHJC)、超时硬盘仓(KCDBJ-CSYPC)、武汉废品仓(KCDBJ-WHFPC)、待处理仓(KCDBJ-DCLC)、介质保留仓(KCDBJ-JZBLC)、武汉借用仓(KCDBJ-WHJYC)
    - _需求: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8, 4.9_
  - [x] 7.2 同步修改 `sheet_fields` 和 `city_fields` 列表中对应的城市名称
    - 移除旧名称，新增调整后的城市名称，保持与 `stock_params` 一致
    - _需求: 4.10_
  - [ ]* 7.3 编写 stock_params 映射完整性属性测试
    - **Property 5: stock_params映射完整性**
    - **验证: 需求 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8, 4.9, 4.10**

- [x] 8. SAP库存查询连接安全处理（需求6）
  - [x] 8.1 修改 `inventory_query.py` 的 `sync_inventory()` 方法
    - 在 `try` 块前将 `conn` 初始化为 `None`
    - 在 `sap_conn()` 调用后增加 `if not conn:` 判断，抛出 `UserError`
    - 将 `finally` 块中的 `conn.close()` 改为 `if conn: conn.close()`
    - _需求: 6.1, 6.2, 6.3_
  - [ ]* 8.2 编写SAP连接安全释放属性测试
    - **Property 7: SAP连接安全释放**
    - **验证: 需求 6.1, 6.2, 6.3**

- [x] 9. 最终检查点 - 确保所有变更正确
  - 确保所有测试通过，如有疑问请询问用户。

## 备注

- 标记 `*` 的任务为可选测试任务，可跳过以加快MVP进度
- 每个任务引用了具体的需求编号以确保可追溯性
- 检查点任务用于增量验证
- 属性测试验证设计文档中定义的通用正确性属性
- 单元测试验证具体示例和边界条件
