## GET wms库房分配表

http://10.0.23.146:8080/quotationApi/spare_parts/wms_storeroom_table



> Header 示例

![image-20241115111204231](D:/Typora/files/image-20241115111204231.png)

> Body 请求参数 示例

```json
{
  "startTime": "1706583050910",
  "endTime": "1732935050910",
  "offset": "1",
  "limit": "10"
}
```

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|Cookie|header|string| 否 |none|
|body|body|object| 否 |none|
|» startTime|body|string| 是 |none|
|» endTime|body|string| 是 |none|
|» offset|body|string| 是 |none|
|» limit|body|string| 是 |none|

> 返回示例

> 200 Response

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回样式

![image-20241115111004535](D:/Typora/files/image-20241115111004535.png)

