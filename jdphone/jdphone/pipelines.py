# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
from pymongo import MongoClient
from scrapy.conf import settings


class JdphonePipeline(object):

    def __init__(self):
        # 获取settings里的配置
        host = settings['MONGODB_HOST']
        port = settings['MONGODB_PORT']
        dbname = settings['MONGODB_DBNAME']
        col = settings['MONGODB_COL']
        # 创建一个mongo实例
        client = MongoClient(host=host, port=port)

        # 访问数据库
        db = client[dbname]

        # 访问集合
        self.col = db[col]

    def process_item(self, item, spider):
        data = dict(item)
        self.col.insert(data)
        return item
