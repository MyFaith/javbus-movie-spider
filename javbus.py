# coding: utf-8

import requests, re, math, random, time
from bs4 import BeautifulSoup
from pymongo import MongoClient
import threading
import queue
import argparse

mongo = MongoClient(host='192.168.199.217')
db = mongo.javbus
mutex = threading.Lock()

class Javbus(threading.Thread):
    def __init__(self, page_queue):
        self.page_queue = page_queue
        self.avs_queue = queue.Queue()
        self.s = requests.Session()
        self.header = {
            'Referer': 'http://www.javbus.com',
            'Cookie': 'existmag=all',
            'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36'
        }
        threading.Thread.__init__(self)

    def run(self):
        while not self.page_queue.empty():
            url = 'http://www.javbus.com/page/%s' %self.page_queue.get()
            self.get_datas(url)
            time.sleep(2)

    def get_datas(self, url):
        avs = []
        # 获取某一页的HTML
        print('正在获取 %s 的数据...' %url)
        html = self.s.get(url, headers=self.header).text
        soup = BeautifulSoup(html, 'html.parser')
        divs = soup.find_all(class_='item')
        # 获取基本数据
        for item in divs:
            av = item.find(class_='photo-info')
            title = item.find(class_='photo-frame').img['title']
            fh = av.span.date.next
            time = av.span.date.next.next.next.next
            link = 'https://www.javbus.in/%s' %fh
            info = {
                'title': title,
                'fh': fh,
                'time': time,
                'link': link
            }
            avs.append(info)
        # 获取磁链
        for item in avs:
            url = item['link']
            html = self.s.get(url, headers=self.header).text
            # 由于磁力链接是ajax方式获取，所以获取数据，构成ajax链接
            gid = re.search(r'var gid = (\d*?);', html).group(1)
            lang = 'zh'
            uc = re.search(r'var uc = (\d*?);', html).group(1)
            img = re.search(r"var img = '(.*?)';", html).group(1)
            floor = math.floor(random.random() * 1e3 + 1)
            # 请求数据
            ajax_url = 'https://www.javbus.in/ajax/uncledatoolsbyajax.php?gid=%s&lang=%s&img=%s&uc=%s&floor=%s' %(gid, lang, img, uc, floor)
            ajax_result = self.s.get(ajax_url, headers=self.header)
            soup = BeautifulSoup(ajax_result.text, 'html.parser')
            try:
                magnet = soup.find('td').a['href']
            except Exception:
                magnet = 'unissued'
            # append
            item['img'] = img
            item['magnet'] = magnet
            print('[取到数据]\n标题：%s\n番号：%s\n时间：%s\n图片：%s\n链接：%s\n磁链：%s\n' %(item['title'], item['fh'], item['time'], item['img'], item['link'], item['magnet']))
            self.avs_queue.put(item)
        # 存储数据
        mutex.acquire()
        while not self.avs_queue.empty():
            item = self.avs_queue.get()
            print('[写入数据库]%s' %item['title'])
            db.avs.insert({
                'title': item['title'],
                'fh': item['fh'],
                'time': item['time'],
                'image': item['img'],
                'link': item['link'],
                'magnet': item['magnet']
            })
        mutex.release()

def main(max_page, thread_num):
    # 构建页面队列
    page_queue = queue.Queue()
    for page in range(1, max_page):
        page_queue.put(page)
    
    threads = []
    # 开启4个线程
    for i in range(thread_num):
        javbus = Javbus(page_queue)
        javbus.setDaemon(True)
        javbus.start()
        threads.append(javbus)
    # 判断
    # while True:
    #     for i in threads:
    #         if not i.isAlive():
    #             break
    #     time.sleep(1)
    for i in threads:
        i.join()

if __name__ == '__main__':
    parser = argparse.ArgumentParser('javbus')
    parser.add_argument('-page', dest='page', default=5, type=int, help='获取的页数')
    parser.add_argument('-thread', dest='thread', default=4, type=int, help='启动的线程数')
    args = parser.parse_args()
    main(args.page, args.thread)