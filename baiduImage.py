import argparse
import os
import re
import sys
import urllib
import json
import socket
import urllib.request
import urllib.parse
import urllib.error
import random
 
# 设置超时
import time
 
from flask import Flask, redirect, request, make_response
import random
 
timeout = 5
socket.setdefaulttimeout(timeout)
 
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
 
 
class Crawler:
    # 睡眠时长
    __time_sleep = 0.1
    __amount = 0
    __start_amount = 0
    __counter = 0
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:23.0) Gecko/20100101 Firefox/23.0', 'Cookie': ''}
    __per_page = 30
 
    # 获取图片url内容等
    # t 下载图片时间间隔
    def __init__(self, t=0.1):
        self.time_sleep = t
 
    @staticmethod
    def handle_baidu_cookie(original_cookie, cookies):
        """
        :param string original_cookie:
        :param list cookies:
        :return string:
        """
        if not cookies:
            return original_cookie
        result = original_cookie
        for cookie in cookies:
            result += cookie.split(';')[0] + ';'
        result.rstrip(';')
        return result
 
    # 开始获取
    def get_images(self, word):
        search = urllib.parse.quote(word)
        pn = self.__start_amount
        image_urls = []
        while pn < self.__amount:
            url = 'https://image.baidu.com/search/acjson?tn=resultjson_com&ipn=rj&ct=201326592&is=&fp=result&queryWord=%s&cl=2&lm=-1&ie=utf-8&oe=utf-8&adpicid=&st=-1&z=&ic=&hd=&latest=&copyright=&word=%s&s=&se=&tab=&width=&height=&face=0&istype=2&qc=&nc=1&fr=&expermode=&force=&pn=%s&rn=%d&gsm=1e&1594447993172=' % (
                search, search, str(pn), self.__per_page)
            try:
                time.sleep(self.time_sleep)
                req = urllib.request.Request(url=url, headers=self.headers)
                page = urllib.request.urlopen(req)
                self.headers['Cookie'] = self.handle_baidu_cookie(self.headers['Cookie'],
                                                                page.info().get_all('Set-Cookie'))
                rsp = page.read()
                page.close()
            except UnicodeDecodeError as e:
                print(e)
                print('-----UnicodeDecodeErrorurl:', url)
            except urllib.error.URLError as e:
                print(e)
                print("-----urlErrorurl:", url)
            except socket.timeout as e:
                print(e)
                print("-----socket timout:", url)
            else:
                rsp_data = json.loads(rsp, strict=False, object_hook=lambda d: {k: urllib.parse.unquote(v) if isinstance(v, str) else v for k, v in d.items()})
                if 'data' not in rsp_data:
                    continue
                else:
                    for image_info in rsp_data['data']:
                        if 'thumbURL' in image_info:
                            thumb_url = image_info['thumbURL']
                            image_urls.append(thumb_url)
                pn += self.__per_page
                return image_urls
 
    def start(self, word):
        self.__per_page = 30
        self.__start_amount = 0
        self.__amount = self.__per_page
        return self.get_images(word)
