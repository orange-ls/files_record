### 传递 URL 参数

你也许经常想为 URL 的查询字符串(query string)传递某种数据。如果你是手工构建 URL，那么数据会以键/值对的形式置于 URL 中，跟在一个问号的后面。例如， `httpbin.org/get?key=val`。 Requests 允许你使用 `params` 关键字参数，以一个字符串字典来提供这些参数。举例来说，如果你想传递 `key1=value1` 和 `key2=value2` 到 `httpbin.org/get` ，那么你可以使用如下代码：

```
>>> payload = {'key1': 'value1', 'key2': 'value2'}
>>> r = requests.get("http://httpbin.org/get", params=payload)
```

通过打印输出该 URL，你能看到 URL 已被正确编码：

```
>>> print(r.url)
http://httpbin.org/get?key2=value2&key1=value1
```

**==注意字典里值为 `None` 的键都不会被添加到 URL 的查询字符串里。==**



### 定制请求头

如果你想为请求添加 HTTP 头部，只要简单地传递一个 `dict` 给 `headers` 参数就可以了。

例如，在前一个示例中我们没有指定 content-type:

> ​	`Content-Type` 是一个 HTTP 响应头（Header），它指定了响应体的媒体类型（MIME 类型）。这个头信息告诉客户端（如浏览器或 API 客户端）如何解释响应内容。`Content-Type` 头通常用于指示响应内容是纯文本、HTML、JSON、XML、图片、视频等。

```
>>> url = 'https://api.github.com/some/endpoint'
>>> headers = {'user-agent': 'my-app/0.0.1'}

>>> r = requests.get(url, headers=headers)
```

注意: 定制 header 的优先级低于某些特定的信息源，例如：

- 如果在 `.netrc` 中设置了用户认证信息，使用 headers= 设置的授权就不会生效。而如果设置了 `auth=` 参数，``.netrc`` 的设置就无效了。
- 如果被重定向到别的主机，授权 header 就会被删除。
- 代理授权 header 会被 URL 中提供的代理身份覆盖掉。
- 在我们能判断内容长度的情况下，header 的 Content-Length 会被改写。

更进一步讲，Requests 不会基于定制 header 的具体情况改变自己的行为。只不过在最后的请求中，所有的 header 信息都会被传递进去。

注意: 所有的 header 值必须是 `string`、bytestring 或者 unicode。尽管传递 unicode header 也是允许的，但不建议这样做。