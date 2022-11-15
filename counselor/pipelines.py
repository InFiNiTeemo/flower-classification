# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
from scrapy.pipelines.images import ImagesPipeline
from scrapy import Request
import re
import os
import pickle
import json
from mixin.save import save_attr, get_attr
from CONSTANTS.constants import *
import urllib
import time
import requests
from multiprocessing.pool import Pool, ThreadPool
from fake_useragent import UserAgent


class WikiPipeline(object):
    def process_item(self, item, spider):
        self.writeFile(item)
        return item

    def writeFile(self, data):
        # print('========',len(data),'=========')
        base_dir = '../origin_page'
        topic_dir = os.path.join(base_dir, data['topic'])
        if not os.path.exists(topic_dir):
            os.mkdir(topic_dir)
        with open(os.path.join(topic_dir, 'introduction') + '.txt', 'w', encoding='utf-8') as fw:
            fw.write(data['text'])


#
class ImagePipeline(ImagesPipeline):
    def get_media_requests(self, item, info):
        # 循环每一张图片地址下载，若传过来的不是集合则无需循环直接yield
        print("In Image Pipeline.")
        for image_url in item['img_urls']:
            print("Image Pipeline:", image_url)
            if USE_PROXY:
                yield Request(image_url, meta={"proxy": PROXY}, dont_filter=True)
            else:
                yield Request(image_url, dont_filter=True)

    def file_path(self, request, response=None, info=None, item=None):
        # 重命名，若不重写这函数，图片名为哈希，就是一串乱七八糟的名字
        image_guid = request.url.split('/')[-1]  # 提取url前面名称作为图片名。
        image_path = os.path.join(item['topic'], image_guid)
        print("Image Pipeline path:", image_path)
        return image_path


NUM_THREADS = 30


def retry(func):
    def inner(*args, **kwargs):
        ret = func(*args, **kwargs)
        max_retry = 100
        cur_retry = 0
        if not ret:
            while cur_retry < max_retry:
                cur_retry += 1
                time.sleep(0.5)
                # print("尝试第:{}次".format(number))
                try:
                    result = func(*args, **kwargs)
                except:
                    continue
                if result:
                    break
    return inner


class ImagePipelineWithoutScrapy(object):
    def process_item(self, item, spider):
        #
        @retry
        def get_image(image_url):
            image_guid = image_url.split('/')[-1]  # 提取url后面名称作为图片名。
            image_path = os.path.join(item['topic'], image_guid)
            if os.path.exists(image_path) and os.path.getsize(image_path) > 1024:
                return
            print("Get img:", image_url)
            urllib.request.urlretrieve(image_url, image_path)

        topic_dir = item['topic']
        topic = topic_dir.rstrip("/").split("/")[-1]
        max_page = int(get_attr(topic_dir, "max_page")[0])
        page = int(item['page'])
        if max_page < page:
            return

        print(f"{topic}  page {page}, pic num: {len(item['img_urls'])}")
        if not len(item["img_urls"]):
            save_attr(topic_dir, "max_page", min(max_page, page-1), force_reset=True)
            return

        for img_url in item["img_urls"]:
            get_image(img_url)
        #l = ThreadPool(len(item["img_urls"])).imap_unordered(get_image, item["img_urls"])  #
        #for x in l:
        #    print("", end="")
        save_attr(topic_dir, "page", page)

        # def save_image(image_url):
        #     image_guid = image_url.split('/')[-1]  # 提取url前面名称作为图片名。
        #     image_path = os.path.join(item['topic'], image_guid)
        #     headers = {'User-Agent': UserAgent().random}
        #     res = requests.get(image_url, headers=headers)
        #     with open(image_path, "wb+") as f:
        #         f.write(res.content)
        #     print(image_url)
        #     print(res.status_code)


        # ThreadPool(NUM_THREADS).imap(get_image, item["img_urls"])
            # proxy = "https://127.0.0.1:8969"
            # if USE_PROXY:
            #     yield Request(image_url, meta={"proxy": proxy}, dont_filter=True)
            # else:
            #     yield Request(image_url, dont_filter=True)


class ImageItemPipeline(object):
    def process_item(self, item, spider):
        base_dir = FLOWER_BASE_DIR
        if not os.path.exists(base_dir):
            os.mkdir(base_dir)
        item['topic'] = os.path.join(base_dir, item['topic'])
        os.makedirs(os.path.join(base_dir, item['topic']), exist_ok=True)
        # self.writeFile(item)
        return item


class GirlItemPipeline(object):
    def process_item(self, item, spider):
        base_dir = GIRL_BASE_DIR
        if not os.path.exists(base_dir):
            os.mkdir(base_dir)
        item['topic'] = os.path.join(base_dir, item['topic'])
        self.writeFile(item)
        return item

    def writeFile(self, data):
        topic_dir = data['topic']
        value = str(data["text"])
        save_attr(topic_dir, "page", value)





class GirlImagePipeline(ImagesPipeline):
    def get_media_requests(self, item, info):
        # 循环每一张图片地址下载，若传过来的不是集合则无需循环直接yield
        for image_url in item['img_url']:
            print("Image URL:", image_url)
            proxy = PROXY

            headers = {"authority": "sxchinesegirlz-0ne.b-cdn.net",
                                     "referer": "https://sxchinesegirlz.one/",
                                   "sec-fetch-site": "cross-site",
                                   "user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.0.0 Mobile Safari/537.36"
                                   }

            if USE_PROXY:
                yield Request(image_url,
                              method="get",
                              headers=headers,
                              meta={"proxy": proxy}, dont_filter=True)
            else:
                yield Request(image_url,
                          method="get",
                          headers=headers,
                          dont_filter=True)

    def file_path(self, request, response=None, info=None, item=None):
        # 重命名，若不重写这函数，图片名为哈希，就是一串乱七八糟的名字

        image_guid = request.url.split('/')[-1]  # 提取url后面名称作为图片名。
        image_path = os.path.join(item['topic'], image_guid)
        print("Image Pipeline path:", image_path)
        return image_path
