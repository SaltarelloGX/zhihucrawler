# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class ZhihuweiboItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass

class Relation(scrapy.Item):
    user_id = scrapy.Field()
    followee_id = scrapy.Field()

class ZhihuUser(scrapy.Item):
    user_href = scrapy.Field()