import psycopg2
import pandas as pd

# 读取 Excel 文件
df = pd.read_excel(r'C:\Users\user\Desktop\我部门的通话_20250101000000_20250331235959_T47To(1)(1)(1).xlsx', engine='openpyxl', dtype=str, na_filter=False)

data_tuples = [tuple(None if str(r).strip() in ['', 'nan'] else str(r).strip() for r in row) for row in df.values.tolist()]

# 测试环境
connection = psycopg2.connect(
    host='10.0.23.146',
    port='54321',
    user='odoo',
    password='xctest$',
    dbname='xc-test'
)
# # 生产环境
# connection = psycopg2.connect(
#     dbname="xc_materiel",
#     user="xc",
#     password="Dcxc7888$",
#     host="10.0.23.199",
#     port="5432"
# )

cursor = connection.cursor()

insert_sql = """
INSERT INTO call_log_report (
   start_time,call_type,screen_number,belong_agent_id,belong_agent_name,
   total_duration,call_result,customer_nick,satisfy_result,call_id,
   alert_time,alert_duration,first_group_id
) VALUES
""" + ','.join(str(dt).replace('None', 'NULL') for dt in data_tuples)

cursor.execute(insert_sql)
connection.commit()

cursor.close()
connection.close()


