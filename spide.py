import requests
import chardet
import json
import pymongo
from json.decoder import JSONDecodeError
from requests.exceptions import ConnectionError
#设置超时提醒，如果下载视频超过10秒就跳过
import socket
socket.setdefaulttimeout(10)
#最简单的反爬取措施
headers = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3377.1 Safari/537.36'}
#配置MongoDB数据库
client = pymongo.MongoClient('localhost')
db = client['KVideo']
#获取初始页的HTML
def get_one_page(url):
    try:
        res = requests.get(url,headers=headers)
        if res.status_code == 200:
            res.encoding = chardet.detect(res.content)['encoding']
            html = res.text
            return html
        return None
    except ConnectionError:
        print('请求初始页失败')
        return None
#分析初始页的Html，获得用户名，标题，视频。通过json解析
def parse_one_page(html):
    try:
        data = json.loads(html)['data']['res']
        for eve_data in data:
            if eve_data and 'rawurl' in eve_data.keys():
                user = eve_data['f']
                title = eve_data['t']
                rawurl = eve_data['rawurl']
                res = requests.get(rawurl,headers=headers)
                playurl = json.loads(res.text)['data']['playLink']
                res = requests.get(playurl,headers=headers)
                videourl = json.loads(res.text)['data']['url']
                data = {
                        'username':user,
                        'title':title,
                        'videourl':videourl
                        }
                download(title,videourl)
                save_to_mongo(data)
    except JSONDecodeError:
        print('解析网页失败')
        return None
#下载视频
def download(title,url):
    try:
        res = requests.get(url,headers=headers)
        if res.status_code == 200:
            with open(title+'.mp4','wb') as f:
                f.write(res.content)
    except Exception as e:
        pass
#存储到MongoDB数据库中
def save_to_mongo(data):
    if data and db['video'].insert(data):
        print('存储到MongoDB数据库成功',data)
    else:
        print('存储到数据库失败',data)

def main():
    page = 1
    while True:
        print('正在爬取第{}页'.format(page))
        url = 'http://pc.k.360kan.com/pc/list?n=10&p={}&f=json&ajax=1&uid=ad733bcf30b5a02a535956fbb7d07f4b&channel_id=2'.format(page)
        html = get_one_page(url)
        parse_one_page(html)
        page+=1

if __name__ == '__main__':
    main()
