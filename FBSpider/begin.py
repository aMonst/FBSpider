from scrapy import cmdline

#cmdline.execute('scrapy crawl FBPostSpider'.split())
#cmdline.execute('scrapy crawl FBInitSpider'.split())
cmdline.execute('scrapy crawl FBUsersSpider'.split())

# import re
# import codecs
#
# if __name__ == '__main__':
#     f = codecs.open("C:\\Users\\Administrator\\Desktop\\test.html", "r", encoding="utf-8")
#     value = f.read()
#     f.close()
#
#     pattern = re.compile(r"profile_id=(\d+)")
#     it = pattern.finditer(value)
#     print(next(it).group(1))

# if __name__ == '__main__':
#     item = {
#         "user_id" : "100000485762440",
#         "user_type" : 2,
#         "user_name" : "stepstep.cheong"
#     }
#
#     col_str = ""
#     row_str = ""
#     val_str = ""
#
#     for key in item.keys():
#         col_str = col_str + key + ","
#         if type(item[key]) == type(1):
#             row_str = row_str + key + "=" + "%d" % item[key] + ","
#             val_str = val_str + "%d" % item[key] + ","
#         else:
#             row_str = row_str + key + "=" + "'%s'" % item[key] + ","
#             val_str = val_str + "'%s'" % item[key] + ","
#
#
#     col_str = col_str[:-1] #去掉多余的 ","
#     val_str = val_str[:-1]
#     row_str = row_str[:-1]
#
#     col_str = "(" + col_str + ")"
#     sql = "insert into top_user%s values (%s) ON DUPLICATE KEY UPDATE %s" %(col_str, val_str, row_str)
#     print(sql)

#
# if __name__ == '__main__':
    # item = {
    #     "user_id" : "1234567890",
    #     "user_name" : "masimaro",
    #     "user_type" : 1
    # }
    #
    # col_str = ""
    # row_str = ""
    # val_str = ""
    #
    # for key in item.keys():
    #     col_str = col_str + key + ","
    #     if type(item[key]) == type(1):
    #         row_str = row_str + "%d" % item[key] + ","
    #         val_str = val_str + key + "=" + "%d" % item[key] + ","
    #     else:
    #         row_str = row_str + "'%s'" % item[key] + ","
    #         val_str = val_str + key + "=" + "'%s'" % item[key] + ","
    #
    # row_str = row_str[:-1]
    # col_str = col_str[:-1]
    # val_str = val_str[:-1]
    #
    # sql = "insert into top_user(%s)values(%s) ON DUPLICATE KEY UPDATE %s" %(col_str, row_str, val_str)

# import requests
#
# if __name__ == '__main__':
#     header = {
#         "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
#         "Accept-Encoding": "gzip, deflate",
#         "Accept-Language": "zh-CN,zh;q=0.8,en;q=0.6",
#         "Cache-Control": "no-cache",
#         "Connection": "keep-alive",
#         "Content-Type": "application/x-www-form-urlencoded",
#         "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.75 Safari/537.36",
#         "Referer": "https://www.facebook.com/",
#     }
#
#     proxies = {
#         "http": "https://192.168.1.178:1080",
#         "https": "http://192.168.1.178:1080",
#     }
#     api = "https://graph.facebook.com/v2.12/100000485762440/friendlists?access_token=EAAGSdoBKSIgBALgSzNwDKda7k1ZC2HJAQskUxuxjwHlx1WFQw6XyZCHZAGKuybD8HOdPwu5wQ4lGtFFYNvIXnHIHc4ZAxSORuHL2SJxfPlJQoOQPTeAgb4F0m85Eqa7UmpOxUoXVDSAhfUWcYPMSRh7cUcO6AnzQGtnHuoaCm9bdgWC5HR1jAeUdTAPy2TfGzoZBIjgUSZBANZAtDPzwjlo"
#     response = requests.get(api, proxies = proxies, headers = header)
#     print(response.json())

