# -*- coding: utf-8 -*-
import scrapy
from FBSpider.items import *
from urllib.parse import urljoin, urlparse
from scrapy.http.request import Request
import codecs
from scrapy_splash import SplashRequest, SplashFormRequest
from FBSpider.LuaScript import *
from FBSpider.settings import *
from FBSpider.ReadConfig import ReadConfig
import re
import os.path
from scrapy.selector import Selector
from FBSpider.dbHelper import *
from scrapy import cmdline
import random

#爬取用户好友信息
class FBUsersSpider(scrapy.Spider):
    name = 'FBUsersSpider'
    def __init__(self, *args, **kwargs):
        self.login_url = "https://www.facebook.com/login"
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.path = os.path.join(base_dir, "users.txt")

        self.header = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "zh-CN,zh;q=0.8,en;q=0.6",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.75 Safari/537.36",
            "Referer": "https://www.facebook.com/",
        }


        self.cookie = []
        self.config = ReadConfig()
        self.deal = set()
        super(FBUsersSpider, self).__init__(*args, **kwargs)

    def login(self, response):
        if self.config.hasKey("proxy"):
            proto, host, port = self.config.getRnadomProxy()
            user_proxy = USE_PROXY % (host, port, proto)
        else:
            user_proxy = ""

        lua_script = LOGIN % user_proxy
        users = self.config.getLoginUsers()
        if not users:
            print("请在配置文件中至少指定一个登陆用户信息")
            return

        for user in users:
            yield SplashFormRequest.from_response(
                response,
                url = self.login_url,
                formdata={
                    "email":user[0],
                    "pass": user[1]
                },
                meta = {"user" : user[0]},
                endpoint="execute",
                args={
                    "wait": 30,
                    "lua_source": lua_script,
                    "user_name" : user[0],
                    "user_passwd" : user[1],
                },
                callback = self.after_login,
                errback = self.error_parse,
            )

    def after_login(self, response):
        #登录成功的话页面会跳转到主页
        if response.data["url"] == self.login_url:
            print("用户[%s]登录失败，即将关闭爬虫....." % response.meta["user"])
            return

        self.cookie.append(response.data["cookies"]) # 保存cookie
        # 登录成功后请求用户主页，爬取用户主页信息
        if self.config.hasKey("proxy"):
            proto, host, port = self.config.getRnadomProxy()
            user_proxy = USE_PROXY % (host, port, proto)
        else:
            user_proxy = ""

        lua_script = REQUEST_MAIN_PAGE % user_proxy

        for user in self.start_users:
            yield SplashRequest(
                url = user[1],
                callback=self.parse_main_page,
                endpoint= "execute",
                headers = response.request.headers,
                cookies= random.choice(self.cookie),
                meta={"level" : 1, "name" : user[0]},
                args={
                    "wait": 30,
                    "lua_source" : lua_script,
                }
            )

    def parse_main_page(self, response):
        if response.meta["name"] in self.deal:
            return

        #提取主页中的用户信息
        user_item = self._get_user_info(response.data["html"], response.url)
        if user_item["user_type"] == 0:
            print("未找到对应用户信息，可能是程序所使用的登录账号被封禁")
            return

        user_item["user_level"] = response.meta["level"]
        user_item["user_name"] = response.meta["name"]

        print("提取到用户信息[%s]" % user_item["user_name"])
        self.deal.add(user_item["user_name"])
        yield user_item
        if user_item["user_level"] == 4: # 最多取3层用户，当前用户为第四层时就不再取（由于外部导入的算第一层所以这里取到第4层）
            return

        if user_item["user_type"] == TopUser.PUBLIC_PAGE:
            #公共主页通过API获取
            print("公共主页没有好友信息")
            return

        elif user_item["user_type"] == TopUser.PRIVATE_PAGE:
            api = urljoin("https://www.facebook.com", user_item["user_id"])
            if self.config.hasKey("proxy"):
                proto, host, port = self.config.getRnadomProxy()
                user_proxy = USE_PROXY % (host, port, proto)
            else:
                user_proxy = ""

            lua_script = GET_FRIEND_PAGE % user_proxy
            yield SplashRequest(
                url = api,
                cookies= random.choice(self.cookie),
                endpoint="execute",
                callback= self._get_friends_page,
                meta={
                    "level" : user_item["user_level"],
                    "name" : response.meta["name"]
                },

                args={
                    "lua_source" : lua_script,
                    "wait": 30,
                }
            )

    def error_parse(self, response):
        print("发生网络错误，即将停止对用户信息的爬取")
        print("-------------------------详情------------------------------------")
        print(repr(response))

    def start_requests(self):
        #开启爬取之前先登录
        yield Request(
            url= self.login_url,
            meta={'cookiejar': 1},
            callback= self.login,
        )

    # 获取用户信息
    def _get_user_info(self, html, url):
        key = "page_id=(\d+)"
        # page_id 只会出现在公共主页上，所以根据page_id来判断页面类型
        pattern = re.compile(key)
        it = pattern.finditer(html)
        user_type = 0
        user_item = TopUserItem()

        try:
            it = next(it)
            user_type = TopUser.PUBLIC_PAGE

        except StopIteration:
            # 未找到page_id 此时视为个人主页
            key = "profile_id=(\d+)"
            pattern = re.compile(key)
            it = pattern.finditer(html)
            try:
                it = next(it)
                user_type = TopUser.PRIVATE_PAGE
            except StopIteration:
                # 两个都没找到，此时视为页面错误，返回错误，爬虫停止
                user_item["user_id"] = None
                user_item["user_type"] = 0
                return user_item

        try:
            user_item["user_type"] = user_type
            user_item["user_id"] = it.group(1)
        except IndexError:
            user_item["user_id"] = None
            user_item["user_type"] = 0
            return user_item

        return user_item

    def _isUserExit(self, user_name):
        dbOpr = dbInit()
        rowset = dbOpr.query(func.count("1")).filter(TopUser.user_name == user_name)
        return True if rowset[0][0] == 1 else False

    def close(spider, reason): #当其关闭的时候调用，打开爬虫爬取用户的发帖信息
        print("用户爬取完毕，准备爬取发帖信息")
        cmdline.execute('scrapy crawl FBPostSpider'.split())