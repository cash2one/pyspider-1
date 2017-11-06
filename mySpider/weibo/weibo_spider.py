#!/usr/bin/python
# -*- coding:utf-8 -*-

from pyspider.spider.base_spider import *
import re
from lxml import etree


class WeiboSpider(BaseSpider):
    """demo spider to crawler sina weibo"""

    def _parser(self, response, task):
        """parser"""
        self.log.info(task['cookies']) 
        if not response.doc:
            self.log.info('None')
            return
        url = task['url']
        doc = response.doc
        # weibo
        result = {}
        if re.match(ur'http://weibo.cn/yaochen\?page=\d+', url):
            result['weibo'] = []
            for node in doc.xpath('//span[@class="ctt"]'):
                ctt = etree.tostring(node, method='text', encoding=unicode)
                if ctt:
                    result['weibo'].append(ctt)

        # follow
        elif re.match(ur'http://weibo.cn/1266321801/follow\?page=\d+', url):
            result['follow'] = []
            for node in doc.xpath('//table/tr/td[2]'):
                follow = etree.tostring(node, method='text', encoding=unicode)
                if follow:
                    result['follow'].append(follow)

        # fans
        elif re.match(ur'http://weibo.cn/1266321801/fans\?page=\d+', url):
            result['fans'] = []
            for node in doc.xpath('//table/tr/td[2]'):
                fans = etree.tostring(node, method='text', encoding=unicode)
                if fans:
                    result['fans'].append(fans)
        else:
            return

        return result

__handler_cls__ = WeiboSpider



