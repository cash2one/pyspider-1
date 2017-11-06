# encoding: utf8

"""
本模块用于从携程网爬取酒店数据

Authors: xuguoqiang(xuguoqiang@baidu.com)
Date:    2015/8/09
"""

import hashlib
import json
import re
import time
import urllib2
import urlparse
import types
import os
import sys
import random
import datetime
import math
from HTMLParser import HTMLParser

from scrapy import log
import scrapy
from scrapy.contrib.spiders.crawl import CrawlSpider
from scrapy.mail import MailSender
import copy

class XiechengSpider(CrawlSpider):
    """ 该类用于从ctrip.com中抓取酒店信息 """

    name = 'xiecheng_spider'
    base_url = 'http://www.ctrip.com'
    allowed_domains = []
    start_urls = []
    max_page = 0

    def __init__(self, words=None, *a, **kw):
        CrawlSpider.__init__(self, *a, **kw)

        self.headers = dict()
        self.headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        #self.headers['Accept-Encoding'] = 'gzip, deflate, sdch'
        self.headers['Accept-Language'] = 'n-GB,en;q=0.8,en-US;q=0.6,zh-CN;q=0.4,zh;q=0.2'
        self.headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 \
                                      (KHTML, like Gecko) Chrome/33.0.1750.117 Safari/537.36'
        self.headers['Connection'] = 'keep-alive'
        self.headers['Host'] = 'xywy_spider.py'
        self.headers['X-Requested-With'] = 'XMLHttpRequest'

        self.mailer = MailSender(smtphost = 'smtp.126.com', mailfrom = 'njuxgq@126.com',
                                 smtpuser = 'njuxgq@126.com', smtppass = 'scrapyerror',
                                 smtpport = 465, smtpssl = True)

    def start_requests(self):
        """开始发送请求"""
        urls = []
        with open('ctrip_hotel_url', 'r') as fi:
            for line in fi:
                urls.append(line.strip())
        for url in urls:
            mMeta = {'url': url}
            yield scrapy.Request(url, headers=self.headers,
                             callback=self.parse_operation_info, meta=mMeta)

    def parse_operation_info(self, response):
        """每个hotel信息"""
        mMeta = response.meta
        ret = {}
        ret['desc'] = ''
        ret['room'] = ''
        ret['url'] = mMeta['url']
        ret['adress'] = response.xpath('//span[@id="ctl00_MainContentPlaceHolder_commonHead1_lbAddress"]/text()').extract()
        if len(ret['adress']) == 0:
            ret['adress'] = ''
        else:
            ret['adress'] = ret['adress'][0]
        ret['desc'] = response.xpath('//span[@id="ctl00_MainContentPlaceHolder_hotelDetailInfo_lbDesc"]/text()').extract()
        if len(ret['desc']) == 0:
            ret['desc'] = ''
        else:
            ret['desc'] = ret['desc'][0]
        ret['room'] = response.xpath('//div[@class="htl_room_txt text_3l "]/p/text()').extract()
        if len(ret['room']) == 0:
            ret['room'] = ''
        else:
            ret['room'] = ret['room'][0].strip()
        hotel_tag = []
        if len(response.xpath('//div[@id="htltags"]/span')) != 0:
            hotel_tag = response.xpath('//div[@id="htltags"]/span/text()').extract()
        ret['hotel_tag'] = hotel_tag
        jdss = {}
        for case in response.xpath('//div[@id="J_htl_facilities"]/dl'):
            name = case.xpath('dt[1]/text()').extract()[0].strip()
            jdss[name] = []
            for item in case.xpath('dd'):
               jdss[name].append(item.xpath('text()').extract()[0].strip())
        ret['jiudiansheshi'] = jdss
        zbss = {}
        for case in response.xpath('//div[@class="hotel_info_comment"]/div[@class="htl_info_table"]/table/tbody/tr'):
            name = case.xpath('th/text()').extract()[0].strip()
            zbss[name] = []
            for item in case.xpath('td/ul[@class="detail_extracontent"]/li/text()').extract():
                zbss[name].append(item.strip())
        ret['zhoubiansheshi'] = zbss
        #pingjia = []
        #print pingjia.append(response.xpath('//p[class="s_row"]/span/text').extract())
        #pingjia.append(response.xpath('//p[class="s_row"]').extract())
        #ret['pingjia'] = pingjia

        print json.dumps(ret, ensure_ascii=False).encode('utf-8', 'ignore')


class MLStripper(HTMLParser):
    """
    用于去除所有HTML Tag的类
    """
    def __init__(self):
        self.reset()
        self.fed = []

    def handle_data(self, d):
        self.fed.append(d)

    def get_data(self):
        """返回数据"""
        return ''.join(self.fed)


def strip_tags(html):
    """
    去除所有HTML Tag

    html: html内容
    """
    s = MLStripper()
    s.feed(html)
    return s.get_data()


if __name__ == '__main__':
    pass

#/* vim: set expandtab ts=4 sw=4 sts=4 tw=100: */
