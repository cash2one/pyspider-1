#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Created on 2015-11-19 09:19:43

from pyspider.spider.base_handler import *
from pyspider.spider.lxml_extractor import LinkExtractor
from pyspider.libs import utils
from .spider_params import *
import re


allow_params = ['cookies', 'headers', 'timeout']

default_pattern_flag = ['ajax_crawler', 'list_url_age']
default_pattern = ['ajax_url_pattern', 'list_url_black_pattern']

class BaseSpider(BaseHandler):

    def __init__(self):
        BaseHandler.__init__(self)

    def set_pattern(self, task, name):
        pat_strs = task.get(name, [])
        self.__setattr__(name, [re.compile(pat) for pat in pat_strs])

    def set_default_pattern(self, task):
        for index, flag in enumerate(default_pattern_flag):
            if task.get(flag, False):
                self.set_pattern(task, default_pattern[index])

    def _befor_run(self, task, response):
        self.set_default_pattern(task)

    def _match(self, pats, value):
        for pat in pats:
            if pat.match(value):
                return True
        return False

    def mycrawl(self, url, task, **kwargs):
        """mycrawl"""
        if not hasattr(url, "__iter__"):
            url = [url]
        for each in allow_params:
            if each in task and task[each]:
                kwargs[each] = task[each]
        ajax_url = []
        if task.get('ajax_crawler', False):
            if self.ajax_url_pattern:
                for each in url:
                    if self._match(self.ajax_url_pattern, each):
                        ajax_url.append(each)
            else:
                ajax_url = url
        no_ajax_url = list(set(url) ^ set(ajax_url))
        if no_ajax_url:
            return self.crawl(no_ajax_url, task, **kwargs)
        if ajax_url:
            kwargs['fetch_type'] = 'js'
            return self.crawl(ajax_url, task, **kwargs)

    def on_start(self, response, task):
        """entrance of spider"""
        seed_file = task['seed_path']
        follow = task['follow']
        url_list = []
        with open(seed_file, 'rb') as fi:
            for line in fi:
                url = line.strip()
                if url:
                    url_list.append(url)
        _config = rebuild_next_params(task)
        _config['age'] = task.get('seed_age', -1)
        if follow:
            _config['callback'] = self._follow
        else:
            _config['callback'] = self._no_follow
        self.mycrawl(url_list, task, **_config)

    def _follow(self, response, task):
        """all site crawler"""
        kwargs = {}
        if task['base_url_pattern']:
            kwargs['allow'] = task['base_url_pattern']
        if task['senior_url_pattern']:
            kwargs['senior_allow'] = task['senior_url_pattern']
        if task['domain']:
            kwargs['allow_domains'] = task['domain']
        link_extract = LinkExtractor(**kwargs)
        new_links = link_extract.extract_links(response=response, task=task)
        _config = rebuild_next_params(task)
        for link in new_links:
            self.process_next_crawler(link, task, **_config)
        return self._parser(response, task)

    def process_next_crawler(self, link, task, **kwargs):
        """process whether set list url age"""
        list_url_age = task['list_url_age']
        try:
            kwargs.pop('age')
        except:
            pass
        kwargs['callback'] = self._follow
        if list_url_age != -1:
            if self.list_url_black_pattern:
                for list_pat in self.list_url_black_pattern:
                    if list_pat.match(link):
                        return self.mycrawl(link, task, **kwargs)
            kwargs['age'] = list_url_age
            return self.mycrawl(link, task, **kwargs)
        else:
            return self.mycrawl(link, task, **kwargs)

    def _no_follow(self, response, task):
        """html crawler"""
        return self._parser(response, task)

    def _parser(self, response, task):
        """parser dom tree by xpath"""
        html = response.doc
        result = {}
        url = task['url'].strip()
        if task['xpath'] != {}:
            xpath2dict = {}
            for k, v in task['xpath'].iteritems():
                xpath2dict[re.compile(k)] = v
            for pat, xpaths in xpath2dict.iteritems():
                if pat.match(url):
                    for name, xpath in xpaths.iteritems():
                        result[name] = utils.etree2text(html.xpath(xpath))
                    break
        del task['senior_url_pattern']
        del task['xpath']
        del task['base_url_pattern']
        del task['list_url_black_pattern']
        return result
