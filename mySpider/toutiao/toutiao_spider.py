#!/usr/bin/python
# -*- coding:utf-8 -*-

from pyspider.spider.base_handler import *
import tornado.gen
import tornado.httpclient
import time
import json
from lxml import etree
from pyspider.fetcher.tonado_cookies import cookie_to_dict

pool_size = 500
cookies_index = 0


# def get_cookies():
#     cookies = list()
#     client = tornado.httpclient.HTTPClient()
#     for i in xrange(pool_size):
#         url = 'http://toutiao.com/search/?keyword={q}'.format(q=random.choice('abcdefghijklmnopqrstuvwxyz'))
#         request = tornado.httpclient.HTTPRequest(url=url, method='HEAD')
#         response = client.fetch(request)
#         cookie = cookie_to_dict(response.headers['set-cookie'])
#         cookies.append(cookie)
#     return cookies

def get_cookies():
    """get cookies from """
    time.sleep(1)
    print '=======get cookies======'
    url = 'http://nj02-rp-2014-q1-01-jh2-201.nj02.baidu.com:8204/viva_ver_1_168/cookies/_search?q=domain:toutiao.com&size=%s' % str(pool_size)
    try:
        client = tornado.httpclient.HTTPClient()
        request = tornado.httpclient.HTTPRequest(url=url)
        response = client.fetch(request)
        result = response.body or ''
        cookies = json.loads(result)
        cookie_result = list()
        for cookie in cookies['hits']['hits']:
            if cookie['_type'] == 'cookies':
                cookie_result.append(cookie_to_dict(cookie['_source']['cookies'].encode('utf-8')))
        return cookie_result
    except Exception as e:
        print str(e)
        return None

class ToutiaoSpider(BaseHandler):
    """demo spider to crawler sougou weixin article"""

    crawl_config = {
        'other': {'cookie_pool': get_cookies()}
    }

    def _get_cookie(self):
        global cookies_index
        cookies = self.crawl_config.get('other', {}).get('cookie_pool', None)
        if cookies:
            cookies_index += 1
            cookies_index %= pool_size
            return cookies[cookies_index - 1]
        return

    @every(seconds=500)
    def _reset_coodies_pool(self):
        self.crawl_config.setdefault('other', {})
        self.log.info('get_cookies')
        self.crawl_config['other']['cookie_pool'] = get_cookies()

    def get_url(self):
        preffix1 = str(time.time())
        preffix2 = str(int(1000 * time.time()))
        url = 'http://toutiao.com/api/article/recent/?source=2&count=20&category=news_finance&max_behot_time=%s&utm_source=toutiao&offset=0&_=%s' % (preffix1, preffix2)
        return url

    @every(seconds=1)
    def on_start(self, response, task):
        url = self.get_url()
        cookies = self._get_cookie()
        if cookies:
            self.log.info(cookies)
            self.crawl(url, task, age=1, callback=self.index_page, cookies=cookies, taskid='toutiao_index_api')
        else:
            self.log.info('no cookies')
            self.crawl(url, task, age=1, callback=self.index_page, taskid='toutiao_index_api')

    def index_page(self, response, task):
        if response.content:
            result = json.loads(response.content)
            if result['message'] == 'success':
                for item in result['data']:
                    url = item['share_url']
                    url = url.split('?', 1)[0]
                    self.crawl(url, task, cookies=response.cookies, callback=self.article_page)

    def article_page(self, response, task):
        if response.doc:
            doc = response.doc
            item = dict()
            try:
                item['title'] = doc.xpath('//div[@class="title"]/h1/text()')[0].strip()
                item['public_time'] = doc.xpath('//div[@class="subtitle clearfix"]/span[2]/text()')[0].strip()
                item['post_user'] = etree.tostring(doc.xpath('//div[@class="subtitle clearfix"]/span[1]')[0],
                                                   method='text', encoding=unicode).strip()
                item['content'] = doc.xpath('//div[@class="article-content"]')
                if item['content']:
                    item['content'] = etree.tostring(item['content'][0], method='text', encoding=unicode).strip()
                return item
            except Exception as e:
                self.log.info(str(e))
                return None

__handler_cls__ = ToutiaoSpider
