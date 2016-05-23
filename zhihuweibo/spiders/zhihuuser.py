# -*- coding: utf-8 -*-
import scrapy
import json
import re
from zhihuweibo.items import ZhihuUser

class ZhihuSpider(scrapy.Spider):
    name = "zhihuuser"
    cookies_file='cookies.txt'
    cookies=[]
    topic_urls=[]
    
    def save_cookies(self, cookies):
        with open(self.cookies_file, 'w') as f:
            f.write(json.dumps(cookies))

    def load_cookies(self):
        dumps = ''
        with open(self.cookies_file, 'r') as f:            
            dumps = f.read()
        cookies = json.loads(dumps)
        return cookies
    def load_topics(self):
        with open('topiccollect.txt','r') as f:
            for line in f.readlines():
                self.topic_urls.append(line.strip())

    def start_requests(self):
        self.cookies = self.load_cookies()
        yield scrapy.Request(url="https://www.zhihu.com",
                               cookies=self.cookies)

    def parse(self, response): # After logined
        self.load_topics()
        for topic_page in self.topic_urls:    
            yield scrapy.Request(url=topic_page,callback=self.extract_user)

    def extract_user(self, response):
        userlist = response.css('a.author-link::attr(href)').extract()
        for user_href in userlist:
            yield ZhihuUser(user_href=user_href)





        