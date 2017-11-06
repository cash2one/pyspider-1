#!/usr/bin/python
# -*- coding:utf-8 -*-

import logging

# set root logger
r = logging.getLogger()
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
r.addHandler(ch)

# set father logger
p = logging.getLogger('foo')
p.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(message)s')
ch.setFormatter(formatter)
p.addHandler(ch)

# set child logger
c = logging.getLogger('foo.bar')
ch = logging.FileHandler('test.log')
c.setLevel(logging.DEBUG)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(message)s')
ch.setFormatter(formatter)
c.addHandler(ch)
c.debug('foo')
c.error("foo error")