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

ITEM_PIPELINES = {
  #'scrapy.pipelines.images.ImagesPipeline':1
   'counselor.pipelines.ImagePipeline': 300,
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
CONCURRENT_REQUESTS = 50




AUTOTHROTTLE_ENABLED = True
