'''
    数据重复检查脚本
'''
import pandas as pd

# 读取Excel文件（替换为你的文件路径）
input_path = "C:\\Users\\user\\Desktop\\123.xlsx"
output_path = "C:\\Users\\user\\Desktop\\重复数据.xlsx"

# 定义唯一标识列
key_columns = [
    "id"
]

# 读取数据
# df = pd.read_excel(input_path, sheet_name="2025年产品专项", header=1)
df = pd.read_excel(input_path)

# 找出所有重复行（保留所有重复实例）
duplicates = df[df.duplicated(subset=key_columns, keep=False)]

# 按关键字段排序以便查看
duplicates_sorted = duplicates.sort_values(by=key_columns)

if len(duplicates_sorted) != 0:
    # 保存结果到新文件
    duplicates_sorted.to_excel(output_path, index=False)

print(f"找到 {len(duplicates)} 条重复数据，已保存到 {output_path}")
