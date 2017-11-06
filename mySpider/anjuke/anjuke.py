#!/usr/bin/pytho
# -*- coding:utf-8 -*-
import xml.etree.ElementTree as ET
from pyspider.spider.base_handler import *
from lxml import etree
import random
import tornado.gen
import tornado.httpclient
import time
import re
import json
from pyspider.fetcher.tonado_cookies import cookie_to_dict

pool_size = 1

class LianjiaSpider(BaseHandler):
    """spider to crawl linjia"""


    ####@every(minutes=120)
    def on_start(self, response, task):
        seed_file = task['seed_path']
        url_list = []
        self.log.info("hello")
        with open(seed_file, 'rb') as fi:
            for line in fi:
                url = line.strip()
                if url:
                    url_list.append(url)
        self.log.info(url_list)
        for url in url_list:
            self.crawl(url, task, callback=self.index_page)

    def index_page(self, response, task):
        doc = response.doc
        self.log.info(doc)
	location_url=response.url[7:-1].split('.')[0]
	pre_url="http://"+response.url[7:-1].split('/')[0]+"/community"
	self.log.info(location_url)#city
        if doc is not None:
	    self.log.info("1")
            node=doc.xpath('//div[@class="list-content"]')
	    if node:
		self.log.info("2")
                house_list= node[0].xpath('./div[@class="li-itemmod"]')
		for house in house_list:
		    try:
		    	save=dict()
		    	house_info=house.xpath('./div[@class="li-info"]')
			if house_info:
			    house_info=house_info[0]
			else:
			    raise Exception
			
                    	house_col1=house_info.xpath('./h3/a/@title')
			if house_col1:
			    house_area=house_col1[0]
			else:
			    house_area=0
			self.log.info(house_area)#
			house_href=house_info.xpath('./h3/a/@href')
			self.log.info(house_href[0])			
		    	house_col2=house_info.xpath('./address/text()')
			if house_col2:
			    house_address=house_col2[0].strip()
			else:
			    house_address=""
			self.log.info(house_address)#
		        house_price=house.xpath('./div[@class="li-side"]')
			if house_price:
			    price=house_price[0].xpath('./p/strong/text()')
			    if price:price=price[0].strip()
			    else:price=0
		        else:
			    price=0
			self.log.info(price)#
		    	save["house_title"]=house_area
		    	save["house_where"]=house_address
		    	save["house_aver_price"]=price
			if house_href:			
		    	#self.log.info(house_href)  
                    	    self.crawl(house_href[0], task, callback=self.article_page, save=save)
			else:
			    raise Exception
			#self.log.info("next page ana")
		    except Exception, e:
			#pass
			self.log.info("######################################error#########################################")
			print e
			pass
		
		try:
	            #self.log.info(node)	
		    next_page_url=doc.xpath('//a[@class="aNxt"]')		
		    if next_page_url:next_page_url=next_page_url[0].xpath('./@href')[0]
		    else:raise Exception
		    self.log.info(next_page_url)
		    self.crawl(next_page_url,task,callback=self.index_page)
		except Exception,e:
			self.log.info("---------------------------------------------------------end this city-------------------------")
			print e
			pass;
		
    def article_page(self, response, task):
        save = response.save
	doc=response.doc
	doc_string=response.text
	if doc_string.find("comm_info")>=0:
	    s_index=doc_string.find("comm_info")
	    end_index=doc_string.find("var city_id")
	    poi_data=doc_string.strip()[s_index+11:end_index-3]
	    poi_string=poi_data.strip()
	    self.log.info(poi_string)
	    
	    x_data=poi_string.split(':')[-1]
	    y_data=poi_string.split(':')[-2]
	    end_index1=x_data.find('/')
	    self.log.info(x_data[0:end_index1].strip()[0:])
	    end_index2=y_data.find('/')
	    self.log.info(y_data[0:end_index2].strip()[0:-1])
            x_data=x_data[0:end_index1].strip()[0:]
	    y_data=y_data[0:end_index2].strip()[0:-1]
	    #self.log.info("+++++++++++++++++++++++++++++++++++++good++++++++++++++++++++++++++++++++++++++++++++")
        if save is not None and doc is not None:
            result = dict()
            if len(save['house_title']):
                result['house_area'] = save['house_title']
            if len(save['house_where']):
                result['house_where'] = save['house_where']
            result['price'] =save['house_aver_price']
	    poi=dict()
	    poi['x']=y_data
	    poi['y']=x_data
	    result['poi']=poi
            return result

__handler_cls__ = LianjiaSpider
