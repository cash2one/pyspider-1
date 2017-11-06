#!/usr/bin/env python
# -*- coding: utf-8 -*-
################################################################################
#
# Copyright (c) 2015 Baidu.com, Inc. All Rights Reserved
#
################################################################################

"""


Authors: zhengjingyao(zhengjingyao@baidu.com)
Creation Date : 2016-01-08 17:57:50
Last Modified : 2016-01-08 19:50:47
"""

import sys
import os
cur_dir = os.path.split(os.path.realpath(__file__))[0]

from re import match
from pyspider.spider.base_handler import *


class ZhihuFavoritesSpider(BaseHandler):
    crawl_config = {}

    #cookie = open('/home/users/zhengjingyao/pyspider-master/data/spider/zhihu/cookie', 'r').read().strip()

    @every(minutes=24 * 60)
    def on_start(self, response, task):

        cookie = task['cookies']
        self.log.info(cookie)
        self.crawl('http://www.sina.com.cn/', task, callback=self.index_page, cookies=cookie)

    #@config(age=24 * 60 * 60)
    def index_page(self, response, task):
        
        t_xpath = '//*[@id="zh-list-answer-wrap"]/div[1]/h2/a'
        page = response.doc
        with open('zhihu.log', 'a') as ofile:
            ofile.write("fuck")

        title = etree.xpath(t_xpath)
        for t in title:
            with open('zhihu.log', 'a') as ofile:
                ofile.write(t.text + '\n')
                ofile.write(response.text)
                ofile.write(len(response.text))

        #for each in response.doc('a[href^="http"]').items():
        #    if match('http://www.zhihu.com/question/\d+$', each.attr.href):
        #        self.crawl(each.attr.href, callback=self.index_page)
        #return [{
        #        "url": response.url,
        #        "title": response.doc('title').text(),
        #        "author": each('.answer-head > .zm-item-answer-author-info > .zm-item-answer-author-wrap > a').eq(1).text(),
        #        "answer": each('.zm-item-rich-text > div').text(),
        #        "vote": each('.count').text()
        #} for each in response.doc('.zu-main-content-inner > #zh-question-answer-wrap > .zm-item-answer').items()]

    #def on_result(self, result):
    #    with open('zhihu.log', 'a') as fp:
    #        for item in result:
    #            fp.write(str(item))
    #            fp.write('\n')


__handler_cls__ = ZhihuFavoritesSpider

#/* vim: set expandtab ts=4 sw=4 sts=4 tw=100: */
