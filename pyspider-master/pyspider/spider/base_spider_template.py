#!/usr/bin/python
# -*- coding:utf-8 -*-


default_spider_str = '''
#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Created on 2015-11-19 09:19:43

from pyspider.spider.base_spider import *

class Spider(BaseSpider):
    %s
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

__handler_cls__ = Spider
'''
