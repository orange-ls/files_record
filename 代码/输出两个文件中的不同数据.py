import pandas as pd

# 读取两个Excel文件
df1 = pd.read_excel(r'C:\Users\user\Desktop\下单费用1756803818.xlsx', dtype=str)
df2 = pd.read_excel(r'C:\Users\user\Desktop\下单费用1756976176.xlsx', dtype=str)

# 检查列名是否一致
if list(df1.columns) != list(df2.columns):
    raise ValueError("错误：两个文件的列不一致")

# 使用merge方法标记数据来源
merged_df = df1.merge(df2,
                      on=df1.columns.tolist(),
                      how='left',
                      indicator=True)

# 筛选出仅存在于一个文件中的数据
diff_df = merged_df[merged_df['_merge'] != 'both']

# 删除辅助列并保存结果
diff_df.drop('_merge', axis=1).to_excel(r'D:\Workspace\差异结果.xlsx', index=False)

print("比较完成，差异已保存到 差异结果.xlsx")
