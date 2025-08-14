import hashlib
import requests
import time

def generate_md5_signature(params, app_secret):
    """
    根据文档生成 MD5 签名
    """
    builder = app_secret
    for key in sorted(params.keys()):  # 按字母排序参数
        builder += f"{key}{params[key]}"
    builder += app_secret
    md5 = hashlib.md5(builder.encode('utf-8')).hexdigest().upper()
    return md5

def create_transfer_order(base_url, app_key, app_secret, subapp_key, partner_id, cust_id, order_data):
    """
    调用转储单创建接口的方法
    """
    # 准备公共参数
    timestamp = str(int(time.time() * 1000))  # 毫秒级时间戳
    version = "1.0"
    method = "CreateTransSwitch"

    # 请求参数
    params = {
        "app_key": app_key,
        "timestamp": timestamp,
        "subappkey": subapp_key,
        "version": version,
        "method": method,
        "content": order_data
    }

    # 生成签名
    sign = generate_md5_signature(params, app_secret)
    params["sign"] = sign

    # 发起请求
    headers = {"Content-Type": "application/json"}
    response = requests.post(base_url, json=params, headers=headers)

    # 返回结果
    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()

# 示例调用
if __name__ == "__main__":
    # 基础信息
    BASE_URL = "http://111.203.122.88:8081/busapi/api/stdapi"  # 接口地址
    APP_KEY = "Digitchalchina"
    APP_SECRET = "123456"
    SUBAPP_KEY = "BCMKJD"
    PARTNER_ID = "SZKT"
    CUST_ID = "1200004260"

    # 示例订单数据（JSON格式）
    order_data = {
        "partnerId": PARTNER_ID,
        "custId": CUST_ID,
        "sCustId": CUST_ID,
        "tCustId": CUST_ID,
        "orderCode": "1231245234222",
        "orderType": "KNZC",
        "transferReason": "物权转移",
        "remark": "测试备注"
    }

    try:
        result = create_transfer_order(BASE_URL, APP_KEY, APP_SECRET, SUBAPP_KEY, PARTNER_ID, CUST_ID, order_data)
        print("接口调用成功，返回结果：", result)
    except Exception as e:
        print("接口调用失败：", e)