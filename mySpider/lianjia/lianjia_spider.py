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


pool_size = 1

class LianjiaSpider(BaseHandler):
    """demo spider to crawler sougou weixin article"""


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
        for url in url_list:
            self.crawl(url, task, callback=self.index_page)

    def index_page(self, response, task):
        doc = response.doc
        self.log.info(doc)

        if doc is not None:
	    self.log.info("1")
            for node in doc.xpath('//div[@class="list-wrap"]'):
                house_list_tree= node.xpath('./ul[@class="house-lst"]')[0]
                self.log.info('2')
		house_list=house_list_tree.xpath('./li')
                self.log.info('3')
		for house in house_list:
		    house_info=house.xpath('./div')[1]
		    #house_detail=house.xpath('./div')[0]
                    self.log.info(house_info.xpath('./@class'))
		    house_href=house_info.xpath('./h2/a/@href')
 		    house_title=house_info.xpath('./h2/a/@title')
                    house_col1=house_info.xpath('./div[@class="col1"]')
		    house_col2=house_info.xpath('./div[@class="col2"]')	
		    house_col3=house_info.xpath('./div[@class="col3"]')
		    where=house_col1.xpath('./div[@class="where"]/a/span/text()')
		      	    
		    #url_info=house_detail.xpath('./@class')
		    self.log.info(house_href)
		    self.log.info(house_location)
		    #self.log.info(url_info)
'''   
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
'''
__handler_cls__ = LianjiaSpider
