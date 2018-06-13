# -*- encoding:utf-8-*-
#主要用来处理配置文件
import requests
import codecs
from urllib.parse import urlparse
import codecs
import pkgutil
from io import StringIO
import os.path
import random


class ReadConfig:
    def __init__(self, **kwargs):
        self._config = {}
        if "path" in kwargs:
            self.path = kwargs["path"]
        else:
            base_dir = os.path.dirname(__file__)
            self.path = os.path.join(base_dir, "FBSpider.config")

        f = codecs.open(self.path, "r", encoding="ascii")
        for item in f.readlines():
            sp = item.split("=")
            self._config[sp[0].strip()] = sp[1].strip()

        f.close()

    def getValue(self, key):
        return self._config[key]

    def addValue(self, key, value):
        self._config[key] = value

    def updateValue(self, key, value):
        self._config[key] = value

    def hasKey(self, key):
        return True if key in self._config else False

    def reWrite(self):
        f = codecs.open(self.path, "w", "utf-8")
        for key in self._config.keys():
            line = key + " = " + self._config[key] + "\r\n"
            f.write(line)

        f.close()

    def getRnadomProxy(self):
        data = self._config["proxy"]
        proxies = data.split(",")
        url = random.choice(proxies)
        urlParse = urlparse(url)
        return urlParse.scheme, urlParse.hostname, urlParse.port

    def getRandomLoginUser(self):
        users = self.getLoginUsers()
        if not users:
            return False

        user = random.choice(users)
        return user[0], user[1]

    def getLoginUsers(self):
        if not self.hasKey("login_users"):
            return False

        data = self._config["login_users"].split(";")
        users = []
        for user in data:
            user = tuple(eval(user))
            users.append(user)

        return users


