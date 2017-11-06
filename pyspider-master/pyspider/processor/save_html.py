#!/usr/bin/python
# -*- coding:utf-8 -*-

import os
import time
import sys
reload(sys)
sys.setdefaultencoding( "utf-8" )

#constains
inner_fields = ['_on_get_info',  '_on_cronjob', 'on_start', '_on_get_info']

class SaveHtml(object):
    """class to save crawled html pages"""
    def __init__(self):
        pass

    def save_html(self, task, response):
        '''save html, override me'''
        raise NotImplementedError()


class DefaultSaveHtml(SaveHtml):
    """default implement of SaveHtml"""
    def save_html(self, task, response):
        """if you need, overrid me"""
        if task['taskid'] in inner_fields:
            return
        path = task['save_html_path']
        if not os.path.exists(path):
            os.mkdir(path)
        # body
        body = os.path.join(path, '%s.body' % task['taskid']).encode('utf-8')
        if 400 > response.status_code >= 200:
            fi = open(body, 'wb')
            fi.write(response.content)
            fi.close()
        else:
            if not os.path.exists(body):
                fi = open(body, 'wb')
                fi.close()

        # header
        header = os.path.join(path, '%s.header' % task['taskid']).encode('utf-8')
        fi = open(header, 'wb')
        fi.write('url: %s\n' % task['url'].encode('utf-8'))
        fi.write('ori_url: %s\n' % response.orig_url.encode('utf-8'))
        fi.write('cost_time: %s\n' % response.time)
        fi.write('crawler_time: %s\n' % time.time())
        fi.write('header: %s\n' % response.headers.__repr__())
        fi.write('status: %s\n' % str(response.status_code))
        fi.close()