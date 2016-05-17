# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html


class ZhihuweiboPipeline(object):
    def process_item(self, item, spider):
        user_id = item.get('user_id')
        followee_id = item.get('followee_id')
        line = '{0} {1}\n'.format(user_id,followee_id)
        with open('relations.txt', 'a') as f:
            f.write(line)
        return item