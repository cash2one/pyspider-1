#coding=gbk
#/***************************************************************************
# * 
# * Copyright (c) 2013 Baidu.com, Inc. All Rights Reserved
# * 
# **************************************************************************/
 
#/**
# * @file 
# * @author shenjianping(com@baidu.com)
# * @date 2013.05.30
# * @brief 
# *  
# **/
import sys
import pyurl

def GetSite(url):
    #reg = 'http://.*?\.(com.cn|org.cn|net.cn|org|com|cn|net)'
    #match = re.match(reg,url)
    #if match:
    #    return match.group()[7:]
    pyurl.setMultiSchemes(1)
    pyurl.normalizeUrl(url)
    domain = pyurl.getMainDomain(url)
    
    return domain

def test():
    url = sys.argv[1]
    site = GetSite(url)
    print site
if __name__ == '__main__':
    test()

    

    
#/* vim: set expandtab ts=4 sw=4 sts=4 tw=100: */
