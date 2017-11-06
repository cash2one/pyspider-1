#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-10-19 15:37:46

import time
import json
import logging
import os
from six.moves import queue as Queue
import sys
logger = logging.getLogger("result")


class ResultWorker(object):

    """
    do with result
    override this if needed.
    """

    def __init__(self, resultdb, inqueue):
        self.resultdb = resultdb
        self.inqueue = inqueue
        self._quit = False

    def on_result(self, task, result):
        '''Called every result, write result to db'''
        if not result:
            return
        if 'taskid' in task and 'project' in task and 'url' in task:
            logger.info('result %s:%s %s -> %.30r' % (
                task['project'], task['taskid'], task['url'], result))
            return self.resultdb.save(
                project=task['project'],
                taskid=task['taskid'],
                url=task['url'],
                result=result
            )
        else:
            logger.warning('result UNKNOW -> %.30r' % result)
            return

    def quit(self):
        self._quit = True

    def run(self):
        '''Run loop'''
        logger.info("result_worker starting...")

        while not self._quit:
            try:
                task, result = self.inqueue.get(timeout=1)
                self.on_result(task, result)
            except Queue.Empty as e:
                continue
            except KeyboardInterrupt:
                break
            except AssertionError as e:
                logger.error(e)
                continue
            except Exception as e:
                logger.exception(e)
                continue

        logger.info("result_worker exiting...")


class OneResultWorker(ResultWorker):
    '''Result Worker for one mode, write results to stdout'''
    def on_result(self, task, result):
        '''Called every result'''
        if not result:
            return
        if 'taskid' in task and 'project' in task and 'url' in task:
            logger.info('result %s:%s %s -> %.30r' % (
                task['project'], task['taskid'], task['url'], result))
            sys.stdout.write(json.dumps({
                'taskid': task['taskid'],
                'project': task['project'],
                'url': task['url'],
                'result': result,
                'updatetime': time.time()
            }, ensure_ascii=False).encode('utf-8') + '\n')
        else:
            logger.warning('result UNKNOW -> %.30r' % result)
            return

class FileResultWorker(object):
    '''Result Worker for one mode, write results to file'''

    """
    do with result write to file
    override this if needed.
    """
    def __init__(self, resultdb, inqueue):
        self.resultdb = resultdb
        self.inqueue = inqueue
        self._quit = False
        self.files = dict()
        self.today = time.strftime("%Y-%m-%d", time.localtime())

    def quit(self):
        self._quit = True

    def run(self):
        '''Run loop'''
        logger.info("result_worker starting...")

        while not self._quit:
            try:
                task, result = self.inqueue.get(timeout=1)
                self.check_date()
                self.on_result(task, result)
            except Queue.Empty as e:
                continue
            except KeyboardInterrupt:
                break
            except AssertionError as e:
                logger.error(e)
                continue
            except Exception as e:
                logger.exception(e)
                continue

        for project in self.files.keys():
            fi = self.files.pop(project)
            if not fi.closed:
                fi.close()

        logger.warning("result_worker exiting...")

    def check_date(self):
        """check days"""
        today = time.strftime("%Y-%m-%d", time.localtime())
        if today != self.today:
            self.today = today
            for project in self.files.keys():
                fi = self.files.pop(project)
                if not fi.closed:
                    fi.close()

    def set_file(self, project, file_path):
        """set files for project"""
        if not file_path:
            file_path = './data/result/%s_' % project
        suffix = int(time.time())
        while os.path.exists(file_path + str(suffix)):
            suffix += 1
        fi = open(file_path + str(suffix), 'wb')
        self.files[project] = fi

    def put_back(self, task, result):
        """put back task and result"""
        try:
            self.inqueue.put((task, result))
        except Queue.Full:
            logger.error('queue overflow')
            return
        except Exception as e:
            logger.exception(e)
            return

    def on_result(self, task, result):
        '''Called every result'''
        if not result:
            return
        if 'taskid' in task and 'project' in task and 'url' in task:
            if task["auto_file"]:
                if task['project'] not in self.files:
                    self.set_file(task['project'], task['file_path'])
                logger.info('result %s:%s %s -> %.30r' % (
                    task['project'], task['taskid'], task['url'], result))
                self.files[task['project']].write(json.dumps({
                    'taskid': task['taskid'],
                    'project': task['project'],
                    'url': task['url'],
                    'result': result,
                    'updatetime': time.time()
                }, ensure_ascii=False).encode('utf-8') + '\n')
                self.files[task['project']].flush() 
            else:
                self.put_back(task, result)
        else:
            logger.warning('result UNKNOW -> %.30r' % result)
            return


class MyFileResultWorker(FileResultWorker):
    """special result_worker for single project"""

    def __init__(self, resultdb, inqueue):
        FileResultWorker.__init__(self, resultdb, inqueue)
        self.time = time.time()
        self.interval = 60*60

    def check_date(self):
        """check time"""
        current_time = time.time()
        if current_time - self.time >= self.interval:
            self.time = current_time
            for project in self.files.keys():
                fi = self.files.pop(project)
                fi.close()

    def on_result(self, task, result):
        '''Called every result'''
        if not result:
            return
        if 'taskid' in task and 'project' in task and 'url' in task:
            if task['project'] == 'hongzhoukan':
                if task['project'] not in self.files:
                    self.set_file(task['project'], task['file_path'])
                logger.info('result %s:%s %s -> %.30r' % (
                    task['project'], task['taskid'], task['url'], result))
                result['source'] = 'your_project_source'
                self.files[task['project']].write(json.dumps({
                    'result': result
                }, ensure_ascii=False).encode('utf-8') + '\n')
                self.files[task['project']].flush() 
            else:
                self.put_back(task, result)
        else:
            logger.warning('result UNKNOW -> %.30r' % result)
            return

