import cpca

# 示例地址列表
# addresses = ["迪庆藏族自治州", "广西壮族自治区", "1", "贵州省", "湖南省", "北京市","2","贵州省"]
addresses = ["大铲岛","黄埔","加格达奇站"]

# 获取多个地址的省市区信息
result = cpca.transform(addresses)

# 提取省份列
provinces = result['省'].values

# 将dataframe转化为list
provinces = provinces.tolist()

# 将addresses列表和provinces列表合并成字典
province_dict = dict(zip(addresses, provinces))

# 打印省份字典
print(province_dict)
#
# if not provinces:
#     print("未找到匹配的省份信息")
#
#
# # 打印省份列表
# print(provinces)