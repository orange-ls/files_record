'''
    1、给定一个xlsx文件路径，简称表格路径。”备货-销售差异“sheet中，表头A到E列分别是：CRM立项编号、项目名称、项目行业一级、销售员、创建时间。
    2、给定一个文件夹路径，简称文件夹路径。文件夹下的每个表名都是{CRM立项编号}_{项目名称}.xlsx，”备货-销售差异汇总“的sheet中，表头A到E列分别是：物料代码、物料名称、备货总数量、销售总数量、差异(备货-销售)。
    3、读取表格路径的数据，提取出{CRM立项编号}_{项目名称}，并按这个提取的结果在文件夹路径中找出这个名称的xlsx文件。
    4、如果找不到就添加到列表中并在执行结束时print；
    5、如果找到对应的xlsx文件，读取他的”备货-销售差异汇总“的sheet数据，拼接为：CRM立项编号、项目名称、项目行业一级、销售员、创建时间、物料代码、物料名称、备货总数量、销售总数量、差异(备货-销售)。最后输出这一份结果表
'''

import os
import sys
import pandas as pd


def merge_stocking_sales_variance(table_path, folder_path):
    """读取备货-销售差异总表，匹配文件夹中的项目明细表，合并输出结果。

    Args:
        table_path: 包含"备货-销售差异"sheet的xlsx文件路径
        folder_path: 包含各项目{xCRM立项编号}_{项目名称}.xlsx文件的文件夹路径
    """
    # 1. 读取总表
    main_cols = ['CRM立项编号', '项目名称', '项目行业一级', '销售员', '创建时间']
    df_main = pd.read_excel(table_path, sheet_name='备货-销售差异', usecols='A:E', dtype=str)
    df_main.columns = main_cols

    not_found = []
    result_frames = []

    detail_cols = ['物料代码', '物料名称', '备货总数量', '销售总数量', '差异(备货-销售)']

    for _, row in df_main.iterrows():
        crm_id = str(row['CRM立项编号']).strip()
        project_name = str(row['项目名称']).strip()
        file_name = f"{crm_id}_{project_name}.xlsx"
        file_path = os.path.join(folder_path, file_name)

        if not os.path.isfile(file_path):
            not_found.append(file_name)
            continue

        # 2. 读取项目明细表
        try:
            df_detail = pd.read_excel(file_path, sheet_name='备货-销售差异汇总', usecols='A:E', dtype=str)
            df_detail.columns = detail_cols
        except Exception as e:
            print(f"读取文件 {file_name} 失败: {e}")
            not_found.append(file_name)
            continue

        # 3. 拼接主表字段到每一行明细
        for col in main_cols:
            df_detail[col] = row[col]

        # 重新排列列顺序
        df_detail = df_detail[main_cols + detail_cols]
        result_frames.append(df_detail)

    # 4. 输出未找到的文件列表
    if not_found:
        print("以下项目文件未找到或读取失败：")
        for f in not_found:
            print(f"  {f}")

    # 5. 合并并输出结果
    if result_frames:
        df_result = pd.concat(result_frames, ignore_index=True)
        output_path = os.path.join(os.path.dirname(table_path), '合并结果_备货销售差异.xlsx')
        df_result.to_excel(output_path, index=False, sheet_name='合并结果')
        print(f"合并完成，结果已保存至: {output_path}")
        print(f"共合并 {len(result_frames)} 个项目，{len(df_result)} 条记录")
        return df_result
    else:
        print("未找到任何可合并的项目文件")
        return pd.DataFrame()


if __name__ == '__main__':
    # if len(sys.argv) < 3:
    #     print("用法: python merge_stocking_sales_variance.py <表格路径> <文件夹路径>")
    #     sys.exit(1)
    #
    # table_path = sys.argv[1]
    # folder_path = sys.argv[2]
    table_path = r'D:\文件\备货销售差异\备货-销售差异\备货-销售差异_20260415144721.xlsx'
    folder_path = r'D:\文件\备货销售差异\备货-销售差异\details'

    if not os.path.isfile(table_path):
        print(f"表格文件不存在: {table_path}")
        sys.exit(1)
    if not os.path.isdir(folder_path):
        print(f"文件夹不存在: {folder_path}")
        sys.exit(1)

    merge_stocking_sales_variance(table_path, folder_path)
