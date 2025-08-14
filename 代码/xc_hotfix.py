import pandas as pd
import psycopg2
import psycopg2.extras

def XcHotfix(A_and_C, replace_relationship):
    """
        A_and_c: A_and_C_columns_processed_split表格地址
        replace_relationship: 关系替换表格地址
    """
    # 读取A_and_C_columns_processed_split表格
    A_and_C_df = pd.read_excel(A_and_C, header=None)
    # 将A_and_C_columns_processed_split表格中的数据转化为字典列表，并去除所有空值
    A_and_C_dict_list = [{row[0]: [val for val in row[1:] if not pd.isna(val)]} for row in A_and_C_df.values]
    # 读取替代关系表格
    replace_relationship_df = pd.read_excel(replace_relationship)

    # 创建数据库连接
    # # 测试环境
    # connection = psycopg2.connect(
    #     host='10.0.23.146',
    #     port='54321',
    #     user='odoo',
    #     password='xctest$',
    #     dbname='xc-test'
    # )
    # 生产环境
    connection = psycopg2.connect(
            dbname="xc_materiel",
            user="xc",
            password="Dcxc7888$",
            host="10.0.23.199",
            port="5432"
        )
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    # 读取数据库compute_product_report中的数据
    # 定义 SQL 查询
    query = "SELECT * FROM compute_product_report"
    # 执行查询
    cursor.execute(query)
    # 获取所有结果
    compute_product_report_df = cursor.fetchall()

    # first_way = []
    # AC表中有单号没有sap号的数据存储到sap_isnull_list中，最后输出为excel
    sap_isnull_list = []
    not_replace_list = []
    ac_exist_com_not = []
    com_len_big_ac = []
    ac_len_big_com = []

    # 遍历A_and_C_columns_processed_split表格中的数据
    for row in A_and_C_dict_list:
        # 获取字典的键和值
        key = list(row.keys())
        value = list(row.values())[0]
        # 如果键是nan或者值是空列表，则跳过
        key = str(key[0]).replace(".0", "")
        if key == "nan" or key == "0":
            continue
        if not value:
            # AC表有工单号，没有物料号，生成一个无物料号的excel
            sap_isnull_list.append(key)
            continue
        # 在compute_product_report中查找name=key的所有行
        value_str = ';'.join(value)
        report_list = []
        report_key_list = []
        for report in compute_product_report_df:
            if report['name'] == key:
                # 将符合要求的行和“保修物料号”存在列表中
                report_list.append(report)
                report_key_list.append(report['gzjwlh'])
        # 系统里查不出工单号
        if not report_list:
            # AC表有工单号，系统没有，生成一个表
            ac_exist_com_not.append({
                "工单号": key,
                "物料号": value_str
            })
            continue
        # 比较value和report_key_list，找出不同的部分
        diff_list_ac = list(set(value) - set(report_key_list))
        diff_list_com = list(set(report_key_list) - set(value))
        # 如果diff_list_ac和diff_list_com都为空，则跳过
        if not diff_list_ac and not diff_list_com:
            # 第一种情况，AC表和系统中的数据一致，不需要替换
            # first_way.append(key)
            continue
        # 第二种情况，AC表和系统中的数据有不一致，需要在替代表中寻找替代
        else:
            # 遍历在系统中不在AC表中的sap号
            for dlc in diff_list_com:
                replace_list = []
                replace_sap_list = []
                replace_diff_ac = []
                # 遍历替代关系表，找到SAP NO等于当前sap的行
                for replace_row in replace_relationship_df.values:
                    if replace_row[1] == dlc:
                        replace_key = replace_row[0]
                        # 找出所用捆绑料号为replace_key的行
                        for x in replace_relationship_df.values:
                            if x[0] == replace_key:
                                # 将找到的行存到列表中,并将sap号存到列表中
                                replace_list.append(x)
                                replace_sap_list.append(x[1])
                        break
                # 遍历diff_list_ac，找出是否可以替代
                for dlac in diff_list_ac:
                    if dlac in replace_sap_list:
                        # 找到可以替代的行，将其替换为replace_key
                        sql = "UPDATE compute_product_report SET gzjwlh = %s WHERE name = %s AND gzjwlh = %s"
                        data = (dlac, key, dlc)
                        cursor.execute(sql, data)
                        connection.commit()
                    else:
                        # 第三种情况：AC表和系统中的数据有不一致，但没有替代关系，将这些信息输出为excel
                        # 找不到可以替代的sap，将ac中的sap号存在replace_diff_ac中
                        replace_diff_ac.append(dlac)
                if replace_diff_ac:
                    replace_diff_ac = ';'.join(replace_diff_ac)
                    for r in report_list:
                        if r['gzjwlh'] == dlc:
                            # 在r中添加一列replace_diff_ac
                            r['replace_diff_ac'] = replace_diff_ac
                            # 将r中的部分字段添加到not_replace_list中
                            not_replace_list.append({
                                'CRM工单号': r['name'],
                                '报修物料号': r['gzjwlh'],
                                '替换物料号': r['replace_diff_ac'],
                                '备件名称': r['bjmc'],
                            })
                            break
            if not diff_list_com and diff_list_ac:
                # AC表有不同的物料号，系统没有
                ac_len_big_com.append({
                    "工单号": key,
                    "物料号": value_str
                })

            if len(diff_list_com) > len(diff_list_ac):
                # 系统的物料号数量大于AC表
                com_len_big_ac.append({
                    "工单号": key,
                    "物料号": value_str
                })

    # 将sap_isnull_list和not_replace_list转化为dataframe，并输出到excel中
    # first_way_df = pd.DataFrame(first_way, columns=['工单号'])
    # sap_isnull_df = pd.DataFrame(sap_isnull_list, columns=['工单号'])
    not_replace_df = pd.DataFrame(not_replace_list, columns=resultCol)
    # ac_exist_com_not_df = pd.DataFrame(ac_exist_com_not, columns=['工单号', '物料号'])
    com_len_big_ac_df = pd.DataFrame(com_len_big_ac, columns=['工单号', '物料号'])
    # ac_len_big_com_df = pd.DataFrame(ac_len_big_com, columns=['工单号', '物料号'])

    # # 生成first_way_df的Excel文件
    # writer_first_way = pd.ExcelWriter(r"C:\Users\user\Desktop\AC表和系统数据一致.xlsx")
    # first_way_df.to_excel(writer_first_way, index=False)
    # writer_first_way.close()

    # # 生成sap_isnull_df的Excel文件
    # writer_sap_isnull = pd.ExcelWriter(r"C:\Users\user\Desktop\AC表SAP号为空.xlsx")
    # sap_isnull_df.to_excel(writer_sap_isnull, index=False)
    # writer_sap_isnull.close()

    # 生成not_replace_df的Excel文件
    writer_not_replace = pd.ExcelWriter(r"C:\Users\user\Desktop\替代关系未找到.xlsx")
    not_replace_df.to_excel(writer_not_replace, index=False)
    writer_not_replace.close()

    # # 生成ac_exist_com_not_df的Excel文件
    # writer_ac_exist_com_not = pd.ExcelWriter(r"C:\Users\user\Desktop\AC有工单号但系统没有.xlsx")
    # ac_exist_com_not_df.to_excel(writer_ac_exist_com_not, index=False)
    # writer_ac_exist_com_not.close()

    # 生成com_len_big_ac_df的Excel文件
    writer_com_len_big_ac = pd.ExcelWriter(r"C:\Users\user\Desktop\BCM中物料号数量大于CRM.xlsx")
    com_len_big_ac_df.to_excel(writer_com_len_big_ac, index=False)
    writer_com_len_big_ac.close()

    # # 生成ac_len_big_com_df的Excel文件
    # writer_ac_len_big_com = pd.ExcelWriter(r"C:\Users\user\Desktop\AC物料号数量大于系统.xlsx")
    # ac_len_big_com_df.to_excel(writer_ac_len_big_com, index=False)
    # writer_ac_len_big_com.close()

    # 关闭数据库连接
    cursor.close()
    connection.close()


# 去除AC表中相同情况和sap号不存在的行
def remove_same_sap(A_and_C, first_way_path, sap_isnull_path):
    # 读取AC表
    A_and_C_df = pd.read_excel(A_and_C, header=None)
    # 读取first_way_path中的工单号
    first_way_df = pd.read_excel(first_way_path)
    # 读取sap_isnull_path中的工单号
    sap_isnull_df = pd.read_excel(sap_isnull_path)
    # 去除first_way_df中的工单号
    A_and_C_df = A_and_C_df[~A_and_C_df[0].isin(first_way_df['工单号'])]
    # 去除sap_isnull_df中的工单号
    A_and_C_df = A_and_C_df[~A_and_C_df[0].isin(sap_isnull_df['工单号'])]
    # 输出结果到excel中
    writer = pd.ExcelWriter(r"C:\Users\user\Desktop\AC表去除重复.xlsx")
    A_and_C_df.to_excel(writer, index=False)
    writer.close()




resultCol = ['CRM工单号', '报修物料号', '替换物料号', '备件名称']
# resultCol = ['CRM工单号', '报修时间', '换件单号', '工单状态', '报修物料号', '备件名称', '备件物料号', '返回件物料号', '备件SN',
#              '备件派件时间', '备件签收时间', '派件方式', '是否超时', '派件费用', '备件出库地', '故障现象（客户报）', '返回件sn',
#              '旧件返回快递', '旧件收件时间', '故障件交接测试时间', '故障现象（实测）', '测试结论', '复测处理完成时间', '供应商',
#              '返厂快递', '返厂时间', 'TAT', '修复件返回快递', '修复件收件时间', '修复件物料号', '修复件SN', '修复件入库时间',
#              '类别', '机型', 'SLA', '服务开始时间', '整机SN', '项目名称', 'CRM立项编号', '客户信息', '负责人', '旧件返回对接人'
#              '备注', '维修单号', '特殊状态', '处理方式', '产品使用天数']


if __name__ == '__main__':
    # 定义表格地址
    A_and_C = r"C:\Users\user\Desktop\A_and_C_columns_processed_split.xlsx"
    # A_and_C = r"C:\Users\user\Desktop\AC表去除重复.xlsx"
    replace_relationship = r"C:\Users\user\Desktop\捆绑料号神州一诺版-24.08.09-已发布.xlsx"

    # 按照AC表和替代关系表 处理系统数据
    XcHotfix(A_and_C, replace_relationship)

    # first_way_path = r"C:\Users\user\Desktop\AC表和系统数据一致.xlsx"
    # sap_isnull_path = r"C:\Users\user\Desktop\AC表SAP号为空.xlsx"
    # 去除AC表中相同情况和sap号不存在的行
    # remove_same_sap(A_and_C, first_way_path, sap_isnull_path)
