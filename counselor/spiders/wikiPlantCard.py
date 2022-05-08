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


class WiKiSpider(scrapy.Spider):
    urlQueue = Queue()
    name = 'wikipedia_plant_card_spider'
    allowed_domains = ['zh.wikipedia.org']
    start_urls = []  # ['https://zh.wikipedia.org/wiki/Category:被子植物']
    # 每个pipeline后面有一个数值，这个数组的范围是0-1000，这个数值确定了他们的运行顺序，数字越小越优先
    custom_settings = {
        'ITEM_PIPELINES': {'counselor.pipelines.WikiPipeline': 800},
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
        callback_func = self.parse_category if 'Category:' in url else self.parse_content
        return scrapy.Request(url, callback=callback_func, dont_filter=True, meta={"proxy": proxy, "layer": layer, "par":par})

    def start_requests(self):  # 控制爬虫发出的第一个请求
        self.start_urls = self.get_entry()
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
        spider = super(WiKiSpider, cls).from_crawler(crawler, *args, **kwargs)
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
        search = sel.xpath("//div[@id='content']")
        # category_entity = search.xpath("//h1[@id='firstHeading']/text()").extract_first()
        candidate_lists_ = search.xpath("//div[@id='mw-subcategories']//a/@href").extract()
        candidate_lists = []
        # 百科页面有许多超链接是锚链接，需要过滤掉

        for url in candidate_lists_:
            if filter(url): # 分类请求中过滤掉一些不符合的请求（例如明显包含游戏的关键词都不要爬取）
                continue
            if '/wiki' in url and 'https://zh.wikipedia.org' not in url:
                if ':' not in url or (':' in url and self.cat_pattern in url):
                    candidate_lists.append('https://zh.wikipedia.org' + Traditional2Simplified(parse.unquote(url)))

        # self.start_urls = self.urlQueue.candidates
        print(cat_str)
        print(candidate_lists)
        print('cat 已处理请求数=', len(self.urlQueue.has_viewed))
        # 处理完分类页面后，将所有可能的内容请求链接直接提交处理队列处理

        if len(self.res) % 1000 == 0:
            df = pd.DataFrame(self.res)
            df.to_csv("Angiosperm Catalog {}.csv".format(len(self.res)))

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
            text = ''.join(content.xpath("./p").xpath("string(.)").extract())
        else:
            table = content.xpath("./div[@id='toc']/preceding-sibling::table")
            text = ''.join(content.xpath("./div[@id='toc']/preceding-sibling::p").xpath("string(.)").extract())
        pic_addr_list = table.xpath(".//a[@class='image']//img/@src").extract()
        pic_addr_list = list(map(lambda x: x.strip(r"//"), pic_addr_list))
        # print(table)
        print(text)
        print(pic_addr_list)


        #mp = p.xpath("div[@id='toc']")
        #p = p.xpath()

        #print(mp)
        #print(tp)
        #time.sleep(3)




        # content_entity = Traditional2Simplified(content_entity)
        # content_page = search.xpath("//div[@id='bodyContent']//div[@id='mw-content-text']//div[@class='mw-parser-output']").extract_first()# 将带有html的标签的整个数据拿下，后期做处理
        # cates = search.xpath("//div[@id='catlinks']//ul//a/text()").extract()
        # candidate_lists_ = search.xpath("//div[@id='bodyContent']//*[@id='mw-content-text' and not(@class='references') and not(@role='presentation')]//a/@href").extract()
        # candidate_lists = []
        # 百科页面有许多超链接是锚链接，需要过滤掉
        # for url in candidate_lists_:
        #     if '/wiki' in url and 'https://zh.wikipedia.org' not in url:
        #         if ':' not in url or (':' in url and 'Category:' in url):
        #             candidate_lists.append('https://zh.wikipedia.org' + url)

        # self.start_urls = self.urlQueue.candidates
        # self.urlQueue.add_has_viewed(this_url)
        # # self.urlQueue.add_candidates(candidate_lists)
        # print('content 候选请求数=', len(self.urlQueue.candidates))
        # print('content 已处理请求数=', len(self.urlQueue.has_viewed))
        # #self.urlQueue.save_has_viewed()
        # # 将当前页面的信息保存下来
        # # print(content_entity)
        # # 如果当前的content的标题或分类属于需要过滤的词（例如我们不想爬取跟游戏有关的，所以包含游戏的请求或分类都不保存）
        # is_url_filter = filter(content_entity)
        # is_cates_filter = False
        # for cate in cates:
        #     cate = Traditional2Simplified(cate)
        #     if filter(cate):
        #         is_cates_filter = True
        #         break
        # if is_url_filter == False and is_cates_filter == False:
        #     counselor_item['content_entity'] = content_entity.replace(':Category', '')
        #     counselor_item['category'] = '\t'.join(cates)
        #     counselor_item['time'] = str(time.time())
        #     counselor_item['url'] = this_url
        #     counselor_item['content'] = str(content_page)
        # return counselor_item

        # dir = '../origin_page/'
        # with open(dir + counselor_item['content_entity'] + '(' + counselor_item['time'] + ')' + '.txt', 'w', encoding='utf-8') as fw:
        #     fw.write('标题：\n' + counselor_item['content_entity'] + '\n')
        #     fw.write('原文地址：' + counselor_item['url'] + '\n')
        #     fw.write('爬取时间：' + counselor_item['time'] + '\n\n')
        #     fw.write(counselor_item['content'])
        #
        # # 处理完分类页面后，将所有可能的内容请求链接直接提交处理队列处理
        # for url in self.urlQueue.candidates:
        #     # print(url)
        #     if 'Category:' in url:
        #         # print(url)
        #         yield scrapy.Request(url, callback=self.parse_category, dont_filter=True)
        #     else:
        #         yield scrapy.Request(url, callback=self.parse_content, dont_filter=True)
