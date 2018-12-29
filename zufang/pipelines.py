# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import pymongo

class ZufangPipeline(object):
    collection = 'gz'
    def __init__(self,mongo_uri,db_name,db_user,db_pass):
        self.mongo_uri = mongo_uri
        self.db_name = db_name
        self.db_user = db_user
        self.db_pass = db_pass

    #重构类的时候不必要修改构造函数，只需要额外添加你要处理的函数
    @classmethod
    def from_crawler(cls,crawler):
        return cls(
            mongo_uri=crawler.settings.get('MONGO_URI'),
            db_name=crawler.settings.get('DB_NAME'),
            db_user=crawler.settings.get('DB_USER'),
            db_pass=crawler.settings.get('DB_PASS'))

    def open_spider(self,spider):
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.zfdb = self.client[self.db_name]
        # self.zfdb.authenticate(self.db_user, self.db_pass)

    def close_spider(self,spider):
        self.client.close()

    def process_item(self, item, spider):
        self.collection = item['region']
        if item['region']=='不限':
            item['region'] = item['address'][0:2]
        data = {
            "title": item["title"].strip(),
            "rooms": item["rooms"],
            "area": item["area"],
            "price": item["price"],
            "address": item["address"],
            "traffic": item["traffic"],
            "region": item["region"],
            "direction": item["direction"],
        }
        self.zfdb[self.collection].update_one(data,{'$set':data},upsert=True)
        return item
