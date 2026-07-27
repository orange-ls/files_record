# 需求文档

## 简介

本需求文档描述备件测算系统（xc_spare_parts）v1322版本的功能优化与缺陷修复，涵盖7个需求点：新增"项目所属行业/区域"字段、XC库存汇总逻辑调整、whbj虚拟城市过滤、其他库区库存名称与编码调整、BOM总表CRM立项编号抓取逻辑优化、SAP库存查询连接安全处理、延保成本核算导入权限控制。

## 术语表

- **PO与存量表（PurchaseOrdersInventory）**：模型 `purchase.order.inventory`，用于管理PO单与存量数据的Excel导入和存储
- **BOM总表（BomTotalTable）**：模型 `bom.total.table`，汇总物料BOM展开后的总表数据
- **备料总表（PrepareMaterials）**：模型 `prepare.materials`，按城市维度计算物料备货量、库存量、缺口等
- **替代料备料总表（AlternativePrepareMaterials）**：模型 `alternative.prepare.materials`，按捆绑料号维度计算替代料备货数据
- **本周项目测算（WeekEstimates）**：模型 `week.estimates`，展示本周项目的物料测算数据
- **汇总看板（SummaryKanban）**：模型 `summary.kanban`，汇总展示项目维度的备件数据看板
- **其他库区库存（OtherReservoirAreaStock）**：模型 `other.reservoir.area.stock`，管理WMS各库房的库存数据
- **SAP库存查询（InventoryQuery）**：模型 `inventory.query`，从SAP系统同步并查询物料库存
- **延保核算基础数据（ExtendedWarrantyBaseData）**：模型 `extended.warranty.base.data`，延保成本核算的基础参数配置
- **ASP上门成本基础数据表（AspCostPerVisit）**：模型 `asp.cost.per.visit`，ASP工程师上门成本基础数据
- **溯源系统**：存储服务器整机信息、BOM组件信息、SN服务完整信息的数据源系统
- **stock_addresses**：鲲鹏日报中定义的库存地址配置列表，包含XC02（MHMU工厂）、XC16（MHMU工厂）、XC17（MH48工厂）
- **stock_params**：其他库区库存中定义的WMS库房编码与城市名称的映射配置列表
- **city_fields**：其他库区库存中定义的城市字段列表，用于数据透视展示
- **whbj**：库存报表中的一个库存汇总合计字段，非实际城市名称
- **conn**：SAP RFC连接对象，由 `sap_conn()` 方法创建，用于调用SAP远程函数

## 需求

### 需求1：PO与存量表及BOM总表新增"项目所属行业/区域"字段

**用户故事：** 作为备件管理员，我希望在PO与存量表和BOM总表中增加"项目所属行业/区域"字段，以便按行业/区域维度分析备件数据。

#### 验收标准

1. WHEN 通过Excel导入PO与存量数据时，THE PurchaseOrdersInventory SHALL 支持解析Excel中的"项目所属行业/区域"列，并将该值存储到 `purchase_order_inventory` 表的 `industry_area` 字段中
2. WHEN Excel模板列数不包含"项目所属行业/区域"列时，THE PurchaseOrdersInventory SHALL 返回模板格式错误提示
3. THE BomTotalTable SHALL 包含 `industry_area` 字段，用于存储项目所属行业/区域信息
4. WHEN 刷新BOM总表数据时，THE BomTotalTable SHALL 优先按项目名从溯源系统的服务器整机存量表（`sn_service_complete_info`）中抓取"项目所属行业/区域"值
5. WHEN 溯源系统服务器整机存量表中对应项目名的"项目所属行业/区域"为空或为"#N/A"时，THE BomTotalTable SHALL 取PO与存量表（`purchase_order_inventory`）中对应项目名的 `industry_area` 值作为回退
6. WHEN PO与存量表中对应项目名的 `industry_area` 也为空时，THE BomTotalTable SHALL 将该记录的 `industry_area` 字段设置为空字符串

### 需求2：XC02/XC16/XC17库存取所有工厂汇总

**用户故事：** 作为备件管理员，我希望备料总表、替代料备料总表、本周项目测算、汇总看板中涉及XC02、XC16、XC17库存的数据取各个工厂所有XC02、XC16、XC17库存汇总，以便获得更准确的库存全貌。

#### 验收标准

1. WHEN 备料总表查询XC02库存时，THE PrepareMaterials SHALL 汇总所有工厂中库存地址为XC02的库存数量，不再限定特定工厂
2. WHEN 备料总表查询XC16库存时，THE PrepareMaterials SHALL 汇总所有工厂中库存地址为XC16的库存数量，不再限定特定工厂
3. WHEN 备料总表查询XC17库存时，THE PrepareMaterials SHALL 汇总所有工厂中库存地址为XC17的库存数量，不再限定特定工厂
4. WHEN 替代料备料总表查询XC02、XC16、XC17库存时，THE AlternativePrepareMaterials SHALL 汇总所有工厂中对应库存地址的库存数量，不再限定特定工厂
5. WHEN 本周项目测算查询XC02、XC16、XC17库存时，THE WeekEstimates SHALL 汇总所有工厂中对应库存地址的库存数量，不再限定特定工厂
6. WHEN 汇总看板同步数据时，THE SummaryKanban SHALL 使用汇总所有工厂的XC02、XC16、XC17库存数量，不再限定特定工厂

### 需求3：过滤whbj虚拟城市

**用户故事：** 作为备件管理员，我希望备料总表和替代料备料总表中不展示whbj这个虚拟城市行，因为whbj只是库存报表中的一个汇总合计字段，不是实际城市。

#### 验收标准

1. THE PrepareMaterials SHALL 在查询结果中排除城市字段值为"whbj"的数据行
2. THE AlternativePrepareMaterials SHALL 在查询结果中排除城市字段值为"whbj"的数据行
3. WHEN 备料总表的城市列表（city_fields）中包含"whbj"时，THE PrepareMaterials SHALL 在SQL查询的城市值集合构建中过滤掉"whbj"
4. WHEN 替代料备料总表的城市列表（city_fields）中包含"whbj"时，THE AlternativePrepareMaterials SHALL 在SQL查询的城市值集合构建中过滤掉"whbj"

### 需求4：其他库区库存名称与编码调整

**用户故事：** 作为备件管理员，我希望调整其他库区库存中的库存名和WMS库房编码映射关系，以便与实际仓库配置保持一致。

#### 验收标准

1. THE OtherReservoirAreaStock SHALL 将原"超时硬盘"库存名调整为"武汉维修仓-测试在途"，对应WMS库房编码为"WHWXC-CSZT"
2. THE OtherReservoirAreaStock SHALL 将原"武汉废品"库存名调整为"武汉维修仓-返厂在途"，对应WMS库房编码为"WHWXC-FCZT"
3. THE OtherReservoirAreaStock SHALL 将原"维修在途"库存名调整为"武汉环境仓"，对应WMS库房编码为"KCDBJ-WHHJC"
4. THE OtherReservoirAreaStock SHALL 将原"委外维修"库存名调整为"超时硬盘仓"，对应WMS库房编码为"KCDBJ-CSYPC"
5. THE OtherReservoirAreaStock SHALL 将原"武汉借用仓"库存名调整为"武汉废品仓"，对应WMS库房编码为"KCDBJ-WHFPC"
6. THE OtherReservoirAreaStock SHALL 保留"武汉测试仓"库存名不变，对应WMS库房编码为"KCDBJ-WHCSC"
7. THE OtherReservoirAreaStock SHALL 新增"待处理仓"库存名，对应WMS库房编码为"KCDBJ-DCLC"
8. THE OtherReservoirAreaStock SHALL 新增"介质保留仓"库存名，对应WMS库房编码为"KCDBJ-JZBLC"
9. THE OtherReservoirAreaStock SHALL 新增"武汉借用仓"库存名，对应WMS库房编码为"KCDBJ-WHJYC"
10. WHEN 同步WMS库存数据时，THE OtherReservoirAreaStock SHALL 使用调整后的库存名与WMS库房编码映射关系进行数据匹配

### 需求5：BOM总表CRM立项编号抓取逻辑调整

**用户故事：** 作为备件管理员，我希望BOM总表的CRM立项编号抓取逻辑更加完善，通过多级回退策略确保尽可能获取到CRM立项编号。

#### 验收标准

1. WHEN 刷新BOM总表数据时，THE BomTotalTable SHALL 优先从溯源系统的服务器BOM组件信息表（`sn_service_bom_info`）中按项目名查找对应的CRM立项编号
2. WHEN 溯源系统BOM组件信息表中项目名对应的CRM立项编号为空时，THE BomTotalTable SHALL 从溯源系统BOM组件信息表中按增配整机项目名称（`add_crm_no`对应的项目名）查找CRM立项编号
3. WHEN 溯源系统BOM组件信息表中项目名和增配整机项目名称对应的CRM立项编号均为空时，THE BomTotalTable SHALL 从测算系统PO与存量表（`purchase_order_inventory`）中按项目名查找对应的CRM立项编号（`proj_number`字段）
4. WHEN 三级查找均未获取到CRM立项编号时，THE BomTotalTable SHALL 将该记录的 `proj_number` 字段保留为空字符串

### 需求6：SAP库存查询连接安全处理

**用户故事：** 作为系统运维人员，我希望SAP库存查询在连接对象为空时不会因调用 `conn.close()` 而报错，以提高系统稳定性。

#### 验收标准

1. WHEN SAP连接对象（conn）为空（None）时，THE InventoryQuery SHALL 在 `finally` 块中跳过 `conn.close()` 调用，避免抛出 `AttributeError` 异常
2. WHEN SAP连接对象（conn）创建成功时，THE InventoryQuery SHALL 在 `finally` 块中正常调用 `conn.close()` 释放连接资源
3. THE InventoryQuery SHALL 在 `sync_inventory` 方法中将 `conn` 变量初始化为 `None`，确保在 `sap_conn()` 调用失败时 `finally` 块能安全执行

### 需求7：延保成本核算导入权限控制

**用户故事：** 作为系统管理员，我希望对延保核算基础数据表和ASP上门成本基础数据表增加导入权限控制，确保只有管理员角色才能执行导入操作，普通用户只能查看数据。

#### 验收标准

1. THE 备件测算系统 SHALL 新增延保成本核算管理员权限组（`group_extended_warranty_manager`），隶属于备件测算系统模块分类
2. THE 备件测算系统 SHALL 新增延保成本核算普通用户权限组（`group_extended_warranty_user`），隶属于备件测算系统模块分类
3. WHILE 用户属于延保成本核算普通用户权限组时，THE ExtendedWarrantyBaseData SHALL 仅允许该用户对数据进行读取操作
4. WHILE 用户属于延保成本核算管理员权限组时，THE ExtendedWarrantyBaseData SHALL 允许该用户对数据进行读取、创建、修改和删除操作
5. WHILE 用户属于延保成本核算普通用户权限组时，THE AspCostPerVisit SHALL 仅允许该用户对数据进行读取操作
6. WHILE 用户属于延保成本核算管理员权限组时，THE AspCostPerVisit SHALL 允许该用户对数据进行读取、创建、修改和删除操作
7. THE 备件测算系统 SHALL 将 `extended_warranty_base_data` 和 `asp_cost_per_visit` 模型的权限从 `base.group_user` 调整为新建的延保成本核算权限组
