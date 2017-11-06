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

class AnjukeShenzhen(BaseHandler):
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
		if doc is not None:
			#self.log.info("indexPage")
			node1=doc.xpath('//div[@id="container"]/div[@class="list-contents"]')
			#self.log.info(node1[0])
			node2=node1[0].xpath('./div[@class="list-results"]')
			#self.log.info(node2[0])
			node=node2[0].xpath('./div[@class="key-list"]')
			#self.log.info(node[0])
			if node:
				#self.log.info("index page is Crawled")
				house_list= node[0].xpath('./div[@class="item-mod"]')
				for house in house_list:
					try:
						save=dict()
						house_info=house.xpath('./div[@class="infos"]')
						if house_info:
							house_info=house_info[0]
						else:
							raise Exception
						house_col1=house_info.xpath('./a[@class="lp-name"]/h3/span[@class="items-name"]/text()')
						if house_col1:
							house_area=house_col1[0]
						else:
							house_area=0
						#self.log.info(house_area)#
						house_href=house_info.xpath('./a[@class="lp-name"]/@href')
						#self.log.info(house_href[0])			
						house_col2=house_info.xpath('./a[@class="address"]/span[@class="list-map"]/text()')
						if house_col2:
							house_address=house_col2[0].strip()
						else:
							house_address=""
						#self.log.info(house_address)#
						house_col3=house.xpath('./a[@class="favor-pos"]/p[@class="price"]/span/text()')
						if house_col3:
							house_price=house_col3[0].strip()
						else:
							house_price=0
						house_col4=house.xpath('./a[@class="favor-pos"]/p[@class="tel"]/text()')
						if house_col4:
							house_phone=house_col4[0].strip()
						else:
							house_phone=''
						house_col5=doc.xpath('//div[@id="header"]/div[@class="site-search"]/div[@class="sel-city"]/a/span/text()')
						if house_col5:
							house_city=house_col5[0]
						else:
							house_city=""
						#self.log.info(house_address)
						save["district"]=house_address.strip().split(']')[0][1:-1]
						save["house_phone"]=house_phone
						save["house_title"]=house_area
						save["house_where"]=house_address
						save["house_aver_price"]=house_price
						save["city"]=house_city
						save["country"]='中国'
						if house_href:			
							#self.log.info(house_href)
							with open("url.txt","a+") as f:
								f.write(str(house_href[0])+'\n')  
							self.crawl(house_href[0], task, callback=self.article_page, save=save)
						else:
							raise Exception
						#self.log.info("next page ana")
					except Exception, e:
						#pass
						self.log.info("######################################error#########################################")
						print e
						pass
		
			try:		#self.log.info(node)	
				next_page_url=node2[0].xpath('./div[@class="list-page"]/div[@class="pagination"]/a[@class="next-page next-link"]/@href')		
				if next_page_url:
					next_page_url=next_page_url[0]
					#self.log.info("next page:")
					self.crawl(next_page_url,task,callback=self.index_page)
				else:
					raise Exception
			except Exception,e:
				self.log.info("---------------------------------------------------------end this city-------------------------")
		
	def article_page(self, response, task):
		save = response.save
		doc=response.doc
		doc_string=response.text
		self.log.info("article_page:")
		if doc is not None:
			self.log.info("aaaaaa")
			node=doc.xpath('//div[@id="container"]/div[@class="main-detail mod"]/div[@class="basic-details"]')
			if len(node)>0:
				self.log.info("bbbbbb")
				try:
                    save['house_kaipanTime']=''
                    save['house_nianxian']=''
					house_kaipanTime=node[0].xpath('./div[@class="brief-info basic-parms"]/p[@class="info-new"]')[0].xpath('./span/text()')
					if len(house_kaipanTime)>0:
						self.log.info("cccccc")
						house_kaipanTime=house_kaipanTime[0]
						save['house_kaipanTime']=house_kaipanTime
					else:
						save['house_kaipanTime']=''
					house_nianxian=node[0].xpath('./div[@class="brief-info basic-parms"]/div[@class="clearfix"]/ul[@class="info-left"]/li')[1].xpath('./span/text()')
					if len(house_nianxian)>0:
						self.log.info('dddddd')
						house_nianxian=house_nianxian[0]
						save['house_nianxian']=house_nianxian
						#self.log.info("house_nianxian")
					else:
						save['house_nianxian']=''
					comment_href=doc.xpath('//div[@id="container"]/div[@class="clearfix user-clear"]/div[@class="user-reviews fl"]/div[@class="main-title"]/a[@class="more"]/@href')
					if len(comment_href)>0:
						with open("comment_url.txt","a+") as f:
							f.write(str(comment_href[0])+'\n')
						self.log.info("comment_url:")
						self.crawl(comment_href[0],task,callback=self.comment_page,save=save)
					else:
						#self.crawl(comment_href[0],task,callback=self.comment_page.save=save)
						self.log.info("comment_url is none")
						raise Exception
				except Exception,e:
					comment_href=doc.xpath('//div[@id="container"]/div[@class="clearfix user-clear"]/div[@class="user-reviews fl"]/div[@class="main-title"]/a[@class="more"]/@href')
					if len(comment_href)>0:
						with open("comment_url.txt","a+") as f:
							f.write(str(comment_href[0])+'\n')
						self.log.info("comment_url:")
						self.crawl(comment_href[0],task,callback=self.comment_page,save=save)
					print e
			else:
				self.log.info("article_page info is none!")
				return save
		else:
			self.log.info("article_page is none!")
			return save
	def comment_page(self,response,task):
		#self.log.info("comment_page:")
		save=response.save
		doc=response.doc
		node=doc.xpath('//div[@id="container"]/div[@class="ugc-content clearfix"]/div[@class="ugc-mod"]/div[@class="total-comment"]/div[@class="total-wrap"]/ul[@class="total-revlist"]')
		if len(node)>0:
			comment_list=node[0].xpath('./li')
			if len(comment_list)>0:
				#self.log.info("commentList is appended")
				for comment in comment_list:
					#self.log.info(comment)
					item=dict()
					id=comment.xpath('./span/@id')
					text=comment.xpath('./div[@class="clearfix"]/div[@class="info-mod"]/h4[@class="rev-subtit all-text"]/text()')
					name=comment.xpath('./div[@class="clearfix"]/div[@class="info-mod"]/div[@class="clearfix"]/a[@class="rev-name fl"]/span/text()')
					time=comment.xpath('./div[@class="clearfix"]/div[@class="info-mod"]/div[@class="tray-panel clearfix"]/span[@class="date"]/text()')
					replyNumber=comment.xpath('./div[@class="clearfix"]/div[@class="info-mod"]/div[@class="tray-panel clearfix"]/div[@class="share-praise fr"]/a[@class="reply-entry"]/em/text()')
					praiseNumber=comment.xpath('./div[@class="clearfix"]/div[@class="info-mod"]/div[@class="tray-panel clearfix"]/div[@class="share-praise fr"]/a[@class="praise-link"]/em/text()')
					shareNumber=comment.xpath('./div[@class="clearfix"]/div[@class="info-mod"]/div[@class="tray-panel clearfix"]/div[@class="share-praise fr"]/a[@class="tram-link"]/em/text()')
					if text:
						item['text']=text[0]
					else:
						item['text']=''
					if name:
						item['name']=name[0]
					else:
						item['name']=''
					if time:
						item['time']=time[0]
					else:
						item['time']=''
					if replyNumber:
						item['replyNumber']=replyNumber[0]
					else:
						item['replyNumber']=''
					if praiseNumber:
						item['praiseNumber']=praiseNumber[0]
					else:
						item['praiseNmber']=''
					if shareNumber:
						item['shareNumber']=shareNumber[0]
					else:
						item['shareNumber']=''
					save[id[0]]=item
		next_comment_href=doc.xpath('//div[@id="container"]/div[@class="ugc-content clearfix"]/div[@class="ugc-mod"]/div[@class="rev-pagination"]/div[@class="pagination"]/a[@class="next-page next-link"]/@href')
		if next_comment_href:
			self.crawl(next_comment_href[0],task,callback=self.comment_page,save=save)
		else:
			print "done"
			result=dict()
			comment=dict()
			details=dict()
			keyList=['city','country','district','house_phone','house_title','house_where','house_aver_price','house_kaipanTime','house_nianxian']
			for key in save:
				if key in keyList:
					details[key]=save[key]
				else:
					comment[key]=save[key]
			result['details']=details
			result['comment']=comment
			return result

__handler_cls__ = AnjukeShenzhen	
			
