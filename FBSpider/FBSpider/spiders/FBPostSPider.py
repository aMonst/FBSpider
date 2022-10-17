import scrapy
from FBSpider.items import *
from urllib.parse import urljoin, urlparse
from scrapy.http.request import Request
from scrapy_splash import SplashRequest, SplashFormRequest
import codecs
from FBSpider.LuaScript import *
from FBSpider.settings import *
from FBSpider.ReadConfig import ReadConfig
import os.path
import json
from scrapy.selector import Selector
from FBSpider.dbHelper import *
import random
import queue
import re

class TaskInfo(object):
    user_id = ""
    user_name = ""
    user_level = ""
    user_type = ""

class FBPostSpider(scrapy.Spider):
    name = 'FBPostSpider'
    def __init__(self, *args, **kwargs):
        super(FBPostSpider, self).__init__(*args, **kwargs)
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

        self.tasks = queue.Queue()
        self.cookie = []
        self.start_users = []
        self.getUsers() # 从文件中导入的用户信息
        self.deal = set() #保存已处理的用户信息
        self.config = ReadConfig()
        self.Inited = False   #是否完成初始化

    def isInitSuccess(self): #是否完成了初始化
        return self.Inited

    def login(self, response):
        users = self.config.getLoginUsers()
        if not users:
            print("请在配置文件中至少指定一个登陆用户信息")
            return

        if self.config.hasKey("proxy"):
            proto, host, port = self.config.getRnadomProxy()
            user_proxy = USE_PROXY % (host, port, proto)
        else:
            user_proxy = ""

        lua_script = LOGIN % user_proxy

        for user in users:
            yield SplashFormRequest.from_response(
                response,
                url=self.login_url,
                formdata={
                    "email": user[0],
                    "pass": user[1]
                },
                endpoint="execute",
                args={
                    "wait": 30,
                    "lua_source": lua_script,
                    "user_name": user[0],
                    "user_passwd": user[1],
                },
                callback=self.after_login,
                errback=self.error_parse,
            )

    def after_login(self, response):
        #登录成功的话页面会跳转到主页
        if response.data["url"] == self.login_url:
            print("登录失败，即将关闭爬虫.....")
            self.Inited = True
            return

        self.cookie.append(response.data["cookies"])  # 保存cookie

    def get_start_request(self):
        # 登录成功后请求用户主页，爬取用户主页信息
        requests = []
        if self.cookie == []:
            return requests

        for user in self.start_users:
            url = urljoin("https://www.facebook.com/", user)
            if self.config.hasKey("proxy"):
                proto, host, port = self.config.getRnadomProxy()
                user_proxy = USE_PROXY % (host, port, proto)
            else:
                user_proxy = ""

            lua_script = REQUEST_MAIN_PAGE % user_proxy

            request = SplashRequest(
                url=url,
                endpoint="execute",
                callback=self._get_user_page,
                meta={
                    "level": 1,
                    "user_name" : user
                },

                cookies=random.choice(self.cookie),
                args={
                    "wait": 30,
                    "lua_source": lua_script,
                }
            )

            requests.append(request)

        self.start_users = [] # 第一次提交任务成功后不再提交，防止重复爬取

        return requests

    def make_requests_from_job(self):
        requests = []
        if not self.tasks.empty():
            task = self.tasks.get()
            if task.user_name in self.deal:
                return

            self.deal.add(task.user_name)
            if task.user_level == 4:
                return

            if task.user_type == TopUser.PUBLIC_PAGE:
                print("公共主页没有好友信息")
                # 公共主页通过API获取发帖信息
                access_token_url = "https://developers.facebook.com/tools/explorer/"

                if self.config.hasKey("proxy"):
                    proto, host, port = self.config.getRnadomProxy()
                    user_proxy = USE_PROXY % (host, port, proto)
                else:
                    user_proxy = ""

                lua_script = REQUEST_MAIN_PAGE % user_proxy

                request = SplashRequest(
                    url = access_token_url,
                    endpoint="execute",
                    callback=self.get_access_token,

                    cookies=random.choice(self.cookie),
                    meta={
                        "user": task.user_id,
                        "level": task.user_level
                    },

                    args={
                        "wait": 30,
                        "lua_source": lua_script,
                    }
                )

                requests.append(request)


            elif task.user_type == TopUser.PRIVATE_PAGE:
                api = urljoin("https://www.facebook.com", task.user_id)
                if self.config.hasKey("proxy"):
                    proto, host, port = self.config.getRnadomProxy()
                    user_proxy = USE_PROXY % (host, port, proto)
                else:
                    user_proxy = ""

                lua_script = GET_FRIEND_PAGE % user_proxy
                request = SplashRequest(
                    url=api,
                    cookies=random.choice(self.cookie),
                    endpoint="execute",
                    callback=self._get_friends_page,
                    meta={
                        "level": task.user_level,
                        "name": task.user_name
                    },

                    args={
                        "lua_source": lua_script,
                        "wait": 30,
                    }
                )

                requests.append(request)

                api = urljoin("https://www.facebook.com", task.user_id)
                if self.config.hasKey("proxy"):
                    proto, host, port = self.config.getRnadomProxy()
                    user_proxy = USE_PROXY % (host, port, proto)
                else:
                    user_proxy = ""

                if self.config.hasKey("flush_times"):
                    flush_times = self.config.getValue("flush_times")
                else:
                    flush_times = 0

                lua_script = REQUEST_COMPLETE_PAGE % (user_proxy, int(flush_times))
                request= SplashRequest(
                    cookies= random.choice(self.cookie),
                    url=api,
                    callback=self._get_private_posts,
                    errback=self._get_posts_error,
                    endpoint="execute",
                    meta={
                        "user": task.user_id,
                        "level": task.user_level
                    },

                    args={
                        "wait": 30,
                        "lua_source": lua_script,
                    }
                )

                requests.append(request)

        return requests

    def get_access_token(self, response):
        sel = Selector(response=response)
        access_token = sel.xpath('//label[@class="_2toh _36wp _55r1 _58ak"]/input[@class="_58al"]//@value').extract_first()

        api = urljoin("https://graph.facebook.com/v3.0", response.meta["user"])
        api = api + "/posts" + "?access_token=" + access_token + "&fields=link,id,message,full_picture,parent_id,created_time,comments"

        yield Request(
            url=api,
            meta={
                'cookiejar': 1,
                "user": response.meta["user"],
                "level" : response.meta["level"]
            },
            callback=self._get_public_posts,
            errback=self.error_parse
        )

    def error_parse(self, response):
        print("发生网络错误，即将停止相应的任务")
        print("-------------------------详情------------------------------------")
        print(repr(response))

    def start_requests(self):
        #开启爬取之前先登录
        yield Request(
            url= self.login_url,
            meta={'cookiejar': 1},
            callback= self.login,
        )


    def _get_public_posts(self, response):
        rep_json = json.loads(response.text)
        data = rep_json["data"]
        post_user = response.meta["user"]

        for post in data:
            try:
                item = FbspiderItem()
                item["post_id"] = post["id"]
                item["post_user"] = post_user
                item["post_message"] = post["message"]
                item["post_time"] = post["created_time"]
                item["post_link"] = post["link"]
                yield item

                item = FBPostImgItem()
                item["post_id"] = post["id"]
                item["img_url"] = post["full_picture"]
                yield  item

                comments = post["comments"]["data"]
                for comment in comments:
                    comment_id = comment["id"]
                    comment_msg = comment["message"]

                    url = urljoin("https://www.facebook.com", comment_id)
                    if self.config.hasKey("proxy"):
                        proto, host, port = self.config.getRnadomProxy()
                        user_proxy = USE_PROXY % (host, port, proto)
                    else:
                        user_proxy = ""

                    lua_script = REQUEST_MAIN_PAGE % (user_proxy)
                    yield SplashRequest(
                        cookies=random.choice(self.cookie),
                        url = url,
                        callback=self._get_comment_user,
                        endpoint="execute",
                        meta= {
                            "level" : response.meta["level"],
                            "message" : comment_msg,
                            "post_id" : post["id"],
                        },
                        args={
                            "wait": 30,
                            "lua_source": lua_script,
                        }
                    )

            except KeyError: # 暂时不处理未找到帖子内容的情况
                continue

        if "paging" not in rep_json:
            return

        paging = rep_json["paging"]
        if "next" in paging:
            api = paging["next"]
            yield Request(
                url = api,
                callback= self._get_public_posts,
                meta={"user" : post_user},
            )

    def _get_posts_error(self, response):
        print("当前有超时错误,将停止对该用户的帖子搜集")

    def _get_private_posts(self, response):
        sel = Selector(response = response)
        posts = sel.xpath("//div[@class = '_5pcr userContentWrapper']")

        if self.config.hasKey("proxy"):
            proto, host, port = self.config.getRnadomProxy()
            user_proxy = USE_PROXY % (host, port, proto)
        else:
            user_proxy = ""

        lua_script = REQUEST_MAIN_PAGE % (user_proxy)

        for post in posts:
            comments = post.xpath("./div[2]")
            post = post.xpath("./div[1]")
            item = FbspiderItem()
            item["post_user"] = response.meta["user"]

            time_tag = post.xpath(".//abbr")
            item["post_time"] = time_tag.xpath(".//@title").extract_first()
            a_tag = time_tag.xpath(".//..") #获取父节点
            href = a_tag.xpath(".//@href").extract_first()

            item["post_link"] = urljoin("https://www.facebook.com", href)
            if item["post_link"].find("photo.php") != -1: #如果是图片则将fbid作为帖子ID
                parseUrl = urlparse(item["post_link"])
                params = parseUrl.query.split("&")
                for param in params:
                    if param.find("fbid=") != -1:
                        post_id = param[5:]
                        break
            else:
                if href[-1] == "/":
                    href = href[:-2]
                post_id = href.split("/")[-1]

            item["post_id"] = post_id
            item["post_message"] = post.xpath(".//p").extract_first()
            img_sel = post.xpath(".//div/img")

            for idx, img in enumerate(img_sel):
                if idx == 0: #第一个图片为用户头像，不用存储
                    continue

                img_item = FBPostImgItem()
                img_item["post_id"] = item["post_id"]
                img_item["img_url"] = img.xpath(".//@src").extract_first()
                try:
                    yield img_item
                except:
                    pass

            yield item

            comments = comments.xpath(".//span[@class = ' UFICommentActorAndBody']")
            for comment in comments:
                a_tag = comment.xpath(".//a[@class = ' UFICommentActorName']")
                user_name = a_tag.xpath(".//text()").extract_first()
                message = comment.xpath(".//span[@class = 'UFICommentBody']//span//text()").extract_first()
                user_page = a_tag.xpath(".//@href").extract_first()

                yield SplashRequest(
                    cookies=random.choice(self.cookie),
                    url=user_page,
                    callback=self._get_user_page,
                    endpoint="execute",
                    meta={
                        "level": response.meta["level"] + 1,
                        "message": message,
                        "post_id": item["post_id"],
                        "user_name": user_name
                    },

                    args={
                        "wait": 30,
                        "lua_source": lua_script,
                    }
                )

    def _get_comment_user(self, response):
        selector = Selector(response= response)
        a_tag = selector.xpath('//a[@class=" UFICommentActorName"]')
        user_name = a_tag.xpath(".//text()").extract_first()
        user_page = a_tag.xpath(".//@href").extract_first()

        if self.config.hasKey("proxy"):
            proto, host, port = self.config.getRnadomProxy()
            user_proxy = USE_PROXY % (host, port, proto)
        else:
            user_proxy = ""

        lua_script = REQUEST_MAIN_PAGE % (user_proxy)
        yield SplashRequest(
            cookies=random.choice(self.cookie),
            url=user_page,
            callback=self._get_user_page,
            endpoint="execute",
            meta={
                "level": response.meta["level"] + 1,
                "message": response.meta["message"],
                "post_id": response.meta["post_id"],
                "user_name" : user_name
            },
            args={
                "wait": 30,
                "lua_source": lua_script,
            }
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

    def getUsers(self):
        f = codecs.open(self.path, "r", encoding="utf-8")
        users = f.readlines()

        for user in users:
            user = user.strip("\r\n")
            self.start_users.append(user)

    def _get_friends_page(self, response):
        hasFriend = response.data["hasFriend"]
        if not hasFriend:
            print("用户[%s]未开放好友查询权限" % response.meta["name"])
            return

        sel = Selector(response = response)
        friends = sel.xpath("//a[@name='全部好友']")
        if friends == []:
            print("用户[%s]未开放好友查询权限" % response.meta["name"])
            return

        if self.config.hasKey("proxy"):
            proto, host, port = self.config.getRnadomProxy()
            user_proxy = USE_PROXY % (host, port, proto)
        else:
            user_proxy = ""

        if self.config.hasKey("flush_times"):
            flush_times = self.config.getValue("flush_times")
        else:
            flush_times = 0

        lua_script = FLUSH_FRIEND_PAGE % (user_proxy, int(flush_times))

        yield SplashRequest(
            url = response.data["url"],
            callback= self.parse_friends,
            endpoint="execute",
            cookies= random.choice(self.cookie),
            meta= {"level" : response.meta["level"], "name" : response.meta["name"]},
            args={
                "wait" : 30,
                "lua_source" : lua_script,
            }
        )

    def parse_friends(self, response):
        sel = Selector(response = response)
        friends = sel.xpath("//li[@class='_698']//div[@class='fsl fwb fcb']//a")

        if self.config.hasKey("proxy"):
            proto, host, port = self.config.getRnadomProxy()
            user_proxy = USE_PROXY % (host, port, proto)
        else:
            user_proxy = ""

        lua_script = REQUEST_MAIN_PAGE % user_proxy

        for friend in friends:
            url = friend.xpath(".//@href").extract_first()
            name = friend.xpath(".//text()").extract_first()

            level = response.meta["level"] + 1

            #记录当前好友关系
            friend_item = FBUserItem()
            friend_item["user_name"] = response.meta["name"]
            friend_item["friend_name"] = name

            print("提取到好友信息%s : %s" % (friend_item["user_name"], friend_item["friend_name"]))
            yield friend_item

            yield SplashRequest(
                url = url,
                endpoint="execute",
                callback= self._get_user_page,
                meta={"user_name" : name, "level" : level},
                cookies = random.choice(self.cookie),
                args={
                    "wait": 30,
                    "lua_source": lua_script,
                }
            )

    def _get_user_page(self, response):
        # 提取主页中的用户信息
        user_item = self._get_user_info(response.data["html"], response.url)
        if user_item["user_type"] == 0:
            print("未找到对应用户信息，可能是程序所使用的登录账号被封禁")
            self.Inited = True
            return

        user_item["user_level"] = response.meta["level"]
        user_item["user_name"] = response.meta["user_name"]

        print("提取到用户信息[%s]" % user_item["user_name"])

        task_info = TaskInfo()
        task_info.user_name = user_item["user_name"]
        task_info.user_level = user_item["user_level"]
        task_info.user_id = user_item["user_id"]
        task_info.user_type = user_item["user_type"]
        self.tasks.put(task_info)
        self.Inited = True

        yield user_item

        if "message" in response.meta:
            comment_item = UserComment()
            comment_item["user_id"] = user_item["user_id"]
            comment_item["user_name"] = response.meta["user_name"]
            comment_item["post_id"] = response.meta["post_id"]
            comment_item["comment"] = response.meta["message"]
            yield comment_item
