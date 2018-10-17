from gevent import monkey; monkey.patch_all()
import gevent
import requests
import time
import queue
from pyquery import PyQuery
from mongoengine import *
import re
import math
import random

connect('javbus', host='myfaith.io', port=27017)

class Avs(Document):
    title = StringField()
    fh = StringField()
    time = StringField()
    image = StringField()
    link = StringField()
    magnet = StringField()

def fetch(pageQueue):
    avs_queue = queue.Queue()
    s = requests.Session()
    header = {
        'Referer': 'http://www.javbus.com',
        'Cookie': 'existmag=all',
        'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36'
    }
    # Run
    while not pageQueue.empty():
        avs = []
        avs_queue = queue.Queue()
        url = pageQueue.get()
        print('正在获取 %s 的数据...' %url)
        html = s.get(url, headers=header).text
        pq = PyQuery(html)
        # Get FH
        for item in pq('.item').items():
            av = pq(item).find('.photo-info span')
            title = pq(item).find('.photo-frame img').attr('title')
            fh = pq(av).find('date').eq(0).text()
            time = pq(av).find('date').eq(1).text()
            link = 'https://www.javbus.com/%s' %fh
            info = {
                'title': title,
                'fh': fh,
                'time': time,
                'link': link
            }
            avs.append(info)
        # Get Magnet
        for item in avs:
            url = item['link']
            html = s.get(url, headers=header).text
            # 由于磁力链接是ajax方式获取，所以获取数据，构成ajax链接
            gid = re.search(r'var gid = (\d*?);', html).group(1)
            lang = 'zh'
            uc = re.search(r'var uc = (\d*?);', html).group(1)
            img = re.search(r"var img = '(.*?)';", html).group(1)
            floor = math.floor(random.random() * 1e3 + 1)
            # 请求数据
            ajax_url = 'https://www.javbus.com/ajax/uncledatoolsbyajax.php?gid=%s&lang=%s&img=%s&uc=%s&floor=%s' %(gid, lang, img, uc, floor)
            ajax_result = s.get(ajax_url, headers=header)
            pq = PyQuery(ajax_result.text)
            try:
                magnet = pq('td a').attr('href')
            except Exception:
                magnet = 'unissued'
            # append
            item['img'] = img
            item['magnet'] = magnet
            print('[取到数据]\n标题：%s\n番号：%s\n时间：%s\n图片：%s\n链接：%s\n磁链：%s\n' %(item['title'], item['fh'], item['time'], item['img'], item['link'], item['magnet']))
            avs_queue.put(item)
        # Sve Data
        while not avs_queue.empty():
            item = avs_queue.get()
            # 判断是获取什么类型
            av = Avs(
                title=item['title'],
                fh=item['fh'],
                time=item['time'],
                image=item['img'],
                link=item['link'],
                magnet=item['magnet']
            )
            av.save()
            print('[写入数据库]%s' %item['title'])

def main(maxPage=10):
    pageQueue = queue.Queue()
    url = 'http://www.javbus.com/page/{pageNum}'
    # url = 'http://www.javbus.com/uncensored/page/{pageNum}'
    for page in range(1, maxPage):
        pageQueue.put(url.format(pageNum=str(page)))
    gevent.joinall([gevent.spawn(fetch, pageQueue) for i in range(10)])

if __name__ == '__main__':
    main()
