#!/usr/bin/python
# -*- coding:utf-8 -*-

"""
加载project的配置
Authors: xuguoqiang(xuguoqiang@baidu.com)
Date: 2015/12/07 10:15
"""

import ConfigParser
import os
import logging
import json
from pyspider.fetcher.tonado_cookies import cookie_to_dict
import re


# constains

base_spider_options = ['follow', 'base_url_pattern', 'seed_path', 'domain', 'senior_url_pattern', 'xpath',
                       'depth_limit', 'seed_age', 'list_url_age', 'list_url_black_pattern', 'save_html',
                       'cookies', 'headers', 'ajax_crawler', 'ajax_url_pattern', 'timeout', 'save_html_path',
                       'deletetime', 'log_level', 'log_path', 'log_interval', 'file_path', 'auto_file']

def get(cf, section, option, default=None):
    """get default value if option is not set in the given section"""
    if not cf.has_section(section):
        raise ConfigParser.NoSectionError
    if cf.has_option(section, option):
        return cf.get(section, option)
    else:
        return default


def getint(cf, section, option, default=None):
    """get default value if option is not set in the given section"""
    if not cf.has_section(section):
        raise ConfigParser.NoSectionError
    if cf.has_option(section, option):
        return cf.getint(section, option)
    else:
        return default


def getfloat(cf, section, option, default=None):
    """get default value if option is not set in the given section"""
    if not cf.has_section(section):
        raise ConfigParser.NoSectionError
    if cf.has_option(section, option):
        return cf.getfloat(section, option)
    else:
        return default


def read_project_config(cf, project):
    """read config of project"""
    ret = {}
    str_params = ['base_url_pattern', 'senior_url_pattern', 'spider',
                  'seed_path', 'save_html_path', 'domain', 'xpath',
                  'list_url_black_pattern', 'ajax_url_pattern',
                  'headers', 'cookies', 'log_path', 'log_level',
                  'lib', 'file_path']
    int_params = ['follow', 'save_html', 'depth_limit', 'seed_age', 'list_url_age', 'ajax_crawler', 'timeout',
                  'deletetime', 'log_interval', 'auto_file']
    float_params = ['rate', 'burst']
    for param in str_params:
        ret[param] = get(cf, project, param, '')
    for param in int_params:
        ret[param] = getint(cf, project, param, -1)
    for param in float_params:
        ret[param] = getfloat(cf, project, param, 0.0)
    # check default parameters value
    if not ret['spider'] and not os.path.exists(ret['seed_path']):
        raise Exception("seed file of project %s not exist: %s" % (project, ret['seed_path']))
    if ret['save_html'] == 1 and not os.path.exists(ret['save_html_path']):
        os.mkdir(ret['save_html_path'])
    if ret['rate'] == 0.0:
        ret['rate'] = 3
    if ret['burst'] == 0.0:
        ret['burst'] = 30
    del ret['spider']
    return ret


def rebuild_project(project):
    """rebuild config"""
    base_url_pattern = project['base_url_pattern']
    senior_url_pattern = project['senior_url_pattern']
    list_url_black_pattern = project['list_url_black_pattern']
    ajax_url_pattern = project['ajax_url_pattern']
    headers = project['headers']
    cookie = project['cookies']
    xpath = project['xpath']
    timeout = project['timeout']
    log_level = project['log_level']
    log_interval = project['log_interval']
    auto_file = project['auto_file']

    project['save_html'] = False if project['save_html'] == -1 else True
    project['follow'] = False if project['follow'] == -1 else True
    project['ajax_crawler'] = False if project['ajax_crawler'] == -1 else True
    project['auto_file'] = False if project['auto_file'] == -1 else True
    if project['domain']:
        project['domain'] = list(set(project['domain'].split(',')))
    if ajax_url_pattern:
        project['ajax_url_pattern'] = [x.stip() for x in ajax_url_pattern.split(',')]
    # if base url pattern
    if base_url_pattern:
        project['base_url_pattern'] = [x.strip() for x in base_url_pattern.split(',')]
    # if senior url pattern
    project['senior_url_pattern'] = {}
    if senior_url_pattern:
        senior_patterns = list(set(senior_url_pattern.split(',')))
        senior_num = len(senior_patterns)
        if senior_num % 2 != 0:
            logging.error(('project: %s fail to load url pattern %s :'
                          % (project['name'], senior_url_pattern)))
        else:
            senior_num /= 2
            for index in range(senior_num):
                try:
                    src_pattern = senior_patterns[2*index]
                    dir_pattern = senior_patterns[2*index+1]
                    project['senior_url_pattern'][src_pattern] = dir_pattern
                except Exception as e:
                    logging.error(('project: %s fail to load senior url pattern: %s to %s:'
                                  % (project['name'], senior_patterns[2*index], senior_patterns[2*index+1])) + str(e))
    # deal headers
    if headers:
        project['headers'] = json.loads(headers)
    else:
        project['headers'] = {}

    # deal cookie
    if cookie:
        if cookie.startswith('{') and cookie.endswith('}'):
            project['cookies'] = json.loads(cookie)
        else:
            project['cookies'] = cookie_to_dict(cookie.encode('utf-8'))
    else:
        project['cookies'] = {}

    if timeout == -1:
        project['timeout'] = 120

    project['xpath'] = {}
    if xpath != '':
        xpath_dict = json.loads(xpath)
        for pattern, xpaths in xpath_dict.iteritems():
            project['xpath'][pattern] = xpaths
    if list_url_black_pattern == '':
        project['list_url_black_pattern'] = list()
    else:
        project['list_url_black_pattern'] = list(set(list_url_black_pattern.split(',')))

    if log_level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR']:
        project['log_level'] = 'DEBUG'
    if log_interval <= 0:
        project['log_interval'] = -1
    return project


def check_project(project):
    """check project info"""
    try:
        base_url_pattern = project['base_url_pattern']
        senior_url_pattern = project['senior_url_pattern']
        list_url_black_pattern = project['list_url_black_pattern']
        ajax_url_pattern = project['ajax_url_pattern']
        headers = project['headers']
        cookie = project['cookies']
        xpath = project['xpath']
        lib = project['lib']

        if project['domain']:
            list(set(project['domain'].split(',')))
        if ajax_url_pattern:
            [x.stip() for x in ajax_url_pattern.split(',')]
        # if base url pattern
        if base_url_pattern:
            [re.compile(x.strip()) for x in base_url_pattern.split(',')]
        # if senior url pattern
        if senior_url_pattern:
            senior_patterns = list(set(senior_url_pattern.split(',')))
            senior_num = len(senior_patterns)
            if senior_num % 2 != 0:
                logging.error(('project: %s fail to load url pattern %s :'
                              % (project['name'], senior_url_pattern)))
            else:
                senior_num /= 2
                for index in range(senior_num):
                    re.compile(senior_patterns[2*index])
                    re.compile(senior_patterns[2*index+1])
        # deal headers
        if headers:
            json.loads(headers)

        # deal cookie
        if cookie:
            if cookie.startswith('{') and cookie.endswith('}'):
                json.loads(cookie)
            else:
                cookie_to_dict(cookie.encode('utf-8'))

        if xpath != '':
            json.loads(xpath)
        if list_url_black_pattern != '':
            [re.compile(x) for x in list(set(list_url_black_pattern.split(',')))]

        # deal libs
        if lib:
            libs = lib.split(',')
            for lib_dir in libs:
                if not os.path.exists(lib_dir):
                    raise Exception("%s not exist." % lib_dir)
        return True
    except Exception as e:
        logging.warning("checking project error:%s", str(e))
        return False
