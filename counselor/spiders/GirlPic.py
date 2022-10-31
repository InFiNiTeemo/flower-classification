# -*- coding: utf-8 -*-
import scrapy
from scrapy.selector import Selector
from scrapy import signals
import os
from items import ContentItem
from queue1 import Queue
import time
from langconv import *
from filter_words import filter_url
from urllib import parse
import pandas as pd
from CONSTANTS.constants import WIKI_PREFIX, GIRL_BASE_DIR, GIRL_MAX_PAGE_RB
from mixin.save import save_attr, get_attr, save_attr_with_timeliness, get_attr_with_timeliness
import random
import numpy as np



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


def find_max_page(save_dir):
    max_page = 1000
    page = get_attr(save_dir, "page")
    if page is not None:
        page = list(map(int, page))
        max_page = min(max_page, min(page))
    return max_page


class GirlGallerySpider(scrapy.Spider):
    urlQueue = Queue()
    base_url = "https://sxchinesegirlz.one"
    name = 'girl_gallery_spider'
    allowed_domains = [base_url]
    start_urls = []  # ['https://zh.wikipedia.org/wiki/Category:被子植物']
    page_list = []
    # 每个pipeline后面有一个数值，这个数组的范围是0-1000，这个数值确定了他们的运行顺序，数字越小越优先
    custom_settings = {
        'ITEM_PIPELINES': {
            # 'scrapy.pipelines.images.ImagesPipeline': 1
            'counselor.pipelines.GirlItemPipeline': 100,
            'counselor.pipelines.GirlImagePipeline': 300,
            # 'counselor.pipelines.WikiPipeline': 800
        },
        # 'FEED_URI': './output.json'
    }
    cat_pattern = "Category:"
    page_pattern = "page"
    res = []

    def get_page_num(self, url):
        if url == self.base_url:
            return 1
        if self.page_pattern in url:
            return url.strip("/").split("/")[-1]
        else:
            return -1

    @classmethod
    def get_entry(cls):
        df = pd.read_csv("../origin_page/Angiosperm Catalog Cleaned.csv", index_col=0)
        url_list = df['cat'].values.tolist()
        return list(map(lambda x: WIKI_PREFIX + r"/" + x, url_list))

    def get_cat(self, url):
        cat_str = url[url.find(self.cat_pattern) + len(self.cat_pattern):]
        return Traditional2Simplified(parse.unquote(cat_str))

    def request(self, url, layer=0, par="", callback_func=None, **kwargs):
        proxy = "https://127.0.0.1:7890"
        if callback_func is None:
            callback_func = self.get_parse_func(url)
        return scrapy.Request(url, callback=callback_func, dont_filter=True,
                              meta={"proxy": proxy, "layer": layer, "par": par, **kwargs})

    def start_requests(self):  # 控制爬虫发出的第一个请求
        if not os.path.exists(GIRL_BASE_DIR):
            os.mkdir(GIRL_BASE_DIR)
        for page_num in range(2, GIRL_MAX_PAGE_RB):
            self.page_list.append(os.path.join(self.base_url, "page", str(page_num)))
        self.start_urls = [self.base_url]  # self.get_entry()
        # print(self.start_urls)
        for url in self.start_urls:
            yield self.request(url)

    def save(self):
        # self.crawler.engine.close_spider(self)
        print('*' * 80, '\n', "entry num:", len(self.res), '\n', '*' * 80)
        df = pd.DataFrame(self.res)
        df.to_csv("Angiosperm Catalog.csv")

    def get_parse_func(self, url):
        return self.parse_category if (self.base_url == url or 'page' in url) else self.parse_content

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(GirlGallerySpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def spider_closed(self, spider):
        self.save()

    def next_page(self, layer, cat_str):
        nxt_page_url = self.page_list[random.randint(0, len(self.page_list))]
        self.page_list.remove(nxt_page_url)
        print("next_page: ", nxt_page_url)
        yield self.request(nxt_page_url, layer + 1, cat_str, self.parse_category)

    def parse_category(self, response):
        """
        处理分类页面的请求
        :param response:
        :return:
        """
        layer = response.meta.get("layer")
        sel = Selector(response)
        this_url = Traditional2Simplified(parse.unquote(response.url))
        cat_str = self.get_cat(this_url)
        if this_url in self.urlQueue.has_viewed:
            return
        self.urlQueue.add_has_viewed(this_url)

        # add information to res
        d = {"layer": layer, "cat": cat_str, "parent": response.meta.get("par")}
        self.res.append(d)

        # check if saved
        page_num = self.get_page_num(this_url)
        finished_flag = True

        # self.urlQueue.delete_candidate(this_url)

        # search = sel.xpath("//div[@id='content']")
        # category_entity = search.xpath("//h1[@id='firstHeading']/text()").extract_first()
        candidate_list_ = sel.xpath("//div[@id='page']//a/@href").extract()
        candidate_list = []
        # 百科页面有许多超链接是锚链接，需要过滤掉
        print("content_url:", this_url)

        for url in candidate_list_:
            candidate_list.append(Traditional2Simplified(parse.unquote(url)))

        # self.start_urls = self.urlQueue.candidates
        # print(cat_str)
        # print(candidate_lists)
        print('cat 已处理请求数=', len(self.urlQueue.has_viewed))
        # 处理完分类页面后，将所有可能的内容请求链接直接提交处理队列处理

        # if len(self.res) % 1000 == 0:
        #    df = pd.DataFrame(self.res)
        #    df.to_csv("Angiosperm Catalog {}.csv".format(len(self.res)))
        candidate_list = list(filter(lambda x: x not in self.urlQueue.has_viewed, candidate_list))
        candidate_list = candidate_list[::-1]  # stack for yield

        # must dispose more content page before jump to another main page otherwise may stackoverflow
        for url in candidate_list:
            if self.get_parse_func(url) == self.parse_content:
                chinese_url = Traditional2Simplified(parse.unquote(url))
                save_dir = os.path.join(GIRL_BASE_DIR, chinese_url.split('/')[-2])
                page_rb = find_max_page(save_dir)
                if page_rb == 1:
                    self.urlQueue.add_has_viewed(chinese_url)
                    print("already visited: ", chinese_url)
                    continue
                else:
                    finished_flag = False
                # yield from get value of another generator
                # but request is not generator
                yield self.request(url, layer + 1, cat_str, self.parse_content)
        if finished_flag:
            print("record page: ", page_num)
            save_attr_with_timeliness(GIRL_BASE_DIR, "page"+str(page_num), "yes")

        x = page_num
        nxt_page_url = ""
        while (page_num != -1 and get_attr_with_timeliness(GIRL_BASE_DIR, "page" + str(page_num)) is not None) or page_num == x:
            print("already visited whole page: ", page_num)
            nxt_page_url = self.page_list[random.randint(0, len(self.page_list)-1)]
            self.page_list.remove(nxt_page_url)
            page_num = self.get_page_num(nxt_page_url)
            print("next_page: ", nxt_page_url)
        yield self.request(nxt_page_url, layer + 1, cat_str, self.parse_category)
        return
        # random.shuffle(candidate_list)
        # for url in candidate_list:
        #    if self.get_parse_func(url) == self.parse_category:
        #        print(url)
        #        # main page one by one
        #        yield self.request(url, layer + 1, cat_str, self.parse_category)
        #        return

    def check_page_meta(self):
        ...

    def parse_content(self, response):
        '''
        处理百科页面请求
        :param response:
        :return:
        '''
        # print('*'*40, response)

        chinese_url = Traditional2Simplified(parse.unquote(response.url))
        if chinese_url in self.urlQueue.has_viewed:
            return
        self.urlQueue.add_has_viewed(chinese_url)

        counselor_item = ContentItem()
        sel = Selector(response)
        this_url = response.url
        # self.urlQueue.delete_candidate(this_url)

        # todo move to request
        save_dir = os.path.join(GIRL_BASE_DIR,chinese_url.split('/')[-2])
        save_attr(save_dir, "url", this_url)

        def get_url_list(url):
            page = 2
            nxt_url = url + str(page) + "/"
            res = [url]
            response_text = response.text.lower()
            while nxt_url.lower() in response_text:
                res.append(nxt_url)
                page += 1
                nxt_url = url + str(page) + "/"
                # print("nxt_url:", nxt_url)
            return res

        url_list = get_url_list(this_url)
        # print("check url: ", url_list)
        i = 1
        for url in url_list:
            # for return, only return value once, loop is over
            # for yield, loop will continue, but will not be sure when to execute
            # nested yield can cause some url will never be traversed
            yield self.request(url, 0, "", self.parse_content_2, text=i)
            i += 1

    def parse_content_2(self, response):
        '''
        处理百科页面请求
        :param response:
        :return:
        '''
        # print('*'*40, response)

        counselor_item = ContentItem()
        sel = Selector(response)

        this_url = response.url
        print("parse_content_2", this_url)

        #pic_addr_list = sel.xpath("//figure[@class='wp-block-image size-large']/img/@src").extract() + sel.xpath(
        #    "//figure[@class='wp-block-image']/img/@src").extract()
        pic_addr_list = sel.xpath("//figure[@class='wp-block-image size-large']/img/@srcset").extract() + sel.xpath(
            "//figure[@class='wp-block-image']/img/@srcset").extract()

        def get_raw_pic(x):
            resolution_list = list(x.split(","))
            high_reso_idx = np.argmax(list(map(lambda x: int(x.split(" ")[-1][:-1]), resolution_list)))
            # print("high_reso_idx: ", high_reso_idx, resolution_list[high_reso_idx])
            x = resolution_list[high_reso_idx].split(" ")[-2]
            return x
        pic_addr_list = list(map(get_raw_pic, pic_addr_list))
        # filter
        # pic_addr_list = list(filter(lambda x: x.startswith("https") or x.startswith("http"), pic_addr_list))

        # print(table)

        def get_gallery_name():
            l = list(this_url.split('/'))
            name = l[-2]
            if len(name) <= 2:
                name = l[-3]
            return name

        counselor_item['img_url'] = pic_addr_list
        counselor_item['text'] = response.meta.get("text")
        counselor_item['topic'] = Traditional2Simplified(parse.unquote(get_gallery_name()))
        return counselor_item
