# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import redis

class ZhihuweiboPipeline(object):

    def __init__(self):
        self.r = redis.StrictRedis(host='localhost',port=6379,db=1)

    def process_item(self, item, spider):
        if 'user_id' in item:
            user_id = item.get('user_id')
            followee_id = item.get('followee_id')
            relation = '{0} {1}'.format(user_id,followee_id)
            if not self.r.exists('relation:'+relation):
                self.r.set('relation:'+relation,1)
                with open('relations.txt', 'a') as f:
                    f.write(relation+'\n')
                return item

        if 'user_href' in item:
            user_href = item.get('user_href')
            if not self.r.exists('user_href:'+user_href):
                self.r.set('user_href:'+user_href,1)
                with open('zhihuuser.txt', 'a') as f:
                    f.write(user_href+'\n')
                return item
                
        # if 'user_href' in item: #!!临时！！
        #     user_href = item.get('user_href')            
        #     with open('zhihuuser.txt', 'a') as f:
        #         f.write(user_href+'\n')
        #     return item
        # if 'user_id' in item:
        #     user_id = item.get('user_id')
        #     followee_id = item.get('followee_id')
        #     relation = '{0} {1}'.format(user_id,followee_id)
        #     with open('relations.txt', 'a') as f:
        #         f.write(relation+'\n')
        #     return item
