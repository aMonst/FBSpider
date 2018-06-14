from scrapy import signals
from .spiders.FBPostSPider import *
import time

class HookSpiderIDLEExterns(object):
    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def __init__(self, crawler):
        cs = crawler.signals.connect
        self.crawler = crawler
        cs(self.spider_idle, signal = signals.spider_idle)

    def spider_idle(self, spider):
        if spider.name == "FBPostSpider":
            if spider.isInitSuccess():
                requests = spider.make_requests_from_job()
            else:
                requests = spider.get_start_request()

            if requests != None:
                for request in requests:
                    self.crawler.engine.crawl(request, spider)