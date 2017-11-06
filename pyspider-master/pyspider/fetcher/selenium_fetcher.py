#!/usr/bin/python
# -*- coding:utf-8 -*-

from selenium import webdriver
import time

def selenium_test(url):
    begin_time = time.time()
    #driver = webdriver.PhantomJS(service_args=['--load-images', 'false', '', ''])
    driver = webdriver.Firefox()
    driver.set_page_load_timeout(20)
    driver.get(url)
    end_time = time.time()
    print end_time - begin_time
    with open('html', 'wb') as fi:
        fi.write(driver.page_source.encode('utf-8'))

def selenium_fetch():
    pass


if __name__ == '__main__':
    selenium_test(u'http://hotels.ctrip.com/hotel/1000203.html')