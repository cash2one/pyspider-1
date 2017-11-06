#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-02-09 11:28:52

import re

# NOTE: When get/get_all/check_update from database with default fields,
#       all following fields should be included in output dict.
{
    'project': {
        'name': str,
        'group': str,
        'status': str,
        'script': str,
        'comments': str,
        'rate': int,
        'burst': int,
        'base_url_pattern': str,
        'seed_path': str,
        'save_html': int,
        'save_html_path': str,
        'follow': int,
        'domain': str,
        'senior_url_pattern': str,
        'xpath': str,
        'depth_limit,list_url_black_pattern': str,
        'list_url_age': int,
        'ajax_crawler': int,
        'ajax_url_pattern': str,
        'cookies': str,
        'headers': str,
        'seed_age': int,
        'updatetime': int,
        'deletetime': int,
        # new
    }
}


class ProjectDB(object):
    status_str = [
        'TODO',
        'DELETE',
        'STOP',
        'DEBUG',
        'RUNNING',
    ]

    def insert(self, name, obj={}):
        raise NotImplementedError

    def update(self, name, obj={}, **kwargs):
        raise NotImplementedError

    def get_all(self, fields=None):
        raise NotImplementedError

    def get(self, name, fields):
        raise NotImplementedError

    def drop(self, name):
        raise NotImplementedError

    def check_update(self, timestamp, fields=None):
        raise NotImplementedError

    def split_group(self, group, lower=True):
        return re.split("\W+", (group or '').lower())

    def verify_project_name(self, name):
        if len(name) > 64:
            return False
        if re.search(r"[^\w]", name):
            return False
        if name == 'all':
            return False
        return True
