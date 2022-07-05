# -*- coding: utf-8 -*-
import scrapy
from scrapy.selector import Selector
from scrapy import signals
from items import ContentItem
from queue1 import Queue
import time
from langconv import *
from filter_words import filter_url
from urllib import parse
import pandas as pd
from CONSTANTS.constants import WIKI_PREFIX


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


def filter(url):
    # 如果字符串url中包含要过滤的词，则为True
    # filter_url = ['游戏', '%E6%B8%B8%E6%88%8F', '维基', '%E7%BB%B4%E5%9F%BA', '幻想', '我的世界', '魔兽']
    for i in filter_url:
        if i in url:
            return True
    return False


class GirlGallerySpider(scrapy.Spider):
    urlQueue = Queue()
    base_url = "https://sxchinesegirlz.one"
    name = 'girl_gallery_spider'
    allowed_domains = [base_url]
    start_urls = []  # ['https://zh.wikipedia.org/wiki/Category:被子植物']
    # 每个pipeline后面有一个数值，这个数组的范围是0-1000，这个数值确定了他们的运行顺序，数字越小越优先
    custom_settings = {
        'ITEM_PIPELINES': {
            #'scrapy.pipelines.images.ImagesPipeline': 1
            'counselor.pipelines.ImagePipeline': 300,
            'counselor.pipelines.WikiPipeline': 800
        },
        # 'FEED_URI': './output.json'
    }
    cat_pattern = "Category:"
    res = []

    @classmethod
    def get_entry(cls):
        df = pd.read_csv("../origin_page/Angiosperm Catalog Cleaned.csv", index_col=0)
        url_list = df['cat'].values.tolist()
        return list(map(lambda x: WIKI_PREFIX + r"/" + x, url_list))

    def get_cat(self, url):
        cat_str = url[url.find(self.cat_pattern) + len(self.cat_pattern):]
        return Traditional2Simplified(parse.unquote(cat_str))

    def request(self, url, layer=0, par=""):
        proxy = "https://127.0.0.1:7890"
        callback_func = self.parse_category if (
                                self.base_url == url or 'page' in url) \
                            else self.parse_content
        return scrapy.Request(url, callback=callback_func, dont_filter=True, meta={"proxy": proxy, "layer": layer, "par":par})

    def start_requests(self):  # 控制爬虫发出的第一个请求
        self.start_urls = [self.base_url]#self.get_entry()
        # print(self.start_urls)
        for url in self.start_urls:
            yield self.request(url)

    def save(self):
        # self.crawler.engine.close_spider(self)
        print('*' * 80, '\n', "entry num:", len(self.res), '\n', '*' * 80)
        df = pd.DataFrame(self.res)
        df.to_csv("Angiosperm Catalog.csv")

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(GirlGallerySpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def spider_closed(self, spider):
        self.save()

    def parse_category(self, response):
        """
        处理分类页面的请求
        :param response:
        :return:
        """
        layer = response.meta.get("layer")
        counselor_item = ContentItem()
        sel = Selector(response)
        this_url = Traditional2Simplified(parse.unquote(response.url))
        cat_str = self.get_cat(this_url)

        # add information to res
        d = {"layer": layer, "cat": cat_str, "parent":response.meta.get("par")}
        self.res.append(d)

        # self.urlQueue.delete_candidate(this_url)
        self.urlQueue.add_has_viewed(this_url)
        # search = sel.xpath("//div[@id='content']")
        # category_entity = search.xpath("//h1[@id='firstHeading']/text()").extract_first()
        candidate_lists_ = sel.xpath("//div[@id='page']//a/@href").extract()
        candidate_lists = []
        # 百科页面有许多超链接是锚链接，需要过滤掉
        print(candidate_lists_)

        for url in candidate_lists_:
            candidate_lists.append(Traditional2Simplified(parse.unquote(url)))
            print(Traditional2Simplified(parse.unquote(url)))

        # self.start_urls = self.urlQueue.candidates
        # print(cat_str)
        # print(candidate_lists)
        print('cat 已处理请求数=', len(self.urlQueue.has_viewed))
        # 处理完分类页面后，将所有可能的内容请求链接直接提交处理队列处理

        #if len(self.res) % 1000 == 0:
        #    df = pd.DataFrame(self.res)
        #    df.to_csv("Angiosperm Catalog {}.csv".format(len(self.res)))

        for url in candidate_lists:
            if url in self.urlQueue.has_viewed:
                continue
            yield self.request(url, layer+1, cat_str)

    def parse_content(self, response):
        '''
        处理百科页面请求
        :param response:
        :return:
        '''
        # print('*'*40, response)
        counselor_item = ContentItem()
        sel = Selector(response)
        this_url = response.url
        self.urlQueue.delete_candidate(this_url)
        # print('this_url=', this_url)
        search = sel.xpath("//div[@id='content']")
        #content_entity = search.xpath("//h1[@id='firstHeading']/text()").extract_first()
        #print(content_entity)
        content = sel.xpath("//div[@class='mw-parser-output']")
        # print(content)
        toc = content.xpath("./div[@id='toc']")
        if len(toc)==0:
            table = content.xpath("./table")
            text = ''.join(content.xpath("./p").xpath("string(.)").extract()).strip("\n")
        else:
            table = content.xpath("./div[@id='toc']/preceding-sibling::table")
            text = ''.join(content.xpath("./div[@id='toc']/preceding-sibling::p").xpath("string(.)").extract()).strip("\n")
        pic_addr_list = table.xpath(".//a[@class='image']//img/@src").extract()
        pic_addr_list = list(map(lambda x: "https:"+x, pic_addr_list))
        print(pic_addr_list)
        # print(table)
        counselor_item['img_url'] = pic_addr_list
        counselor_item['text'] = text
        counselor_item['topic'] = Traditional2Simplified(parse.unquote(this_url.split('/')[-1]))
        return counselor_item
