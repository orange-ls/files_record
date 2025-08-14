# 传入两个excel表格，按A列，找出表2有表1没有的数据
import pandas as pd


def find_missing_data(file1, file2, output_file=r'C:\Users\user\Desktop\result.xlsx'):
    """
    比较两个Excel文件，找出表2中存在但表1中不存在的数据（基于A列）

    参数:
    file1 (str): 第一个Excel文件路径
    file2 (str): 第二个Excel文件路径
    output_file (str): 结果输出文件路径（默认'result.xlsx'）
    """
    try:
        # 读取Excel文件（默认读取第一个sheet）
        df1 = pd.read_excel(file1)
        df2 = pd.read_excel(file2)

        # 获取A列数据（自动处理列名大小写和空格）
        col_name = df1.columns[0]  # 默认第一个列名
        for df in [df1, df2]:
            # 查找不区分大小写和空格的列名
            possible_cols = [col for col in df.columns
                             if col.strip().lower() == 'a']
            if possible_cols:
                col_name = possible_cols[0]

        # 提取A列唯一值
        df1_values = set(df1[col_name].dropna().astype(str).unique())
        df2_values = set(df2[col_name].dropna().astype(str).unique())

        # 找出表2有表1没有的值
        unique_to_df2 = df2_values - df1_values

        # 筛选表2中独有的数据行
        result = df2[df2[col_name].astype(str).isin(unique_to_df2)]

        # 保存结果
        result.to_excel(output_file, index=False)
        print(f"操作成功！共找到 {len(result)} 条差异数据")
        print(f"结果已保存至: {output_file}")

        return result

    except Exception as e:
        print(f"发生错误: {str(e)}")
        return None


# 使用示例
if __name__ == "__main__":
    # 替换为你的实际文件路径
    file1_path = r"C:\Users\user\Desktop\25年业绩表.xlsx"
    file2_path = r"C:\Users\user\Desktop\25年数据_result.xlsx"

    find_missing_data(file1_path, file2_path)