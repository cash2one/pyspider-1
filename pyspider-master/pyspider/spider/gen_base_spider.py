#!/usr/bin/python
# -*- coding:utf-8 -*-

import os
import logging

from pyspider.spider.base_spider_template import *
from pyspider.libs import read_project_config


def local_projects(cf):
    '''
    build local projects
    :param project_list:
    :return:
    '''
    every_config = '@every(minutes=%d, seconds=%d)'
    project_list = cf.get('run', 'projects').split(',')
    projects = {}
    for project in project_list:
        if cf.has_option(project, 'spider'):
            spider_file = cf.get(project, 'spider')
            if os.path.exists(spider_file):
                fi = open(spider_file, 'rb')
                projects[project] = {'script': fi.read(), 'name': project}
                fi.close()
                continue
            else:
                logging.ERROR('spider not exist: %s' % spider_file)
                continue
        try:
            every_para = read_project_config.getint(cf, project, 'every', -1)
        except Exception as e:
            logging.info(str(e))
            continue
        if every_para == -1:
            projects[project] = {'script': default_spider_str % '', 'name': project}
        elif every_para > 0:
            minutes = every_para / 60
            seconds = every_para % 60
            projects[project] = {'script': default_spider_str % (every_config % (minutes, seconds)), 'name': project}
        else:
            logging.error('get invalid parameter for project %s: every = %d' % (project, every_para))
            continue
    logging.info(projects)

    return projects


def one_local_project(cf, project):
    '''
    build local projects
    :param project_list:
    :return:
    '''

    if not cf.has_section(project):
        return
    every_config = '@every(minutes=%d, seconds=%d)'
    if cf.has_option(project, 'spider'):
        spider_file = cf.get(project, 'spider')
        if os.path.exists(spider_file):
            fi = open(spider_file, 'rb')
            spider_str = fi.read()
            fi.close()
            return project, {'script': spider_str, 'name': project}
        else:
            logging.error('spider not exist: %s' % spider_file)
            return
    try:
        every_para = read_project_config.getint(cf, project, 'every', -1)
    except Exception as e:
        logging.info(str(e))
        return
    if every_para != -1:
        minutes = every_para / 60
        seconds = every_para % 60
        return project, {'script': default_spider_str % (every_config % (minutes, seconds)), 'name': project}
    elif every_para != -1 and every_para <= 0:
        logging.error('get invalid parameter for project %s: every = %d' % (project, every_para))
        return
    else:
        return project, {'script': default_spider_str % '', 'name': project}