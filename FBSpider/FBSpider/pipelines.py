# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
from FBSpider.ReadConfig import ReadConfig
from FBSpider.items import *
from FBSpider.dbHelper import *
from scrapy.http.request import Request
from urllib.parse import urljoin
import pymysql

class FbspiderPipeline(object):
    def process_item(self, item, spider):
        if isinstance(item, FBConfigItem):
            self.FBConfigItemParse(item, spider)
        else:
            if hasattr(item, "table_name"):
                col_str = ""
                row_str = ""
                val_str = ""

                for key in item.keys():
                    col_str = col_str + key + ","
                    if type(item[key]) == type(1):
                        row_str = row_str + "%d" % item[key] + ","
                        val_str = val_str + key + "=" + "%d" % item[key] + ","
                    elif type(item[key]) == type('1'):
                        temp = item[key].replace("'", "\\'")
                        row_str = row_str + "'%s'" % temp + ","
                        val_str = val_str + key + "=" + "'%s'" % temp + ","
                    elif item[key] == None:
                        row_str = row_str + "''" + ","
                        val_str = val_str + key + "=" + "''" + ","

                row_str = row_str[:-1]
                col_str = col_str[:-1]
                val_str = val_str[:-1]

                sql = "insert into %s(%s)values(%s) ON DUPLICATE KEY UPDATE %s" % (item.table_name, col_str, row_str, val_str)
                conn = dbInit()
                result = conn.exec_sql(sql)
                conn.commit()

                print("sql:%s执行成功" % sql)

    def FBConfigItemParse(self, item, spider):
        config = ReadConfig()
        config.addValue("access_token", item["access_token"])
        config.addValue("cookie", item["cookie"])
        config.reWrite()