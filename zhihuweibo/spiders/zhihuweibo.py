# -*- coding: utf-8 -*-
import scrapy
import json
import re
from bs4 import BeautifulSoup
from zhihuweibo.items import Relation

class ZhihuSpider(scrapy.Spider):
    name = "zhihu"
    cookies_file='cookies.txt'
    cookies=[]
    USER_MINIMUM_ANSWERS = 10
    MAX_CRAWL_FOLLOWEES = 500
    MAX_CRAWL_FOLLOWERS = 500
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
        yield scrapy.Request(url="https://www.zhihu.com/",
                               cookies=self.cookies)

    def parse(self, response): # After logined
        yield scrapy.Request(url="https://www.zhihu.com/people/JAVAC/followees",callback=self.search_followees_or_followers)
        yield scrapy.Request(url="https://www.zhihu.com/people/JAVAC/followers",callback=self.search_followees_or_followers)

    def search_followees_or_followers(self, response):
        #请求来自“关注了”页面 etc: https://www.zhihu.com/people/JAVAC/followees
        # 或者来自 https://www.zhihu.com/people/JAVAC/followers
        #TODO：先爬当前已有的前20项‘正在关注’或者‘关注人’信息
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

        for i in range(20,limit_people,20):
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
        # 筛选回答大于一定数量的人
        pagedata = json.loads(response.body.decode('utf-8'))
        for fraction in pagedata['msg']:
            soup = BeautifulSoup(fraction,"lxml")
            answers = int(re.match(r'^(\d+)',soup.select("div.details.zg-gray > a:nth-of-type(3)")[0].get_text()).group(0))
            if answers > self.USER_MINIMUM_ANSWERS:
                href = soup.select("div.zm-list-content-medium > h2 > a")[0].get("href")
                check_weibo_req = scrapy.Request(url=href, callback=self.filter_having_weibo)
                check_weibo_req.meta['user_id'] = response.meta['user_id']
                check_weibo_req.meta['mode'] = response.meta['mode']
                yield check_weibo_req

    def filter_having_weibo(self, response): #该用户关注的人/粉丝中有微博的        
        user_id = response.meta['user_id']
        target_id = re.match(r'.*people/(.+)$',response.url).group(1)
        mode = response.meta['mode']
        if response.css('a.zm-profile-header-user-weibo'):
            if mode == 'followees':
                print('--------',user_id,' → ',target_id,'---------')
                yield Relation(user_id=user_id,followee_id=target_id)
            elif mode =='followers':
                print('--------',target_id,' → ',user_id,'---------')
                yield Relation(user_id=target_id,followee_id=user_id)
                
        
        
            
            

    def search_followees(self, response): #请求来自个人主页 etc: https://www.zhihu.com/people/JAVAC/followees
        #TODO：先爬当前已有的前20项‘正在关注’信息
        followees = int(response.css("div.zm-profile-side-following > a:nth-child(1) > strong::text").extract_first())
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
        for i in range(20,self.MAX_CRAWL_FOLLOWEES,20):
            if i > followees:
                break            
            params['offset'] = i
            next_page_form_data['params'] = json.dumps(params)
            ajax = scrapy.FormRequest(url='https://www.zhihu.com/node/ProfileFolloweesListV2',
            formdata=next_page_form_data,headers=next_page_headers,callback=self.parse_pagination_followees)
            ajax.meta['user_id'] = currentuser
            yield ajax
    def parse_pagination_followees(self, response):
        # 来自ajax响应
        # 筛选回答大于一定数量的人
        pagedata = json.loads(response.body.decode('utf-8'))
        for fraction in pagedata['msg']:
            soup = BeautifulSoup(fraction,"lxml")
            answers = int(re.match(r'^(\d+)',soup.select("div.details.zg-gray > a:nth-of-type(3)")[0].get_text()).group(0))
            if answers > self.USER_MINIMUM_ANSWERS:
                href = soup.select("div.zm-list-content-medium > h2 > a")[0].get("href")
                check_weibo_req = scrapy.Request(url=href, callback=self.filter_followees_having_weibo)
                check_weibo_req.meta['user_id'] = response.meta['user_id']
                yield check_weibo_req

    def filter_followees_having_weibo(self, response): #该用户关注的人中有微博的
        user_id = response.meta['user_id']
        followee_id = re.match(r'.*people/(.+)$',response.url).group(1)
        if response.css('a.zm-profile-header-user-weibo'):
            print('--------',user_id,' → ',followee_id,'---------')
            yield Relation(user_id=user_id,followee_id=followee_id)




