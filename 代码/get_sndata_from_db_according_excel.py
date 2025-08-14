'''
    读取excel表格，
    根据表格中的“项目名”和“CRM立项编号”列为键，
    在数据库-sn_service_complete_info 中获取对应的'服务产品类别(内部)', '所在城市', '推送标识', '产品交付时间'
'''
import pandas as pd
import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_values


def get_db_connection():
    """创建PostgreSQL数据库连接"""
    try:
        # # 测试环境
        # conn = psycopg2.connect(
        #     host='10.0.23.146',
        #     port='54321',
        #     user='odoo',
        #     password='xctest$',
        #     dbname='xc-test'
        # )

        # 生产环境
        conn = psycopg2.connect(
            dbname="xc_materiel",
            user="xc",
            password="Dcxc7888$",
            host="10.0.23.199",
            port="5432"
        )
        return conn
    except Exception as e:
        print(f"数据库连接失败：{str(e)}")
        return None


def fetch_data_from_db(project_keys):
    """使用IN条件从数据库批量查询数据"""
    if not project_keys:
        return {}

    data_dict = {}

    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # 构建查询参数（元组列表）
            query_args = [(name, crm_id) for name, crm_id in project_keys]

            # 使用参数化查询防止SQL注入
            query = sql.SQL("""
                SELECT 
                    proj_name,
                    crm_no,
                    service_product_type,
                    city,
                    push_flag,
                    deliver_time
                FROM sn_service_complete_info
                WHERE (proj_name, crm_no) IN %s
            """)

            # 执行查询
            cursor.execute(query, (tuple(query_args),))

            # 处理结果
            for row in cursor.fetchall():
                key = (row[0], row[1])  # project_name, crm_id
                data_dict[key] = {
                    '服务产品类别(内部)': row[2],
                    '所在城市': row[3],
                    '推送标识': row[4],
                    '产品交付时间': row[5].strftime('%Y-%m') if row[5] else ''
                }
        return data_dict
    except Exception as e:
        print(f"数据库查询失败：{str(e)}")
        return {}
    finally:
        if conn:
            conn.close()


def process_excel_with_db(input_file, output_file):
    """主处理函数（与之前保持相同）"""
    """带数据库查询的Excel处理"""
    try:
        df = pd.read_excel(input_file)
    except Exception as e:
        print(f"读取Excel失败：{str(e)}")
        return

    # 验证必要列
    required_columns = ['项目名', 'CRM立项编号']
    for col in required_columns:
        if col not in df.columns:
            print(f"缺少必要列：{col}")
            return

    # 获取所有唯一键值对
    project_keys = df[['项目名', 'CRM立项编号']].drop_duplicates().itertuples(index=False, name=None)

    # 从数据库获取数据字典
    data_dict = fetch_data_from_db(project_keys)

    # 添加新列
    new_columns = ['服务产品类别(内部)', '所在城市', '推送标识', '产品交付时间']
    for col in new_columns:
        df[col] = df.get(col, '')  # 保留已有数据

    # 填充数据
    for index, row in df.iterrows():
        key = (row['项目名'], row['CRM立项编号'])
        if key in data_dict:
            for col in new_columns:
                df.at[index, col] = data_dict[key].get(col, row.get(col, ''))

    # 保存结果
    try:
        df.to_excel(output_file, index=False)
        print(f"处理完成，保存到：{output_file}")
    except Exception as e:
        print(f"保存文件失败：{str(e)}")


# 使用示例
if __name__ == "__main__":
    process_excel_with_db(
        input_file=r'C:\Users\user\Desktop\需测算项目-250527.xlsx',
        output_file=r'C:\Users\user\Desktop\结果.xlsx'
    )

