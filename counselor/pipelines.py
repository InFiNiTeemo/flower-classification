# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
from scrapy.pipelines.images import ImagesPipeline
from scrapy import Request
import re
import os


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


class ImagePipeline(ImagesPipeline):
    def get_media_requests(self, item, info):
        # 循环每一张图片地址下载，若传过来的不是集合则无需循环直接yield
        print("In Image Pipeline.")
        for image_url in item['img_url']:
            print("Image Pipeline:", image_url)
            proxy = "https://127.0.0.1:7890"
            yield Request(image_url, meta={"proxy": proxy}, dont_filter=True)

    def file_path(self, request, response=None, info=None, item=None):
         # 重命名，若不重写这函数，图片名为哈希，就是一串乱七八糟的名字
         image_guid = request.url.split('/')[-1] # 提取url前面名称作为图片名。
         image_path = os.path.join(item['topic'], image_guid)
         print("Image Pipeline:", image_path)
         return image_path
