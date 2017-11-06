#!/usr/bin/env python
# -*- coding:utf-8 -*-

import imp
import six
import linecache

class_str = """
#!/usr/bin/python
# -*- coding:utf-8 -*-

class Project(object):
    def __init__(self):
        self.value = 1

"""

mod = imp.new_module('project')

mod.__file__ = '<%s>' % 'project'
code = compile(class_str, "project", "exec")
six.exec_(code, mod.__dict__)
linecache.clearcache()
print mod.__dict__
