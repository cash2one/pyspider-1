#!/usr/bin/python
# -*- coding:utf-8 -*-
"""
生成新的链接，并对链接进行过滤；
"""

from pyspider.libs.url import (quote_chinese, _build_url, _encode_params, _encode_multipart_formdata,
                               curl_to_arguments, url_is_from_any_domain, add_http_if_no_scheme)
import re

class LinkExtractor(object):
    def __init__(self, task, response):
        self._domain = task['domain']
        self._base_url_pattern = [re.compile(pat_strs) for pat_strs in task['base_url_pattern']]
        self._senior_url_pattern = dict()
        for k, v in task['senior_url_pattern'].iteritems():
            self._senior_url_pattern[re.compile(k)] = re.compile(v)
        self._url_pattern_mod = task['url_pattern_mod']
        self._doc = response.doc
        self._task_url = task['url']

    def extract_links(self):
        if self._doc is None:
            return []
        candidates = self._doc.xpath('//a')
        ret = []
        for each in candidates:
            if 'href' not in each.attrib or each.attrib['href'].lower().startswith('javascript')\
                    or each.attrib['href'].lower().startswith('mailto:'):
                    continue
            url = add_http_if_no_scheme(each.attrib['href'].strip())
            if self.filter_url(url):
                ret.append(url)
        return ret

    def filter_url(self, url):
        """filter url"""
        if self._domain and not self.domain_filter(url):
            return False
        if self._url_pattern_mod == 'base':
            if not self.base_url_pattern_filter(url):
                return False
        elif self._url_pattern_mod == 'senior':
            if not self.senior_url_pattern_filter(url):
                return False
        return True

    def domain_filter(self, url):
        """judge whether url match the given domains"""
        return url_is_from_any_domain(url, self._domain)

    def base_url_pattern_filter(self, url):
        """judge whether url match base url patterns"""
        for base_pat in self._base_url_pattern:
            if base_pat.match(url):
                return True
        return False

    def senior_url_pattern_filter(self, url):
        """judge whether url match senior url patterns"""
        for src_pat, dir_pat in self._senior_url_pattern.iteritems():
            if src_pat.match(self._task_url) and dir_pat.match(url):
                return True
        return False

    def reset(self):
        """reset domians, both base and senior url patterns"""
        self._url_pattern_mod = None
        self._base_url_pattern = []
        self._senior_url_pattern = {}
        self._domain = []