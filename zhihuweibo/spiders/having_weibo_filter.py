# -*- coding: utf-8 -*-
import scrapy
import json
import re
from zhihuweibo.items import ZhihuUser

class ZhihuSpider(scrapy.Spider):
    name = "zhihu_weibo_filter"
    cookies_file='cookies.txt'
    cookies=[]
    USER_MINIMUM_ANSWERS = 10
    MAX_CRAWL_FOLLOWEES = 500
    MAX_CRAWL_FOLLOWERS = 500
    users_file = 'zhihuuser_nf.txt'
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
        yield scrapy.Request(url="https://www.zhihu.com",
                               cookies=self.cookies)

    def parse(self, response): # After logined
        if response.css('a.zu-top-nav-userinfo span.name'): # login success
            with open(self.users_file,'r') as f:
                for line in f.readlines():
                    self.user_list.append(line.strip())
            for user_href in self.user_list:
                url = "https://www.zhihu.com" + user_href
                check_having_weibo =  scrapy.Request(url=url,callback=self.filter_having_weibo)
                check_having_weibo.meta['user_href'] = user_href
                yield check_having_weibo
        else:
            print('登录失败')
        
    def filter_having_weibo(self, response): #该用户关注的人/粉丝中有微博的 本解析参考：个人主页
        user_href = response.meta['user_href']
        total_selector = "div.zm-profile-side-following > a:nth-child({0}) > strong::text"
        followees = int(response.css(total_selector.format(1)).extract_first())
        followers = int(response.css(total_selector.format(2)).extract_first())
        if response.css('a.zm-profile-header-user-weibo') and (followers > 100) and (followees > 100):
            yield ZhihuUser(user_href=user_href)
