import requests
import hashlib
import json
import time

def create_signature(appkey, subappkey, version, method, body, appSecret):
    # 获取时间戳
    timestamp = str(int(time.time() * 1000))  # 毫秒时间戳
    
    # 拼接加密字符串
    abc = appSecret + "app_key" + appkey + "customerId" + subappkey + "formatjson" + "method" + method + \
          "sign_methodMD5" + "timestamp" + timestamp + "v" + version
    
    # 加密字符串拼接
    md5_str = abc + body + appSecret
    
    # 进行 MD5 加密并转化为大写
    md5_hash = hashlib.md5(md5_str.encode('utf-8')).hexdigest().upper()
    
    return md5_hash, timestamp

def send_request():
    # 设定请求头部参数
    appkey = "Digitchalchina"
    subappkey = "BCMKJD"
    version = "1.0"
    method = "CreateTransSwitch"
    appSecret = "123456"

    # 请求体内容
    # body = json.dumps({
    #     "partnerId": "chint",
    #     "custId": "CSGCH1001",
    #     "sCustId": "CSGCH1001",
    #     "tCustId": "CSGCH1001",
    #     "orderCode": "ZC012601",
    #     "orderType": "QMZC01",
    #     "cancelFlag": "",
    #     "orderSource": "1",
    #     "transferReason": "",
    #     "remark": "",
    #     "items": [
    #         {
    #             "item": "1",
    #             "materialIdF": "170000319511",
    #             "materialIdT": "170000319511",
    #             "qty": "2",
    #             "stockIdF": "CSKCD1001",
    #             "stockIdT": "CSKCD1001",
    #             "batchCodeF": "",
    #             "batchCodeT": "",
    #             "materialQualityF": "0",
    #             "materialQualityT": "0",
    #             "materialStateF": "A",
    #             "materialStateT": "A"
    #         }
    #     ]
    # })
    body = json.dumps(
        {
            "partnerId": "KTadmin",
            "custId": "1200004260",
            "sCustId": "1200004260",
            "tCustId": "1200004260",
            "orderCode": "KJ2025011509",
            "orderType": "KJD",
            "remark": "",
            "transFlag": "2",
            "items": [
                {
                    "item": "",
                    "materialIdF": "000000000302001332",
                    "materialIdT": "000000000302001332",
                    "qty": "1",
                    "stockIdF": "KCDBJ-WHBJC",
                    "stockIdT": "KCDBJ-BJBJC",
                    "batchCodeF": "",
                    "batchCodeT": "",
                    "proDateF": "",
                    "proDateT": "",
                    "expDateF": "",
                    "expDateT": "",
                    "materialQualityF": "0",
                    "materialQualityT": "0",
                    "materialStateF": "A",
                    "materialStateT": "A",
                    "batch1F": "",
                    "batch1T": "",
                    "batch2F": "",
                    "batch2T": "",
                    "batch3F": "",
                    "batch3T": "",
                    "batch4F": "",
                    "batch4T": "",
                    "batch5F": "",
                    "batch5T": ""
                }
            ]
        }
    )

    # 生成签名和时间戳
    signature, timestamp = create_signature(appkey, subappkey, version, method, body, appSecret)

    # 请求头
    headers = {
        "appkey": appkey,
        "subappkey": subappkey,
        "sign": signature,
        "timestamp": timestamp,
        "version": version,
        "method": method
    }

    # 请求 URL
    url = "http://111.203.122.88:8081/busapi/api/stdapi"
    # url = "http://xcwms.digitalchina.com/busapi/api/stdapi"

    # 发起 GET 请求
    response = requests.get(url, headers=headers, data=body)

    # 检查响应
    if response.status_code == 200:
        print("请求成功，响应内容:", response.json())
    else:
        print(f"请求失败，状态码: {response.status_code}, 错误信息: {response.text}")


# 调用请求
if __name__ == '__main__':
    send_request()
