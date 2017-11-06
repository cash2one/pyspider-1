#!/usr/bin/python
# -*- coding:utf-8 -*-
"""
@Author: xuguoqiang@baidu.com
@Date: 2015/08/10
"""

import urllib2
import threading
import sys
import json
import re
import os
from collections import deque
import lxml.html as html

result_link = deque()
pat = re.compile(r'/hotel/\d*.html')
city_code = deque()

def get_hotel_info(item, fo):
    hotel_info = item['HotelPositionJSON']
    hotel_num = len(hotel_info)
    location = []
    navagation = item['Navagation']
    location = re.sub(r'<[^>]+>', '', navagation).replace(' ', '').replace(u'酒店', '').split('&gt;')

    if hotel_num > 0:
        for i in xrange(hotel_num):
            result = {}
            result['url'] = "http://hotels.ctrip.com%s" % hotel_info[i]['url']
            result['price'] = hotel_info[i]['price']
            result['star'] = hotel_info[i]['star']
            result['score'] = hotel_info[i]['score']
            result['stardesc'] = hotel_info[i]['stardesc']
            result['title'] = hotel_info[i]['name']
            result['location'] = location
            fo.write(json.dumps(result, ensure_ascii=False).encode('utf-8', 'ignore')+'\n')
    else:
        print "error"
        pass

def load_city_code():
    # pat2 = re.compile(r'http://hotels.ctrip.com/international/[^\d]*(\d*)')
    # fi = open('6138_result')
    # line = fi.readline()
    # items = json.loads(line)
    # for link in items['hotel_link']:
    #     m = pat2.match(link)
    #     if m:
    #         city_code.append(m.groups()[0])
    with open('ctrip_abroad_hotel_city_code', 'r') as fi:
        for line in fi:
            city_code.append(int(line.strip()))

def request(city_code, page=1):
    url = 'http://hotels.ctrip.com/international/tool/AjaxHotelList.aspx?cityId=%s&pageIndex=%s' % (city_code, page)
    request = urllib2.Request(url)
    response = urllib2.urlopen(request)
    status_code = response.getcode()
    if status_code >= 200 and status_code < 400:
        result = response.read()
        result = re.sub(r"\\x26([a-zA-Z]{2,6});", r"&\1;", result)
        return result.strip()
    else:
        print >> sys.stderr, "error"
        return None

def parse_city_nextpage(city_code, fo, page):
    result = request(city_code, page)
    if result:
        result = json.loads(result.decode('utf-8'))
        get_hotel_info(result, fo)

def parse_city(city_code, fo, page=1):
    result = request(city_code, page)
    if result:
        result = json.loads(result.decode('utf-8'))
        page_num = int(result['totalPage'])
        get_hotel_info(result, fo)
        if page_num > page:
            for i in xrange(page, page_num):
                try:
                    parse_city_nextpage(city_code, fo, i+1)
                except:
                    pass

def parse_start(fo):
    global city_code
    while True:
        try:
            city = city_code.popleft()
            parse_city(city, fo, 1)
        except IndexError:
            break

def multi_get_hotel_link(thread_count = 100):
    """get hotel link use multi thread"""
    print >> sys.stderr, "begin"
    fo = open('test', 'w+')
    if len(city_code) == 0:
        return
    threads = [threading.Thread(target=parse_start, args=(fo,)) for i in xrange(thread_count)]
    for i in xrange(thread_count):
        threads[i].start()
    for i in xrange(thread_count):
        threads[i].join()
    fo.close()
    print >> sys.stderr, 'done'

if __name__ == '__main__':
   load_city_code()
   multi_get_hotel_link(40)
