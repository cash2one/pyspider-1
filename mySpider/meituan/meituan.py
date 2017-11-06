#!/usr/bin/python
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


    @every(minutes=120)
    def on_start(self, response, task):
        seed_file = task['seed_path']
        url_list = []
        self.log.info("hello")
        with open(seed_file, 'rb') as fi:
            for line in fi:
                url = line.strip()
                if url:
                    url_list.append(url)
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
                house_list= node[0].xpath('./div[@class="li-itemmod"]')
		for house in house_list:
		    try:
		    	save=dict()
		    	house_info=house.xpath('./div[@class="li-info"]')
			if house_info:
			    house_info=house_info[0]
			else:
			    raise Exception
                    	house_col1=house_info.xpath('./h3/@title')
			if house_col1:
			    house_area=house_col1[0]
			else:
			    house_area=0
			house_href=house_info.xpath('./h3/@href')			
		    	house_col2=house_info.xpath('./address/test()')
			if house_col2:
			    house_address=house_col2[0]
			else:
			    house_address=""
		        house_price=house.xpath('./div[@class="li-side"]')
			if house_price:
			    price=house_price[0].xpat('./p/strong/text()')
		        else:
			    price=0
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
		    next_page_url=node.xpath('./div[@class="aNxt"]')
		    if next_page_url:next_page_url=next_page_url[0].xpath('./@href')
		    else:raise Exception
		    self.crawl(next_page_url,task,callback=self.index_page)
		except Exception,e:
			self.log.info("---------------------------------------------------------eorror-------------------------")
			print e
			pass;
		
    def article_page(self, response, task):
        save = response.save
	doc=response.doc
	doc_string=response.text
	if doc_string.find("comm_info")>=0:
	    s_index=doc_string.find("comm_info")
	    end_index=doc_string.find("var city_id")
	    poi_data=doc_string.strip()[s_index+10:end_index-2]
	    poi_string=poi_data.strip()
	    poi_data=json.loads(poi_string.decode('utf-8'))
	    #self.log.info(poi_string.strip())
	    x_data=poi_data['comm_lat']
	    y_data=poi_data['comm_lng']
	    self.log.info(x_data)
	    self.log.info(y_data)
	else:
	    x_data=-1
	    y_data=-1
	    #self.log.info("+++++++++++++++++++++++++++++++++++++good++++++++++++++++++++++++++++++++++++++++++++")
        if save is not None and doc is not None:
            result = dict()
            if save['house_title']:
                result['house_area'] = save['house_title']
            if save['house_where']:
                result['house_where'] = save['house_where']
            if save['house_aver_price']:
                result['price'] =save['house_aver_price']
	    poi=dict()
	    poi['x']=y_data
	    poi['y']=x_data
	    result['poi']=poi
            return result

__handler_cls__ = LianjiaSpider
