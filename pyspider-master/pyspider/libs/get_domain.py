#!/usr/bin/python
# -*- coding:utf-8 -*-

import commands
import os
import urlparse

lib_dir = os.path.dirname(os.path.realpath(__file__))

def get_domain2(url):
    """get domain of url"""
    temp_url = url.split("#")[0]
    temp_url = temp_url.split("?")[0]

    cmd = "echo %s | %s domain" % (temp_url, os.path.join(lib_dir, "get_maindomain"))
    ret_code, output = commands.getstatusoutput(cmd)
    if ret_code != 0:
        return False, None
    return True, output


def get_domain(url):
    if url.find('://') == -1:
        url = 'http://' + url
    try:
        domain = urlparse.urlparse(url).hostname.split(".")
        domain = ".".join(len(domain[-2]) < 4 and domain[-3:] or domain[-2:])
    except Exception as e:
        return False, str(e)
    return True, domain


if __name__ == '__main__':
    url = 'http://www.e26.cn/CorpInfo/1/8990/qdxt/INDEX13041119.SHTML'.decode('utf-8')
    print get_domain(url)
