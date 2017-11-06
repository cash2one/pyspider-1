#!/usr/bin/python
# -*- coding:utf-8 -*-

import urllib2
import threading
import sys
import json
import re
import os
from collections import deque
import lxml.html as html
import traceback

result_link = deque()
pat = re.compile(r'/hotel/\d*.html')
city_code = deque()

def get_hotel_info(item, fo):
    #item = json.loads(line.decode('utf-8'))
    hotel_list = item['hotelList']
    hotel_info = item['hotelPositionJSON']
    hotel_num = len(hotel_info)
    doc = html.fromstring(hotel_list.strip())
    #url = hotel_info['url']
    #url = doc.xpath('//li[@class="searchresult_info_name"]/h2[@class="searchresult_name"]/a/@href')
    #estimate = doc.xpath('//p[@class="medal_list"]/span/@title')
    #price = doc.xpath('//div[@class="hotel_price"]/span/text()')
    pricelist = doc.xpath('//li[@class="searchresult_info_name"]')
    price = []
    for item in pricelist:
       name = item.xpath('//div[@class="hotel_price"]/span/text()')
       if len(name) != 0:
           price.append(int(name[0]))
       else:
           price.append(0)

    # print "%d\t%d\t%d\t%d" % (hotel_num, len(url), len(estimate), len(price))
    # if hotel_num != len(price):
    #     return
    #print str(len(price)) + '\t' + str(hotel_num)
    if len(price)  == hotel_num:
        for i in xrange(hotel_num):
            result = {}
            result['url'] = "http://hotels.ctrip.com%s" % hotel_info[i]['url'].split('#')[0]
            ##result['estimate'] = estimate[i]
            result['price'] = price[i]
            result['star'] = hotel_info[i]['star']
            result['score'] = hotel_info[i]['score']
            result['short_name'] = hotel_info[i]['shortName']
            result['stardesc'] = hotel_info[i]['stardesc']
            result['title'] = hotel_info[i]['name']
            fo.write(json.dumps(result, ensure_ascii=False).encode('utf-8', 'ignore')+'\n')
    else:
        #print >> sys.stderr, "parser wrong: %d\t %d\t %d" % (len(url), len(estimate), len(price))
        print "error"


def load_city_code():
    pat2 = re.compile(r'/hotel/[^\d]*(\d*)')
    fi = open('6121_result')
    line = fi.readline()
    items = json.loads(line)
    for link in items['city_link']:
        m = pat2.match(link)
        if m:
            city_code.append(m.groups()[0])

def request(city_code, page=1):
    url = 'http://hotels.ctrip.com/Domestic/Tool/AjaxHotelList.aspx?city=%s&page=%s' % (city_code, page)
    request = urllib2.Request(url)
    response = urllib2.urlopen(request)
    status_code = response.getcode()
    if status_code >= 200 and status_code < 400:
        result = response.read()
        result = re.sub(r"\\\\x", r'\\x', result)
        return result.strip()
    else:
        print >> sys.stderr, url
        return None

def parse_city_nextpage(city_code, fo, page):
    result = request(city_code, page)
    if result:
        try:
            result = json.loads(result.decode('utf-8'))
        except Exception as e:
            traceback.print_exc(file=sys.stderr)
            print >> sys.stderr, result
            return
        #hotel_links = set(pat.findall(result['hotelList']))
        get_hotel_info(result, fo)
        #for hotel_link in hotel_links:
            #hotel_link = "http://hotels.ctrip.com%s" % hotel_link.encode('utf-8', 'ignore')
            #result_link.append(hotel_link)
        #fo.write(hotel_link+os.linesep)

def parse_city(city_code, fo, page=1):
    result = request(city_code, page)
    if result:
        result = json.loads(result.decode('utf-8'))
        hotel_num = int(result['hotelAmount'])
        page_num = (hotel_num+25)/25
        get_hotel_info(result, fo)
        #hotel_links = set(pat.findall(result['hotelList']))
        #for hotel_link in hotel_links:
            #hotel_link = "http://hotels.ctrip.com%s" % hotel_link.encode('utf-8', 'ignore')
            #result_link.append(hotel_link)
            #fo.write(hotel_link+os.linesep)
        #print page_num
        if page_num > page:
            for i in xrange(page, page_num):
                try:
                    parse_city_nextpage(city_code, fo, i+1)
                except Exception as e:
                    traceback.print_exc(file=sys.stderr)


def parse_start(fo):
    global city_code
    while True:
        try:
            city = city_code.popleft()
            parse_city(city, fo, 1)
        except IndexError:
            break

def multi_get_hotel_link(thread_count = 100):
    print >> sys.stderr, "begin"
    fo = open('hotel_price_result2', 'w+')
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
   multi_get_hotel_link(50)