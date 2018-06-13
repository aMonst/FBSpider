# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy
class FBConfigItem(scrapy.Item):
    cookie = scrapy.Field()
    access_token = scrapy.Field()

#保存用户发帖的信息
class FbspiderItem(scrapy.Item):
    table_name = scrapy.Field()
    post_id = scrapy.Field()
    post_user = scrapy.Field()
    post_message = scrapy.Field()
    post_time = scrapy.Field()
    post_link = scrapy.Field()

    def __init__(self):
        super(FbspiderItem, self).__init__()
        FbspiderItem.table_name = "user_post"

#用户信息
class TopUserItem(scrapy.Item):
    PUBLIC_PAGE = 1 #公共主页
    PRIVATE_PAGE = 2 #个人主页
    table_name = scrapy.Field()
    user_id = scrapy.Field()
    user_name = scrapy.Field()
    user_type = scrapy.Field()
    user_level = scrapy.Field()

    def __init__(self):
        super(TopUserItem, self).__init__()
        TopUserItem.table_name = "top_user"

#保存帖子的图片信息
class FBPostImgItem(scrapy.Item):
    table_name = scrapy.Field()
    post_id = scrapy.Field()
    img_url = scrapy.Field()

    def __init__(self):
        super(FBPostImgItem, self).__init__()
        FBPostImgItem.table_name = "post_img"

#获取用户的好友信息
class FBUserItem(scrapy.Item):
    table_name = scrapy.Field()
    user_name = scrapy.Field()
    friend_name = scrapy.Field()

    def __init__(self):
        super(FBUserItem, self).__init__()
        FBUserItem.table_name = "user_friends"

class UserComment(scrapy.Item):
    table_name = scrapy.Field()
    user_id = scrapy.Field()
    user_name = scrapy.Field()
    post_id = scrapy.Field()
    comment = scrapy.Field()

    def __init__(self):
        super(UserComment, self).__init__()
        UserComment.table_name = "user_comment"