#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<roy@binux.me>
#         http://binux.me
# Created on 2014-11-24 22:27:45


import sys
from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

import pyspider

install_requires = [
    'chardet>=2.2',
    'cssselect>=0.9',
    'lxml',
    'pycurl',
    'pyquery',
    'requests>=2.2',
    'tornado>=3.2',
    'u-msgpack-python>=1.6',
    'click>=3.3',
    'six',
]

extras_require_all = [
    'pymongo>=2.7.2,<3.0',
    'redis',
    'psycopg2',
]
if sys.version_info < (3, 0):
    extras_require_all.extend([
        'pika>=0.9.14',
    ])


setup(
    name='pyspider',
    version=pyspider.__version__,

    description='pyspider',
    long_description=long_description,


    classifiers=[
        'Development Status :: 4 - Beta',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',

        'License :: OSI Approved :: Apache Software License',

        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Environment :: Web Environment',

        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],

    packages=find_packages(exclude=['data', 'tests*']),

    install_requires=install_requires,

    extras_require={
        'all': extras_require_all,
        'test': [
            'unittest2>=0.5.1',
            'coverage',
            'httpbin',
            'pyproxy>=0.1.6',
        ]
    },

    package_data={
        'pyspider': [
            'logging.conf',
            'fetcher/phantomjs_fetcher.js',
        ],
    },

    entry_points={
        'console_scripts': [
            'pyspider=pyspider.run:main'
        ]
    },

    test_suite='tests.all_suite',
)
