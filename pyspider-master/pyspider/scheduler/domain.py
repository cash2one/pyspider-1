#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Author: xuguoqiang(xuguoqiang@baidu.com)
# Created on 2015-12-28 20:14:23

import logging
import threading
import time
from .token_bucket import Bucket

logger = logging.getLogger('scheduler')


class Domain(object):

    def __init__(self, rate=20, burst=50):
        self.mutex = threading.RLock()
        self.bucket = Bucket(rate=rate, burst=burst)
        self.update_time = time.time()

    @property
    def rate(self):
        return self.bucket.rate

    @rate.setter
    def rate(self, value):
        self.bucket.rate = value

    @property
    def burst(self):
        return self.bucket.burst

    @burst.setter
    def burst(self, value):
        self.bucket.bucket = value

    def get_bucket(self):
        """return True when bucket available"""
        self.update_time = time.time()
        if self.bucket.get() < 1:
            return False
        self.mutex.acquire()
        self.bucket.desc()
        self.mutex.release()
        return True

    def size(self):
        return self.bucket.get()