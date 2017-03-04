# 番号磁链获取器
获取Javbus上的数据并保存到MongoDB数据库

### 依赖库
- requests
- BeautifulSoup4
- progress
- re
- math
- random
- pymongo

### 使用方法
* 下载

> git clone https://github.com/MyFaith/JavbusGetter.git

* 安装依赖库

> pip install BeautifulSoup4 requests pymongo

* 修改javbus.py中的服务器配置

`mongo = MongoClient(host='192.168.199.217')`

* 运行
`python javbus.py -page 10 -thread 4` (page 页数 thread 启用线程数)

### 运行结果
![1.png](https://ooo.0o0.ooo/2017/03/04/58ba86e297b31.png)
