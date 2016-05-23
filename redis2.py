# -*- coding: utf-8 -*-


import redis

if __name__ =='__main__':
    user_file = 'zhihuuser.txt'
    r = redis.StrictRedis(host='localhost',port=6379,db=1)
    with open(user_file,'a') as f:
        for key in r.keys('user_href*'):
            f.write(key.decode('utf-8')+'\n')