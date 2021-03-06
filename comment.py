from bs4 import BeautifulSoup
import requests
from lxml import etree
import re
from pymongo import MongoClient
import urllib3

cookie = {"Cookie": "your_cookie"}
urllib3.disable_warnings()
client = MongoClient()
db = client['weibo']

def get_weibo_comment(url):
    weibo_serial = url[25:34]
    collection = db[weibo_serial]
    html = requests.get(url, cookies=cookie, verify=False).content
    selector = etree.HTML(html)
    pagenum = int(selector.xpath('//input[@name="mp"]')[0].attrib['value'])
    for i in range(1, pagenum+1):
        pageurl = url + "&page=" + str(i)
        pagehtml = requests.get(pageurl, cookies=cookie, verify=False).content
        soup = BeautifulSoup(pagehtml, 'lxml')
        creg = re.compile('C_\d{16}')
        content = soup.find_all(attrs={'id': creg})
        for con in content:
            weibo_item = {
                'name': con.a.string,# 发布人微博ID
                'content': con.find_all(attrs={'class': 'ctt'})[0].get_text(),# 微博内容
                'time&device': con.find_all(attrs={'class': 'ct'})[0].get_text().replace(u'\xa0', u' ')# 发布时间及设备
            }
            print(weibo_item)
            if collection.insert_one(weibo_item):
                print('Saved to Mongo')

if __name__ == '__main__':
    url = 'https://weibo.cn/comment/Hpup0v9MW'
    get_weibo_comment(url)
