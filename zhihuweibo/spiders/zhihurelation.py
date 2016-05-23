# -*- coding: utf-8 -*-
import scrapy
import json
import re
from bs4 import BeautifulSoup
from zhihuweibo.items import Relation
import redis

class ZhihuSpider(scrapy.Spider):
    name = "zhihurelationsupplement"
    cookies_file='cookies.txt'
    cookies=[]
    USER_MINIMUM_ANSWERS = 10
    MAX_CRAWL_FOLLOWEES = 201 # 翻页用
    MAX_CRAWL_FOLLOWERS = 201
    offset_start = 20
    users_file = 'zhihuuser_l2-4.txt'
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
        self.redis_user = redis.StrictRedis(host='localhost',port=6379,db=1)
        self.cookies = self.load_cookies()
        yield scrapy.Request(url="https://www.zhihu.com",
                               cookies=self.cookies)

    def parse(self, response): # After logined
        if response.css('a.zu-top-nav-userinfo span.name'): # login success
            with open(self.users_file,'r') as f:
                for line in f.readlines():
                    self.user_list.append(line.strip())
            for user_href in self.user_list:
                url1 = 'https://www.zhihu.com'+user_href+'/followees'
                url2 = 'https://www.zhihu.com'+user_href+'/followers'
                yield scrapy.Request(url=url1,callback=self.search_followees_or_followers)
                yield scrapy.Request(url=url2,callback=self.search_followees_or_followers)

        else:
            print('登录失败')
        
    def search_followees_or_followers(self, response):
        #请求来自“关注了”页面 etc: https://www.zhihu.com/people/JAVAC/followees
        # 或者来自 https://www.zhihu.com/people/JAVAC/followers
        
        next_page_headers={
            "Referer" : response.url,
            "X-Requested-With" : "XMLHttpRequest",
        }
        params={
                'offset' : 20,
                'order_by' : "created",
                'hash_id' : response.css("div.zm-profile-header-op-btns.clearfix > button::attr(data-id)").extract_first(),
            }
        next_page_form_data={
                "method":"next",
                "params":json.dumps(params),
                "_xsrf":response.css("input[name=_xsrf]::attr(value)").extract_first(),
            }
        
        currentuser = re.match(r'.*people/(.+)/.+$',response.url).group(1)
        total = 0
        form_url = ''
        limit_people = 0
        total_selector = "div.zm-profile-side-following > a:nth-child({0}) > strong::text"
        mode = re.match(r'.*people/.+/(.+)$',response.url).group(1)
        if mode == 'followees':
            total = int(response.css(total_selector.format(1)).extract_first())
            form_url = 'https://www.zhihu.com/node/ProfileFolloweesListV2'
            limit_people = self.MAX_CRAWL_FOLLOWEES
        elif mode =='followers':
            total = int(response.css(total_selector.format(2)).extract_first())
            form_url = 'https://www.zhihu.com/node/ProfileFollowersListV2'
            limit_people = self.MAX_CRAWL_FOLLOWERS

        followees = int(response.css(total_selector.format(1)).extract_first())
        followers = int(response.css(total_selector.format(2)).extract_first())

        if followees>100 and followers>100:
            #先爬当前已有的前20项‘正在关注’或者‘关注人’信息
            cards = response.css('#zh-profile-follows-list > div > div')
            for card in cards:
                followers = int(re.match(r'(\d+).*',card.css('div.details.zg-gray > a:nth-child(1)::text').extract_first()).group(1))
                answers = int(re.match(r'(\d+).*',card.css('div.details.zg-gray > a:nth-child(3)::text').extract_first()).group(1))
                if followers>100 and answers>10:
                    href = card.css('div.zm-list-content-medium > h2 > a::attr(href)').extract_first()
                    short_href = re.match(r'.*com(.*)',href).group(1)
                    if self.redis_user.exists('user_href:'+short_href):
                        target_id = re.match(r'/people/(.*)',short_href).group(1)
                        if mode == 'followees':
                            yield Relation(user_id=currentuser,followee_id=target_id)
                        elif mode =='followers':
                            yield Relation(user_id=target_id,followee_id=currentuser)
            # 翻页
            for i in range(self.offset_start,limit_people,20):
                if i > total:
                    break
                params['offset'] = i
                next_page_form_data['params'] = json.dumps(params)
                ajax = scrapy.FormRequest(url=form_url,
                    formdata=next_page_form_data,headers=next_page_headers,callback=self.parse_pagination)
                ajax.meta['user_id'] = currentuser
                ajax.meta['mode'] = mode
                yield ajax

    def parse_pagination(self, response):
        # response来自ajax响应 ，不限关注或粉丝页
        # 筛选回答大于一定数量的人，提前筛选出关注者大于100粉丝
        pagedata = json.loads(response.body.decode('utf-8'))
        for fraction in pagedata['msg']:
            soup = BeautifulSoup(fraction,"lxml")
            followers = int(re.match(r'\D*(\d+).*',soup.select('div.details.zg-gray > a:nth-of-type(1)')[0].get_text()).group(1))
            answers = int(re.match(r'\D*(\d+).*',soup.select("div.details.zg-gray > a:nth-of-type(3)")[0].get_text()).group(1))
            if answers > self.USER_MINIMUM_ANSWERS and followers>100:
                href = soup.select("div.zm-list-content-medium > h2 > a")[0].get("href")
                short_href = re.match(r'.*com(.*)',href).group(1)
                if self.redis_user.exists('user_href:'+short_href):
                    target_id = re.match(r'/people/(.*)',short_href).group(1)
                    mode = response.meta['mode']
                    currentuser = response.meta['user_id']
                    if mode == 'followees':
                        yield Relation(user_id=currentuser,followee_id=target_id)
                    elif mode =='followers':
                        yield Relation(user_id=target_id,followee_id=currentuser)
