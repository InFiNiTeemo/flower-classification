# -*- coding: utf-8 -*-                                                                                                                                                                    +
import re

import scrapy
from scrapy.selector import Selector
from scrapy import signals
import os
from items import PicItem
from queue1 import Queue
import time
from langconv import *
from filter_words import filter_url
from urllib import parse
import pandas as pd
from CONSTANTS.constants import *
from mixin.save import save_attr, get_attr, save_attr_with_timeliness, get_attr_with_timeliness
import random
import urllib
import urllib3
import numpy as np
import requests
import json
import base64
from datetime import datetime


random.seed(datetime.now())


headers = {
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.8',
    'Cache-Control': 'max-age=0',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36',
    'Connection': 'keep-alive',
    'Referer': 'http://www.baidu.com/'
}

def Traditional2Simplified(sentence):
    '''
    将sentence中的繁体字转为简体字
    :param sentence: 待转换的句子
    :return: 将句子中繁体字转换为简体字之后的句子
    '''
    sentence = Converter('zh-hans').convert(sentence)
    return sentence


def split(url_list):
    '''
    分离两种不同的请求类型（分类/内容）
    :return:
    '''
    cates_url, content_url = [], []
    for url in url_list:
        if 'Category:' in url:
            cates_url.append(url)
        else:
            content_url.append(url)
    return cates_url, content_url


# #
# # def filter(url):
# #     # 如果字符串url中包含要过滤的词，则为True
# #     # filter_url = ['游戏', '%E6%B8%B8%E6%88%8F', '维基', '%E7%BB%B4%E5%9F%BA', '幻想', '我的世界', '魔兽']
# #     for i in filter_url:
# #         if i in url:
# #             return True
#     return False

MAX_PAGE = 2
def get_unvisited_page(topic_dir):
    max_page = int(get_attr(topic_dir, "max_page", default=[MAX_PAGE])[0])
    visited_pages = set(map(int, get_attr(topic_dir, "page", [])))
    unvisited_pages = set(np.arange(1, max_page+1, 1)) - visited_pages
    return list(unvisited_pages)


def is_visited(topic_dir):
    # print("len: ",  len(get_unvisited_page(topic_dir)))
    return len(get_unvisited_page(topic_dir)) == 0


class FlowerPicSpider(scrapy.Spider):
    urlQueue = Queue()
    base_url = "https://ppbc.iplant.cn"
    name = 'flower_pic_spider'
    dataset_path = str(os.path.join(DATA_DIR, "Flower", "huabaike.csv"))
    allowed_domains = [base_url]
    start_urls = []
    topic_urls = []
    # 每个pipeline后面有一个数值，这个数组的范围是0-1000，这个数值确定了他们的运行顺序，数字越小越优先
    custom_settings = {
        'ITEM_PIPELINES': {
            # 'scrapy.pipelines.images.ImagesPipeline': 1
            'counselor.pipelines.ImageItemPipeline': 100,
            'counselor.pipelines.ImagePipelineWithoutScrapy': 300,
            # 'counselor.pipelines.WikiPipeline': 800
        },
        # 'FEED_URI': './output.json'
    }
    # settings
    cat_pattern = "Category:"
    page_pattern = "page"
    search_prefix = "https://ppbc.iplant.cn/ashx/getphotopage.ashx?"
    max_page = MAX_PAGE
    #
    res = []
    df = None
    base_dir = FLOWER_BASE_DIR

    def get_an_unvisit_topic_url(self, topic_urls: list):
        remove_list = []
        for topic_url in topic_urls:
            topic = self.get_topic(topic_url)
            topic_dir = os.path.join(self.base_dir, topic)
            if not self.has_viewed(topic_url) and not is_visited(topic_dir):
                for remove_url in remove_list:
                    topic_urls.remove(remove_url)
                print("Choose topic: ", topic)
                topic_urls.remove(topic_url)
                return topic_url
            else:
                print("visited:", topic)
                remove_list.append(topic_url)
        return ""

    def get_page_num(self, url):
        for s in re.split("[?]|[&]", parse.unquote(url)):
            if "page=" in s:
                return s.strip("page=")
        return 1

    @classmethod
    def get_topic(cls, url):
        for s in re.split("[?]|[&]", parse.unquote(url)):
            if "keyword=" in s:
                return s.strip("keyword=")
        return ""


    def get_cat(self, url):
        cat_str = url[url.find(self.cat_pattern) + len(self.cat_pattern):]
        return Traditional2Simplified(parse.unquote(cat_str))

    def request(self, url, layer=0, par="", callback_func=None, **kwargs):
        proxy = "https://127.0.0.1:7890"
        if callback_func is None:
            callback_func = self.get_parse_func(url)
        if USE_PROXY:
            return scrapy.Request(url, callback=callback_func, dont_filter=True,
                                  meta={"proxy":PROXY, "layer": layer, "par": par, **kwargs})
        else:
            return scrapy.Request(url, callback=callback_func, dont_filter=True,
                              meta={"layer": layer, "par": par, **kwargs})

    def start_requests(self):  # 控制爬虫发出的第一个请求
        if not os.path.exists(self.base_dir):
            os.mkdir(self.base_dir)
        self.df = pd.read_csv(self.dataset_path)
        search_prefix = "https://ppbc.iplant.cn/ashx/getserachinfo21.ashx?keyword={****}&sel=like"# "https://ppbc.iplant.cn/list21?keyword={****}&sel=like"
        self.topic_urls = self.df["title"].apply(lambda x: search_prefix.replace("{****}", x)).values.tolist() # [:2]
        random.shuffle(self.topic_urls)
        yield self.request(self.get_an_unvisit_topic_url(self.topic_urls), callback_func=self.parse_category)

    def save(self):
        # self.crawler.engine.close_spider(self)
        print('*' * 80, '\n', "entry num:", len(self.res), '\n', '*' * 80)
        df = pd.DataFrame(self.res)
        df.to_csv("Angiosperm Catalog.csv")

    def get_parse_func(self, url):
        return self.parse_category if self.base_url == url else self.parse_content

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(FlowerPicSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def spider_closed(self, spider):
        self.save()

    def has_viewed(self, url, add_has_viewed=False, return_url=False):
        this_url = Traditional2Simplified(parse.unquote(url))
        if this_url in self.urlQueue.has_viewed:
            self.topic_urls.remove(this_url)
            if return_url:
                return True, this_url
            else:
                return True
        if add_has_viewed:
            self.urlQueue.add_has_viewed(this_url)
        if return_url:
            return False, this_url
        return False

    def parse_ajax(self, response):
        def get_urls():
            if "searchlist" not in json.loads(response.text):
                return []
            decode = base64.b64decode(json.loads(response.text)["searchlist"])
            sel = Selector(text=decode)
            img_list = sel.xpath("//div[@class='img']//img/@src").extract()
            if img_list is None:
                return []
            img_list = list(map(lambda x: "https:"+x, img_list))
            return img_list

        has_view, this_url = self.has_viewed(response.url, add_has_viewed=True, return_url=True)
        if has_view:
            return
        item = PicItem()
        item['topic'] = self.get_topic(response.url)
        item['page'] = response.meta.get("page_num")
        item['img_urls'] = get_urls()
        assert isinstance(item['img_urls'], list)
        return item

    def parse_category(self, response):
        """
        处理分类页面的请求
        :param response:
        :return:
        """
        # print(response.__dict__.keys())
        if response.status != 200:
            print("status not 200!", response.url)
            return

        has_view, this_url = self.has_viewed(response.url, add_has_viewed=True, return_url=True)
        if has_view:
            return

        layer = response.meta.get("layer")
        sel = Selector(response)
        cat_str = self.get_cat(this_url)

        # add information to res
        #d = {"layer": layer, "cat": cat_str, "parent": response.meta.get("par")}
        # self.res.append(d)

        # get attr and save
        topic_dir = os.path.join(self.base_dir, self.get_topic(this_url))
        if get_attr(topic_dir, "max_page") is None:
            save_attr(topic_dir, "max_page", self.max_page)
        if get_attr(topic_dir, "url") is None:
            save_attr(topic_dir, "url", this_url)
        unvisited_page = get_unvisited_page(topic_dir)

        # traverse page
        def get_page_url(p):
            d = {}
            res = this_url
            for k, v in d.items():
                res += f"{k}={v}&"
            res += f"&page={p}"
            return res

        # visited page
        print(f"url: {this_url}   unvisited page: {unvisited_page}")
        # since yield's order is as stack, ::-1 can traverse page from 1 to n
        for page_num in unvisited_page[::-1]:
            request_url = get_page_url(page_num)
            print("next_page: ", request_url)
            yield self.request(request_url, callback_func=self.parse_ajax, page_num=page_num)

        # traverse another topic

        yield self.request(
            self.get_an_unvisit_topic_url(self.topic_urls),
            layer=layer, callback_func=self.parse_category
        )
        return