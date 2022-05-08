# -*- coding: utf-8 -*-
import requests

# 1、网址url  --豆瓣网
url = 'https://zh.wikipedia.org/wiki/Category:%E8%AE%A1%E7%AE%97%E6%9C%BA%E7%BC%96%E7%A8%8B' #'http://www.douban.com'

headers = {
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.8',
    'Cache-Control': 'max-age=0',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36',
    'Connection': 'keep-alive',
    'Referer': 'http://www.baidu.com/'
}

# 使用代理 http, https
proxies = {
    "http": "http://127.0.0.1:7890",
    "https": "http://127.0.0.1:7890",
}

# 2、直接请求  返回结果
response = requests.get(url,
                    proxies=proxies,
                    headers=headers)

# 3、获取状态码，如果是200表示获取成功
#print('状态码：', response)

# 4、读取内容
data = response.text


# 6、打印结果
print(data)
