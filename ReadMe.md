FBSpider
====================
# 需求
1. 抓FB上一个用户的底下3层内容
2. 第一层：用户好友和用户发布的内容（包括图片）
3. 第二层：第一层爬到的用户的好友和用户发布的内容（包括图片）
4. 第三层：第二层得到的用户的好友

# 数据库设计
## top_user:用户表
用户表，用来存储所有用户信息，以便后续根据该表内容进行用户发帖爬取

|字段|含义|数据类型|长度|备注|
|:---|:---|:-------|:---|:---|
|user_name|用户名|Char|32||
|user_id|用户ID|char|32|primary key|
|user_type|用户类型|Integer||1：公共用户 2：私人用户|
|user_level|用户层级|Integer||记录用户之前的关系，从外部导入的用户为1级，由一级用户通过好友关系查找到的为2级用户，并以此类推|

## user_post：用户信息表
用来保存用户发布的信息，不包括图片

|字段|含义|数据类型|长度|备注|
|:---|:---|:-------|:---|:---|
|post_id|信息ID|char|32|primary key|
|user_id|发布该条信息的用户|char|32|foreign key|
|post_message|发布内容|string|||
|post_time|发布时间|string|||
|post_link|信息所对应的URL|string|||

## post_img: 内容中包含的图片信息
|字段|含义|数据类型|长度|备注|
|:---|:---|:-------|:---|:---|
|id|记录ID|integer||primary key|
|post_id|对应信息ID|char|32|foreign key|
|img_url|图片所在路径|char|32||

## user_friends 用户关系表
|字段|含义|数据类型|长度|备注|
|:---|:---|:-------|:---|:---|
|id|记录ID|integer||primary key|
|user_name|用户名称|char|32|primary key, foreign key|
|friend_name|好友用户名称|char|32||

## user_comment 用户评论表
|字段|含义|数据类型|长度|备注|
|:---|:---|:-------|:---|:---|
|user_id|评论的用户id|char|16|primary key|
|user_name|评论用户的名称|char|255||
|post_id|对应帖子的ID|char|32|primary key|
|comment|评论的内容|mediumtext||



# 开发方案
1. 语言：python3
2. 开发平台: windows
3. 开发工具: pycharm
4. 使用的第三方库: scrapy + sqlalchemy + pymysql + scrapy_splash

# 程序运行环境配置
## python 环境的安装
请到python官方网站下载对应的python版本(开发使用的版本为3.6.4)，Linux下可能自带python3环境，若没有请自行百度并下载编译对应的python版本

## 第三方库的安装配置
### virtualenv安装(可以跳过这一步， 但是为了保持系统python环境的干净以及后续迁移问题，推荐安装)
推荐使用virtualenv将各个程序的python环境进行隔离，安装请使用如下命令
```shell
pip install virtualenv
```
linux 下也可以使用命令
```shell
apt-get install virtualenv
```
安装完成之后，进入到对应的目录中使用命令
```shell
virtualenv env --python=python3 --no-site-packages
```
env：代表虚拟环境的名称
--python=python3：代表使用的python环境，如果系统提示找不到对应的python文件，请使用绝对路径或者将对应路径加入到环境变量中
--no-site-packages: 创建一个不带任何第三方扩展包的干净的虚拟环境，为了成功安装scrapy，请使用该选项

linux下使用命令
```shell
source env/bin/activate
```
Windows下使用命令
```shell
cd env/Scripts
activate.bat
```
使用对应命令激活虚拟环境，当看到出现类似这样的命令行界面(前面会出现一个虚拟环境的名称)时就表示成功
```shell

(env) D:\PythonProgram\FBSpider>
```
### 安装程序依赖库
项目m目录中有一个piplist.txt文件，该文件中记录了当前环境中所使用的python库，在虚拟环境中使用
```shell
pip install -r piplist.txt
```
安装里面的所有环境

### 安装程序需要的软件环境
对于Linux或者Windows 10 企业版可以直接安装docker
对于Windows 7或者Windows 10家庭版需要安装docker toolbox
成功安装docker后使用命令
```shell
docker pull scrapinghub/splash
```
拉取对应镜像.完成之后启动splash
```shell
sudo docker run -p 5053:5053 -p 8050:8050 -p 8051:8051 scrapinghub/splash --timeout=3600
```
三个-p后的内容分别为 ssh连接的端口、http连接的端口和https的端口
timeout 是超时时间，单位为s

最后安装对应的mysql服务并保证能从对应机器上连接到数据库中
需要修改mysql配置如下：
```
[client] #增加的内容
port  = 3306
socket  = /tmp/mysql.sock
default-character-set = utf8mb4

[mysql]
default-character-set = utf8mb4

[mysqld] #修改的内容
port  = 3306
socket  = /tmp/mysql.sock
character-set-server=utf8
character-set-filesystem = utf8
sql_mode = STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION
character-set-client-handshake = FALSE
character-set-server = utf8mb4
collation-server = utf8mb4_unicode_ci
init_connect='SET NAMES utf8mb4'
```
请对照这些配置信息修改mysql的配置文件,Windows中配置文件位于对应安装目录下的my.ini中，Linux中一般位于/etc/mysql/my.cnf中
配置完成之后请重启mysql服务
```shell
# linux下
/etc/init.d/ mysql restart
#或者
service mysql restart

#Windows下，使用管理员权限启动cmd
net stop mysql
net start mysql
```

### 创建数据库和表结构
首先在mysql中创建一个名为fbspider的数据库
对应的字符集为utf8mb4 -- UTF-8 Unicode，排序规则为:utf8mb4_unicode_ci
在数据库中执行下面的sql命令创建对应的表结构

```sql
SET FOREIGN_KEY_CHECKS=0;

-- ----------------------------
-- Table structure for post_img
-- ----------------------------
DROP TABLE IF EXISTS `post_img`;
CREATE TABLE `post_img` (
  `post_id` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `img_url` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `id` int(11) NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=28 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for top_user
-- ----------------------------
DROP TABLE IF EXISTS `top_user`;
CREATE TABLE `top_user` (
  `user_name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `user_id` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `user_type` tinyint(4) NOT NULL,
  `user_level` tinyint(4) NOT NULL,
  PRIMARY KEY (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for user_friends
-- ----------------------------
DROP TABLE IF EXISTS `user_friends`;
CREATE TABLE `user_friends` (
  `user_name` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `friend_name` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `id` int(11) NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_name` (`user_name`,`friend_name`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=61 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for user_post
-- ----------------------------
DROP TABLE IF EXISTS `user_post`;
CREATE TABLE `user_post` (
  `post_id` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `post_user` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL,
  `post_message` mediumtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `post_time` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `post_link` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`post_id`),
  KEY `post_user` (`post_user`),
  CONSTRAINT `user_post_ibfk_1` FOREIGN KEY (`post_user`) REFERENCES `top_user` (`user_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
SET FOREIGN_KEY_CHECKS=1;
```

# 配置文件的相关说明
在项目中主要有3个配置文件，分别为users.txt、FBSpider.config、settings.py
1. user.txt:主要保存需要导入的用户信息，只需要提供用户名或者用户ID
>如何获取用户名或者用户ID：在用户对应主页上有两个格式的URL，类似于:https://www.facebook.com/ogyen.gyeltsen.1或者https://www.facebook.com/profile.php?id=100026173923202,针对第一种URL，可以得到用户名为ogyen.gyeltsen.1,对于第二种URL只能使用id来爬取id为100026173923202

2. FBSpider.config:主要存储程序所使用的一些外部资源信息，比如代理，爬取所需要的登录用户
**请注意，每种配置内容只能在同一行，且必须严格遵守下面给出的格式来进行配置**
- proxy: 使用的代理，每个代理请使用 协议://ip:端口这种格式，每个代理间使用逗号隔开
- flush_times: 下拉页面的次数，下拉页面是为了爬取用户后面加载出来的信息，这次数尽量不要太大，当程序多次刷新时可能会超过这个超时值此时会报错并终止爬取该用户的信息
- login_users: 登录用户，请使用("用户名","密码")的格式来给出，多个登录用户间使用逗号隔开

3. settings.py:程序运行相关的参数信息
- SPLASH_URL: splash 程序所对应的URL,主要由协议 + ip + 端口3个部分组成
- DOWNLOAD_DELAY: 下载延时，每次发包前会有这个延时，减缓爬取速度，防止速度过快而被封号
- LOG_FILE：日志文件保存的位置
- MYSQL_HOST: mysql所在的主机IP
- MYSQL_PORT: mysql端口
- MYSQL_DBNAME: 数据库名称
- MYSQL_USER: 登录数据的用户名
- MYSQL_PASSWD: 登录数据库的密码

# 更新记录
1. 20180524：完成第一版
2. 根据客户需求新增爬取用户帖子的评论，以及评论人对应的发帖和好友信息