# coding: utf-8

import requests, re, math, random
from bs4 import BeautifulSoup
from progress.bar import ShadyBar

class Javbus():
	def __init__(self):
		self.url = 'https://www.javbus.in/page/{page}'
		self.total_page = 1
		self.avs_info = []
		self.final_data = []
		self.s = requests.Session()
		self.header = {
			'Referer': 'http://www.javbus.in',
    		'Cookie': 'existmag=all',
			'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36'
		}

	def get_html(self, page):
		url = self.url.replace('{page}', str(page))
		req = self.s.get(url, headers=self.header)
		return req.text

	def get_full_page(self):
		full_page = ''
		bar = ShadyBar('解析数据', max=self.total_page, suffix='%(percent)d%% [%(index)d/%(max)d]')
		for index in range(self.total_page):
			text = self.get_html(index+1)
			full_page += text
			bar.next()
		bar.finish()
		return full_page

	def get_all_fh(self):
		full_page = self.get_full_page()
		soup = BeautifulSoup(full_page, 'html.parser')
		divs = soup.find_all(class_='item')
		bar = ShadyBar('获取全站番号信息', max=len(divs), suffix='%(percent)d%% [%(index)d/%(max)d]')
		for item in divs:
			av = item.find(class_='photo-info')
			# 需要的数据
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
			self.avs_info.append(info)
			bar.next()
		bar.finish()
		return self.avs_info

	def get_magnet(self):
		bar = ShadyBar('获取磁力链接', max=len(self.avs_info), suffix='%(percent)d%% [%(index)d/%(max)d]')
		for item in self.avs_info:
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

			write_text = '标题：%s\n番号：%s\n发行时间：%s\nJav链接：%s\n磁力链接：%s\n\n' %(item['title'], item['fh'], item['time'], item['link'], item['magnet'])
			f = open('av.txt', 'a')
			f.write(write_text)
			f.close()
			self.final_data.append(item)
			bar.next()
		bar.finish()

if __name__ == '__main__':
	javbus = Javbus()
	javbus.get_all_fh()
	javbus.get_magnet()
