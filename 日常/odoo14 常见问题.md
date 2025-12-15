## 步骤：

1、创建虚拟环境

```
D:\Python\Python3.8\python.exe -m venv venv
也可简写：python -m venv venv（默认创建python版本）
```

2、切换到虚拟环境
3、下载配置文件中的包

```
pip install -r requirements.txt -i https://repo.huaweicloud.com/repository/pypi/simple
```





## 问题：

1、pyrfc库问题

​	a、pyrfc使用2.4.2版本

​	b、nwrfc：

​		下载对应zip，

​		解压后把META-INF和SIGNATURE.SMF移到nwrfcsdk中

​		创建环境变量：SAPNWRFC_HOME：D:\project\nwrfc750P_6-70002755\nwrfcsdk

​		PATH中添加：%SAPNWRFC_HOME%\lib

​		重启电脑



2、python-ldap库
	下载python_ldap-3.4.4-cp38-cp38-win_amd64.whl

​	在终端执行

```
pip install D:\project\python_ldap-3.4.4-cp38-cp38-win_amd64.whl
```

​		

