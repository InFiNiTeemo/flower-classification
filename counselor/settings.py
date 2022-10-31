# -*- coding: utf-8 -*-

# Scrapy settings for counselor project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = 'counselor'

SPIDER_MODULES = ['counselor.spiders']
NEWSPIDER_MODULE = 'counselor.spiders'

#  items go through from lower valued to higher valued classes.
ITEM_PIPELINES = {
   #'scrapy.pipelines.images.ImagesPipeline':1
   'counselor.pipelines.GirlItemPipeline': 100,
   'counselor.pipelines.GirlImagePipeline': 300,

   # 'counselor.pipelines.WikiPipeline': 800,
}


# Crawl responsibly by identifying yourself (and your website) on the user-agent
USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_3) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.54 Safari/536.5'
KEEP_ALIVE = 'True'
IMAGES_STORE = '../origin_page'
FILES_STORE = 'images'

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

#DOWNLOAD_DELAY = 3
CONCURRENT_REQUESTS = 128




AUTOTHROTTLE_ENABLED = True
