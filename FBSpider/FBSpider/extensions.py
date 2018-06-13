from scrapy import signals
from .spiders.FBPostSPider import FBPostSpider

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
            request = spider.make_requests_from_job()
            if request != None:
                self.crawler.engine.crawl(request, spider)