# -*- coding: utf-8 -*-
import scrapy
import json
import re


class ZhihuSpider(scrapy.Spider):
    name = "zhihuinfo"
    cookies_file='cookies.txt'
    cookies=[]

    users_file = ''
    user_list=[]
    def save_cookies(self, cookies):
        with open(self.cookies_file, 'w') as f:
            f.write(json.dumps(cookies))

    def load_cookies(self):
        dumps = ''
        with open(self.cookies_file, 'r') as f:            
            dumps = f.read()
        cookies = json.loads(dumps)
        return cookies

    def start_requests(self):        
        self.cookies = self.load_cookies()
        yield scrapy.Request(url="https://weibo.cn",
                               cookies=self.cookies)

    def parse(self, response): # After logined        
        if response.css('a.zu-top-nav-userinfo span.name'): # login success
            with open(self.users_file,'r') as f:
                for line in f.readlines():
                    self.user_list.append(line.strip())
            for user_href in self.user_list:
                pass
        else:
            print('------登录失败------')