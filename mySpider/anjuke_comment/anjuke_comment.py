#!/usr/bin/pytho
# -*- coding:utf-8 -*-
import xml.etree.ElementTree as ET
from pyspider.spider.base_handler import *
from lxml import etree
import random
import tornado.gen
import tornado.httpclient
import time
import re
import json
from pyspider.fetcher.tonado_cookies import cookie_to_dict

pool_size = 1

class AnjukeSpider(BaseHandler):
    """spider to crawl Anjuke"""

    ####@every(minutes=120)
    def on_start(self, response, task):
        seed_file = task['seed_path']
        url_list = []
        with open(seed_file, 'rb') as fi:
            for line in fi:
                url = line.strip()
                if url:
                    url_list.append(url)
        for url in url_list:
            self.crawl(url, task, callback=self.index_page)

    def index_page(self, response, task):
        doc = response.doc
        url = response.url
        self.log.info(doc)
        self.log.info("+++++++++++++++++++++++++entry++++++++++++++++++++++++++++++++++")
        if doc is  None:return ""
        node=doc.xpath('//div[@class="ugc-mod"]')
        if node:
            house_list= node[0].xpath('./div[@class="total-comment"]')
            if house_list:
                result = list()
                house_list = house_list[0]
                comment_list = house_list.xpath('./div[@class="total-wrap"]/ul[@class="total-revlist"]')
                if comment_list is None:return ""
                comment_list_details = comment_list[0].xpath('./li')
                for sub_comment in comment_list_details:
                    id = sub_comment.xpath('./span/@id')[0]
                    self.log.info(id)
                    text = sub_comment.xpath('./div[@class="clearfix"]/div[@class="info-mod"]')
                    if text:
                        text = text[0]
                        comment_text = text.xpath('./h4[@class="rev-subtit part-text"]/text()')
                        if comment_text:
                            comment_text = comment_text[0]
                        else:
                            comment_text = ""
                    save = dict()
                    save['id'] = id
                    self.log.info(comment_text)
                    save['text'] = comment_text.strip()
                    result.append(save)
            try:
                next_page_url=node[0].xpath('./div[@class="rev-pagination"]')		
                if next_page_url:
                    next_page_url=next_page_url[0]
                    next_page_url = next_page_url.xpath('./div[@class="pagination"]/a[@class="next-page next-link"]')
                    if next_page_url:
                        next_page_url = next_page_url[0].xpath('./@href')[0]
                        self.log.info(next_page_url)
                        self.crawl(next_page_url,task,callback=self.index_page)
            except Exception,e:
                self.log.info("---------------------------------------------------------end this city-------------------------")
            return self.article_page(result)
    
    #def article_page(self, response, task):
    def article_page(self, result):
        self.log.info(result)
        return result

__handler_cls__ = AnjukeSpider
