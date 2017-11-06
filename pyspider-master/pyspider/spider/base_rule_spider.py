#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
import copy

from pyspider.spider.base_handler import *


class BaseSpider(BaseHandler):

    rules = ()

    def __init__(self, *a, **kw):
        self._compile_rules()

    def start_rule(self, task, response):
        task_url = task['url']
        for rule in self._rules:
            if rule.link_extractor and rule.link_extractor.link_allowed(task_url):
                return self._parse_response(response, rule.callback, rule.cb_kwargs, rule.follow)
        return self._parse_response(task, response, self.parse_start_url, cb_kwargs={}, follow=True)

    def parse_start_url(self, task, response):
        return {}

    def _requests_to_follow(self, task, response):
        if not response or response.doc is None:
            return
        follows = set()
        for n, rule in enumerate(self._rules):
            links = [l for l in rule.link_extractor.extract_links(task, response) if l not in follows]
            if links and rule.process_links:
                links = rule.process_links(links)
            follows = follows.union(links)
            self.crawl(links, task, callback=self._response_downloaded, rule=n)

    def _response_downloaded(self, task, response):
        rule = -1
        for each in response.save or []:
            if each == 'rule':
                rule = each
                break
        if rule != -1:
            return self._parse_response(response, rule.callback, rule.cb_kwargs, rule.follow)
        else:
            logging.info('no rule match')

    def _parse_response(self, task, response, callback, cb_kwargs, follow=True):
        """handle response"""
        self._set_crawler(task)
        if follow and self._follow_links:
            self._requests_to_follow(task, response)
        if callback:
            cb_res = callback(task, response, **cb_kwargs) or {}
            return cb_res

    def _compile_rules(self):
        def get_method(method):
            if callable(method):
                return method
            elif isinstance(method, basestring):
                return getattr(self, method, None)

        self._rules = [copy.copy(r) for r in self.rules]
        for rule in self._rules:
            rule.callback = get_method(rule.callback)
            rule.process_links = get_method(rule.process_links)
            rule.process_request = get_method(rule.process_request)

    def _set_crawler(self, task):
        self._follow_links = task['follow']
