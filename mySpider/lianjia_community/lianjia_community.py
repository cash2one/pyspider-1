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


    ##@every(minutes=120)
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
	pre_url="http://"+response.url[7:-1].split('/')[0]+"/xiaoqu"
	self.log.info(location_url)#city
        if doc is not None:
	    self.log.info("1")
	    node=doc.xpath('//div[@class="list-wrap"]')
	    if node:
                house_list_tree= node[0].xpath('./ul[@class="house-lst"]')
		if house_list_tree:
		    house_list_tree=house_list_tree[0]
		else:self.log.info('error1')
                self.log.info('2')
		house_list=house_list_tree.xpath('./li')
                self.log.info('3')
		for house in house_list:
		    try:
		    	save=dict()
		    	house_info=house.xpath('./div[@class="info-panel"]')
			if house_info:
			    house_info=house_info[0]
			else:
			    self.log.info('error2')
                    	house_col1=house_info.xpath('./div[@class="col-1"]')[0]
		    	house_col3=house_info.xpath('./div[@class="col-3"]')[0]	
		        
 		    	house_title=house_info.xpath('./h2/a/text()')[0]
		        
		    	self.log.info(house_title.encode('utf-8'))#title
		    	house_href=house_info.xpath('./h2/a/@href')[0]
 		    
		    	self.log.info(house_href.encode('utf-8'))#house_href
			info_detail=house_col1.xpath('./div[@class="other"]')
			if info_detail:
			    house_where=info_detail[0].xpath('./div/a[1]/text()')[0]+info_detail[0].xpath('./div/a[2]/text()')[0]
			else:house_where=""
			self.log.info(house_where)#house_where
		    	house_total_price=house_col3.xpath('./div[@class="price"]/span')
		    	#self.log.info("ok")
		    	if house_total_price[0].xpath('./span'):
				house_total_price=0
				self.log.info("0")
			else:
				house_total_price=house_total_price[0].xpath('./text()')[0]
				#self.log.info('ok')  	    
		    		self.log.info(house_total_price.encode('utf-8'))#house total_price
		    	save["location_url"]=location_url
		    	save["house_title"]=house_title
		    	save["house_where"]=house_where
		    	save["house_total_price"]=house_total_price
		    	#self.log.info(house_href)  
                    	self.crawl(house_href, task, callback=self.article_page, save=save)
			#self.log.info("next page ana")
		    except Exception, e:
			#pass
			self.log.info("######################################error#########################################")
			print e
			pass
		
		try:
	            #self.log.info(node)	
		    next_page_url=doc.xpath('//div[@class="page-box house-lst-page-box"]/@page-data')
		    if next_page_url:
			next_page_url=next_page_url[0]
		    else:raise Exception
	 	    #self.log.info("next ok")
		    #self.log.info(next_page_url)
		    page_json=json.loads(next_page_url)
		    if int(page_json["totalPage"])>int(page_json["curPage"]):
		        #self.log.info("next ok ok ")
		        self.crawl(pre_url+"/pg"+str(page_json["curPage"]+1),task,callback=self.index_page)
		        #self.log.info("return")
		except Exception,e:
			self.log.info("---------------------------------------------------------eorror-------------------------")
			print e
			pass;
		
    def article_page(self, response, task):
        save = response.save
	doc=response.doc
	doc_string=response.text
	if doc_string.find("resblockPosition:")>=0:
	    s_index=doc_string.find("resblockPosition:")
	    end_index=doc_string.find("cityId:")
	    poi_data=doc_string.strip()[s_index+17:end_index-2].strip()[1:-2]
	    city_id=doc_string[end_index+7:end_index+15].strip()
	    self.log.info(poi_data)
	    #self.log.info(city_id)
	elif doc_string.find("coordinates:")>=0:
	    s_index=doc_string.find("coordinates:")
	    poi_data=doc_string.strip()[s_index+12:s_index+37].strip()[1:-2]
	    self.log.info(poi_data)
	else:
	    poi_data=-1
	    #self.log.info("+++++++++++++++++++++++++++++++++++++good++++++++++++++++++++++++++++++++++++++++++++")
        if save is not None and doc is not None:
            result = dict()
	    
	    if save['location_url']:
		result['city']=save['location_url']
	    if save['house_title']:
		result['house_area']=save['house_title']
	    if save['house_where']:
		result['house_where']=save['house_where']
	    if save['house_total_price']:
		result['house_aver_price']=save['house_total_price']
	    result['poi']=poi_data
	    #result['city_id']=city_id
	    #self.log.info(result['program_time'].encode('utf-8'))
            return result

__handler_cls__ = LianjiaSpider
