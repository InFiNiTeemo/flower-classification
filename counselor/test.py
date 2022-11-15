# -*- coding: utf-8 -*-
import requests
from urllib import parse
import json
from scrapy.selector import Selector
import base64
import urllib


# 1、网址url  --豆瓣网
url = 'https://ppbc.iplant.cn/list21?keyword=%E9%83%81%E9%87%91%E9%A6%99&sel=like' #'http://www.douban.com'

# ppbc
#url = "https://ppbc.iplant.cn/ashx/getphotopage.ashx?page=3&n=2&group=sp&cid=34052"
# url =  "https://ppbc.iplant.cn/sp/34052"
# no redirect
# url ="https://ppbc.iplant.cn/ashx/getserachinfo21.ashx?keyword=菊花&sel=like"#&t=0.57611321"
url ="https://ppbc.iplant.cn/ashx/getserachinfo21.ashx?page=2&keyword=菊花&sel=like"#&t=0.57611321"


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
                    headers=headers)

# 3、获取状态码，如果是200表示获取成功
#print('状态码：', response)

# 4、读取内容
data = response.text
data = json.loads(data)

# 6、打印结果
#print(parse.unquote(url))
print(response.__dict__.keys())
#print(response.url)

prefix = "https://ppbc.iplant.cn/ashx/getphotopage.ashx?"
def get_content(response):
    ...
    #print(page_num,":", pth)
    #text = json.loads(_response.text)
    #print(type(text))

# get_content(response)
#print(response.status_code)

# print(len(data["searchlist"]))
#print(base64.b64decode(data["searchlist"]))
# decode = base64.b64decode(data["searchlist"])
# sel = Selector(text=decode)
# img_list = sel.xpath("//div[@class='img']//img/@src").extract()
# print(len(img_list))
# https://ppbc.iplant.cn/list21?keyword=郁金香&sel=like

# https://ppbc.iplant.cn/ashx/getphotopage.ashx?page=3&n=2&group=sp&cid=32201

#import re
#for i in re.split("\\?|\\&", "wqejrlkjl?iueoiqewj&.rejal"):
#    print(i)


#urllib.request.urlretrieve("https://img8.iplant.cn/image2/236/5912808.jpg", '/home/mobius/img.jpg')
