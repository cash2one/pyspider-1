#!/usr/bin/python
# -*- coding:utf-8 -*-

import requests


class CookieUtil(object):

    def __init__(self, login_url=None):
        self.login_url = login_url

    def get_cookie(self):
        """override me"""

    def get_zhihu_cookie(self, retry_times=3):
        email = '578359441@qq.com'
        passwd = 'xgq012'

        self.login_url = 'http://www.zhihu.com/login'
        for i in range(retry_times):
            login_res = requests.post(self.login_url, data={'email': email, 'password': passwd})

            if login_res.status_code == 200:
                print "login success"
                return login_res.cookies
            else:
                print 'status code not right %s' % str(login_res.status_code)
        return

if __name__ == '__main__':
    cookie_util = CookieUtil()
    print cookie_util.get_zhihu_cookie()