#!/usr/bin/python
# -*- coding:utf-8 -*-

from pyspider.spider.base_handler import *
from lxml import etree
import random
import tornado.gen
import tornado.httpclient
import time
import re
from pyspider.fetcher.tonado_cookies import cookie_to_dict


_COOKIE_RE = re.compile(r'(ABTEST=\S+?|SNUID=\S+?|IPLOC=\S+?|SUID=\S+?|black_passportid=\S+?);')

pool_size = 1


def _get_suv():
    return '='.join(['SUV', str(int(time.time()*1000000) + random.randint(0, 1000))])

def process_cookie(cookie):
    """get cookie dict"""
    l = _COOKIE_RE.findall(cookie)
    l.append(_get_suv())
    return cookie_to_dict('; '.join(l))

def get_cookies():
    cookies = list()
    client = tornado.httpclient.HTTPClient()
    for i in xrange(pool_size):
        url = 'http://weixin.sogou.com/weixin?query={q}'.format(q=random.choice('abcdefghijklmnopqrstuvwxyz'))
        request = tornado.httpclient.HTTPRequest(url=url, method='HEAD')
        response = client.fetch(request)
        cookie = process_cookie(response.headers['set-cookie'])
        cookies.append(cookie)
        time.sleep(2)
    return cookies


class WeixinSpider(BaseHandler):
    """demo spider to crawler sougou weixin article"""

    crawl_config = {
        'other': {'cookie_pool': get_cookies()}
    }

    def _get_cookie(self):
        cookies = self.crawl_config.get('other', {}).get('cookie_pool', None)
        if cookies:
            return cookies[random.randint(0, len(cookies) - 1)]
        return

    @every(minutes=60)
    def _reset_coodies_pool(self):
        self.crawl_config.setdefault('other', {})
        self.crawl_config['other']['cookie_pool'] = get_cookies()

    @every(minutes=120)
    def on_start(self, response, task):
        seed_file = task['seed_path']
        url_list = []
        self.log.info("hello")
        with open(seed_file, 'rb') as fi:
            for line in fi:
                url = line.strip()
                if url:
                    url_list.append(url)
        age = task.get('seed_age', -1)
        for url in url_list:
            cookies = self._get_cookie()
            if cookies:
                self.crawl(url, task, age=age, callback=self.index_page, cookies=cookies)
            else:
                self.crawl(url, task, age=age, callback=self.index_page)

    def index_page(self, response, task):
        doc = response.doc
        if doc is not None:
            for node in doc.xpath('//div[@class="txt-box"]'):
                url = node.xpath('./h4/a/@href')[0]
                title = etree.tostring(node.xpath('./h4')[0], method='text', encoding=unicode)
                text = node.xpath('./p[1]/text()')[0]
                open_name = node.xpath('./div[@class="s-p"]/a[1]/@title')[0]
                suffix = open_name+text+title
                cookies = response.cookies
                self.crawl(url, task, callback=self.article_page, taskid=md5string(suffix), cookies=cookies)
            max_page = 0
            for url in doc.xpath('//div[@id="pagebar_container"]/a/@href'):
                max_page += 1
                if max_page > 3:
                    break
                cookies = self._get_cookie()
                if not cookies:
                    cookies = response.cookies
                self.crawl(url, task, age=7200, callback=self.index_page, cookies=cookies)

    def article_page(self, response, task):
        doc = response.doc
        if doc is not None:
            if doc.xpath('//label[@for="seccodeInput"]'):
                raise Exception("blocked, retry again!")
            result = dict()
            result['title'] = doc.xpath('//div[@id="page-content"]/div[@id="img-content"]/h2/text()')
            result['public_time'] = doc.xpath('//div/em[@id="post-date"]/text()')
            result['content'] = doc.xpath('//div[@id="js_content"]')
            result['post_user'] = doc.xpath('//a[@id="post-user"]/text()')
            if result['public_time']:
                result['public_time'] = result['public_time'][0].strip()
            if result['post_user']:
                result['post_user'] = result['post_user'][0].strip()
            if result['title']:
                result['title'] = result['title'][0].strip()
            if result['content']:
                result['content'] = etree.tostring(result['content'][0], method='text', encoding=unicode).strip()
            if not result['content']:
                raise Exception("maybe blocked, should be retry.")
            return result

__handler_cls__ = WeixinSpider
