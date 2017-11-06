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
	pre_url="http://"+response.url[7:-1].split('/')[0]+"/loupan"
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
			    raise Exception
                    	house_col1=house_info.xpath('./div[@class="col-1"]')[0]
		    	house_col2=house_info.xpath('./div[@class="col-2"]')[0]	
		    
 		    	house_title=house_col1.xpath('./h2/a/text()')
			if house_title:
			    house_title=house_title[0]
			else:
			    house_title=""
		    
		    	self.log.info(house_title.encode('utf-8'))#title
		    	house_href=house_col1.xpath('./h2/a/@href')
			if house_href:
			    house_href=house_href[0]
			else:
			    house_href="" 		    
		    	self.log.info(house_href.encode('utf-8'))#house_href
		    	house_scale=house_col1.xpath('./div[@class="area"]/span/text()')
		    	if house_scale:
                   	    self.log.info(house_scale[0].strip().encode('utf-8'))#house_scale
			    house_scale=house_scale[0].strip()
			else:
			    house_scale=-1
		    	house_type=house_col1.xpath('./div[@class="area"]/text()')
			if house_type:
			    house_type=house_type[0].strip()
		    	    self.log.info(house_type.encode('utf-8'))#house type
			else:
			    house_type=-1
		    	where=house_col1.xpath('./div[@class="where"]/span/text()')
			if where:where=where[0]
			else:where=""
                    	self.log.info(where.strip().encode('utf-8'))#house location
                   	house_aver_price=house_col2.xpath('./div[@class="price"]/div[@class="average"]/span')
			if house_aver_price:
		    	    house_aver_price=house_aver_price[0].xpath('./text()')[0]
			    self.log.info(house_aver_price.encode('utf-8'))#house average price
		    	else:
			    self.log.info("-1")
			    house_aver_price=-1
		    	#self.log.info("ok")
		    	house_total_price=house_col2.xpath('./div[@class="price"]/div[@class="sum-num"]')
		    	#self.log.info("ok")
		    	if len(house_total_price)>=1:
				house_total_price=house_col2.xpath('./div[@class="price"]/div[@class="sum-num"]/span/text()')[0]
				#self.log.info('ok')  	    
		    		self.log.info(house_total_price.encode('utf-8'))#house total_price
			else:
				house_total_price=-1
				self.log.info("-1")
		    	save["location_url"]=location_url
		    	save["house_title"]=house_title
		    	save["house_href"]=house_href
		    	save["house_scale"]=house_scale
		    	save["house_type"]=house_type
		    	save["house_where"]=where
		    	save["house_aver_price"]=house_aver_price
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
		    next_page_url=node[0].xpath('./div[@class="page-box house-lst-page-box"]/@page-data')
		    if next_page_url:next_page_url=next_page_url[0]
		    else:raise Exception
	 	    #self.log.info("next ok")
		    #self.log.info(next_page_url)
		    page_json=json.loads(next_page_url)
		    if int(page_json["totalPage"])>int(page_json["curPage"]):
		        #self.log.info("next ok ok ")
		        self.crawl(pre_url+"/pg"+str(page_json["curPage"]+1),task,callback=self.index_page)
		        #self.log.info("return")
		    else:print "end one city"
		except Exception,e:
			self.log.info("---------------------------------------------------------eorror-------------------------")
			print e
			pass;
		
    def article_page(self, response, task):
        save = response.save
	doc=response.doc
	doc_string=response.text
	if doc_string.find("point:")>=0:
	    s_index=doc_string.find("point:")
	    end_index=doc_string.find("loupanName")
	    poi_data=doc_string.strip()[s_index+8:end_index-3]
	    poi_string=poi_data.strip()[:-2]
	    #self.log.info(poi_string.strip())
	    x_data=poi_string.strip().split(',')[0].strip()[11:-1]
	    y_data=poi_string.strip().split(',')[1].strip()[11:-2]
	    self.log.info(x_data)
	    self.log.info(y_data)
	else:
	    x_data=-1
	    y_data=-1
	    #self.log.info("+++++++++++++++++++++++++++++++++++++good++++++++++++++++++++++++++++++++++++++++++++")
        if save is not None and doc is not None:
            result = dict()
            result['program_location'] = doc.xpath('//div[@class="box-loupan"]/p[@class="desc-p clear"]/span[@class="label-val"]/text()')
            result['program_time'] = doc.xpath('//div[@class="box-loupan"]/ul[@class="table-list clear"]/li[1]/p/span[@class="label-val"]/text()')
	    result['live_time'] = doc.xpath('//div[@class="box-loupan"]/ul[@class="table-list clear"]/li[3]/p/span[@class="label-val"]/text()')
            result['house_num'] =doc.xpath('//div[@class="box-loupan"]/ul[@class="table-list clear"]/li[7]/p/span[@class="label-val"]/text()') 
	    result['live_area'] = doc.xpath('//div[@class="box-loupan"]/ul[@class="table-list clear"]/li[15]/p/span[@class="label-val"]/text()')
	    result['building_area'] = doc.xpath('//div[@class="box-loupan"]/ul[@class="table-list clear"]/li[16]/p/span[@class="label-val"]/text()')
            if result['program_location']:
                result['program_location'] = result['program_location'][0].strip()
            if result['program_time']:
                result['program_time'] = result['program_time'][0].strip()
            if result['live_time']:
                result['live_time'] = result['live_time'][0].strip()
            if result['house_num']:
                result['house_num'] =result['house_num'][0].strip()
            if result['live_area']:
                result['live_area']=result['live_area'][0].strip()
	    if result['building_area']:
		result['building_area']=result['building_area'][0].strip()
	    
	    if save['location_url']:
		result['city']=save['location_url']
	    if save['house_title']:
		result['house_title']=save['house_title']
	    if save['house_href']:
		result['house_href']=save['house_href']
	    if save['house_scale']:
		result['house_scale']=save['house_scale']
	    if save['house_type']:
		result['house_type']=save['house_type']
	    if save['house_where']:
		result['house_where']=save['house_where']
	    if save['house_aver_price']:
		result['house_aver_price']=save['house_aver_price']
	    if save['house_total_price']:
		result['house_total_price']=save['house_total_price']
	    poi=dict()
	    poi['x']=y_data
	    poi['y']=x_data
	    result['poi']=poi
	    #self.log.info(result['program_time'].encode('utf-8'))
            return result

__handler_cls__ = LianjiaSpider
