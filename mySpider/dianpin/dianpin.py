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
import time
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
        if doc is not None:
	    self.log.info("1")
	    node=doc.xpath('//a[@class="city J-city"]')
	    if node:city_name=node[0].xpath('./text()')[0]#city_name
	    list_node=doc.xpath('//div[@id="shop-all-list"]')
	    if list_node:
                shop_list_tree= list_node[0].xpath('./ul')
		if shop_list_tree:
		    shop_list_tree=shop_list_tree[0]
		else:self.log.info('error1')
                self.log.info('2')
		shop_list=shop_list_tree.xpath('./li')
                self.log.info('3')
		for shop in shop_list:
		    try:
		    	save=dict()
		    	shop_info=shop.xpath('./div[@class="txt"]')
			map_info=shop.xpath('./div[@class="operate J_operate Hide"]')
			if shop_info:
			    shop_info=shop_info[0]
			else:
			    self.log.info('error2')
			if map_info:
			    map_info=map_info[0]
			else:
			    self.log.info('error3')
                    	col1=shop_info.xpath('./div[@class="tit"]')
		    	col2=shop_info.xpath('./div[@class="comment"]')
			col3=shop_info.xpath('./div[@class="tag-addr"]')
			col4=shop_info.xpath('./span[@class="comment-list"]')
			if col1:
			    col1=col1[0]
			    title=col1.xpath('./a[1]/@title')[0]#name
			    self.log.info(title)
			    href=col1.xpath('./a[1]/@href')[0]#href
			    self.log.info(href)
			if col2:
			    col2=col2[0]
			    if col2.xpath('./span'):
				star=col2.xpath('./span/@title')[0]#star
				self.log.info(star)
			    if col2.xpath('./a[@class="mean-price"]'):
				mean_price=col2.xpath('./a[@class="mean-price"]/b')
				if mean_price:mean_price=mean_price[0].xpath('./text()')[0]
				else:mean_price=0
				self.log.info(mean_price)#price
		 	if col3:
			    col3=col3[0]
			    shop_area=col3.xpath('./a[2]/span/text()')#area
			    if shop_area:
				shop_area=shop_area[0]
			    else:
				shop_area=""
			    self.log.info(shop_area)
		            shop_address=col3.xpath('./span/text()')#address
			    if shop_address:
				shop_address=shop_address[0]
			    else:
				shop_address=""
			    self.log.info(shop_address)
			if col4:
			    col4=col4[0]
			    taset_score=col4.xpath('./span[1]/b/text()')[0]#tast_score
			    self.log.info(taset_score)
			    env_score=col4.xpath('./span[2]/b/text()')[0]#env_score
			    self.log.info(env_score)
			    ser_score=col4.xpath('./span[3]/b/text()')[0]#service_score
			    self.log.info(ser_score)
			else:
			    taset_score=0
			    env_score=0
			    ser_score=0
			shop_poi=map_info.xpath('./a[@class="o-map J_o-map"]')
			if shop_poi:shop_poi=shop_poi[0].xpath('./@data-poi')[0]
			self.log.info(shop_poi)
		        
		    	save["shop_name"]=title
		    	save["shop_href"]=href
		    	save["shop_star"]=star
		    	save["shop_mean_price"]=mean_price
			save['shop_area']=shop_area
			save['shop_address']=shop_address
			save['taset_score']=taset_score
			save['env_score']=env_score
			save['ser_score']=ser_score
			save['shop_poi']=shop_poi
			save['city']=city_name
		        yield save
		    except Exception, e:
			#pass
			self.log.info("######################################error#########################################")
			print e
			pass
		try:
		    time.sleep(1)
		    next_page_url=doc.xpath('//div[@class="page"]/a[@class="next"]')
		    if next_page_url:
			next_page_num=next_page_url[0].xpath('./@data-ga-page')[0]
		        self.log.info(next_page_num)
		    else:
			raise Exception
		    end_index=response.url.rfind('/')
		    next_page_url=response.url[0:end_index]+'/p'+next_page_num
		    self.log.info(next_page_url)
		    self.crawl(next_page_url,task,callback=self.index_page)
		except Exception,e:
			self.log.info("---------------------------------------------------------end this city-------------------------")
			print e
			pass;
		
		
__handler_cls__ = LianjiaSpider
