#-*- encoding:utf-8 -*-
# 数据库操作类
# import pymysql
# from twisted.enterprise import adbapi
# import pymysql.cursors
# from scrapy.utils.project import get_project_settings
# import scrapy.item
# import six
# from FBSpider.items import *
# from DBUtils.PooledDB import  PooledDB
#
# class dbHelper:
#     def __init__(self):
#         self.settings = get_project_settings()
#         self.dbpramas = dict(
#             host=self.settings["MYSQL_HOST"],
#             db=self.settings["MYSQL_DBNAME"],
#             user=self.settings["MYSQL_USER"],
#             passwd=self.settings["MYSQL_PASSWD"],
#             use_unicode = True,
#             charset="utf8",
#             cursorclass=pymysql.cursors.DictCursor,
#         )
#
# #        self.dbpool = adbapi.ConnectionPool("pymysql", **self.dbpramas)
#         self.dbpool = PooledDB(pymysql,
#                                50 ,
#                                host = self.dbpramas["host"],
#                                user = self.dbpramas["user"],
#                                passwd = self.dbpramas['passwd'],
#                                db= self.dbpramas["db"],
#                                port = 3306,
#                                charset = self.dbpramas["charset"]
#                         )
#
#     def connect(self):
#         return self.dbpool
#
#     def insert(self, item):
#         if hasattr(item, "table_name"):
#             col_str = ""
#             row_str = ""
#             val_str = ""
#
#             for key in item.keys():
#                 col_str = col_str + key + ","
#                 if type(item[key]) == type(1):
#                     row_str = row_str + "%d" % item[key] + ","
#                     val_str = val_str + key + "=" + "%d" % item[key] + ","
#                 elif type(item[key]) == type('1'):
#                     temp = item[key].replace("'", "\\'")
#                     row_str = row_str + "'%s'" % temp + ","
#                     val_str = val_str + key + "=" + "'%s'" % temp + ","
#                 elif item[key] == None:
#                     row_str = row_str + "''" + ","
#                     val_str = val_str + key + "=" + "''" + ","
#
#             row_str = row_str[:-1]
#             col_str = col_str[:-1]
#             val_str = val_str[:-1]
#
#             sql = "insert into %s(%s)values(%s) ON DUPLICATE KEY UPDATE %s" % (item.table_name, col_str, row_str, val_str)
#             # query = self.dbpool.runInteraction(self._conditional_insert, sql)
#             # query.addErrback(self._error_handler, sql)
#
#             conn = self.dbpool.connection()
#             cur = conn.cursor()
#             cur.execute(sql)
#             cur.close()
#             conn.close()
#
#     def _conditional_insert(self, tx, sql):
#         tx.execute(sql)
#
#     def _error_handler(self, err, sql):
#         print("--------------------------database operation exception!-------------------------------")
#         print("error sql:%s" % sql)
#         print("%s" % err)
#
#     def exec_sql(self, sql):
#         # db = pymysql.connect(self.dbpramas["host"], self.dbpramas["user"], self.dbpramas["passwd"], self.dbpramas["db"], use_unicode = True, charset = "utf8")
#         # cursor = db.cursor()
#         #
#         # cursor.execute(sql)
#         # data = cursor.fetchall()
#         # db.close()
#
#         conn = self.dbpool.connection()
#         cur = conn.cursor()
#         cur.execute(sql)
#         data = cur.fetchall()
#         cur.close()
#         conn.close()
#
#         return data
#
# dbOpr = dbHelper()

from sqlalchemy import Column, ForeignKey, create_engine, UniqueConstraint, and_, MetaData, func
from sqlalchemy.types import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import *
from scrapy.utils.project import get_project_settings
#创建对象基类
BaseModel = declarative_base()
metadata = MetaData()

def InitConnectPool():
    settings = get_project_settings()
    dbtype = "mysql"
    dbEngine = "pymysql"
    user = settings["MYSQL_USER"]
    password = settings["MYSQL_PASSWD"]
    dbIp = "localhost"
    dbPort = "3306"
    database = settings["MYSQL_DBNAME"]
    try:
        charset = "utf8"
        conn_str = dbtype + "+" + dbEngine + "://" + user + ":" + password + "@" + \
                        dbIp + ":" + dbPort + "/" + database + "?" + "charset=" + charset
    except KeyError:
        conn_str = dbtype + "+" + dbEngine + "://" + user + ":" + password + "@" + \
                        dbIp + ":" + dbPort + "/" + database
    engine = create_engine(conn_str, pool_size = 200, pool_recycle=5, pool_timeout=30, max_overflow=0)
    return engine

class dbInit:
    _conn_pool = None

    def __init__(self):
        if dbInit._conn_pool == None:
            dbInit._conn_pool = InitConnectPool()

        self.engine = dbInit._conn_pool
        self.session = scoped_session(
            sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
        )

    def add(self, obj):
        try:
            self.session.add(obj)
        except:
            return False

    def adds(self, objs):
        try:
            self.session.add_all(objs)
        except:
            return False

    def query(self, *args):
        try:
            return self.session.query(*args)
        except:
            return None

    def getSession(self):
        return self.session

    def commit(self):
        try:
            self.session.commit()
        except:
            return False

    def create_tables(self):
        return BaseModel.metadata.create_all(self.engine)

    def delete(self, obj):
        return self.session.delete(obj)

    def exec_sql(self, sql_str, **kwargs):
        try:
            return self.session.execute(sql_str, kwargs)
        except:
            return None

    def __del__(self):
        self.session.close()

class TopUser(BaseModel):
    PUBLIC_PAGE = 1
    PRIVATE_PAGE = 2
    __tablename__ = 'top_user'
    user_id = Column(String, primary_key= True)
    user_name = Column(String)
    user_type = Column(Integer)
    user_level = Column(Integer)

class UserFriends(BaseModel):
    __tablename__ = "user_friends"
    id = Column(Integer, primary_key= True)
    user_name = Column(String)
    friend_name = Column(String)
    __table_args__ = (
        UniqueConstraint("user_name", 'friend_name'),
    )

class UserPosts(BaseModel):
    __tablename__ = "user_post"
    post_id = Column(String, primary_key= True)
    post_user = Column(String, ForeignKey("top_user.user_id"))
    post_message = Column(String)
    post_time = Column(String)
    post_link = Column(String)

class PostImg(BaseModel):
    __tablename__ = "post_img"
    id = Column(Integer, primary_key=True)
    post_id = Column(String)
    img_url = Column(String)
