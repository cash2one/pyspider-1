#!/usr/bin/python
# -*- coding:utf-8 -*-

import hashlib

def identity(value):
    return value

class Rule(object):

    def __init__(self, link_extractor, callback=None, cb_kwargs=None, follow=None, process_links=None, process_request=identity):
        self.link_extractor = link_extractor
        self.callback = callback
        self.cb_kwargs = cb_kwargs or {}
        self.process_links = process_links
        self.process_request = process_request
        if follow is None:
            self.follow = False if callback else True
        else:
            self.follow = follow

    def md5(self):
        """compute rule md5, only for allow/deny/deny_domains/allow_domains info"""
        key = ""
        if self.link_extractor:
            key += self.link_extractor.get_allow()
            key += self.link_extractor.get_deny()
            key += self.link_extractor.get_deny_domains()
            key += self.link_extractor.get_allow_domains()
        return hashlib.md5(key).hexdigest()



