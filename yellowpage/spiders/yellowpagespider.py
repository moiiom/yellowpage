# /usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import math
import urlparse
import datetime
import scrapy
import random
from scrapy.selector import Selector
from yellowpage.items import YellowpageItem
from yellowpage.constants import MyGlobals
from yellowpage.settings import DATA_BASE_PATH, USER_AGENT_LIST

reload(sys)
sys.setdefaultencoding('utf-8')


class YellowPageSpider(scrapy.Spider):
    name = "yellowpagespider"
    pagesize = 30
    allowed_domains = ["www.yellowpages.com"]
    base_url = "http://www.yellowpages.com"
    data_date = datetime.datetime.now().strftime('%Y%m%d')

    def __init__(self, *args, **kwargs):
        super(YellowPageSpider, self).__init__(*args, **kwargs)
        self.start_urls = self._get_start_urls()
        # self.start_urls = ["http://www.yellowpages.com/search?search_terms=food&geo_location_terms=Los+Angeles%2C+CA"]

    def parse(self, response):
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, sdch",
            "Accept-Language": "zh-CN,zh;q=0.8",
            "Cache-Control": "max-age=0",
            "Connection": "keep-alive",
            "Cookie": "vrid=94bea872-7686-4208-b3c8-ec7a7e78081b; express:sess=eyJka3MiOiJjY2NhMjRiNy1mYjA3LTQzZjYtYTkwNi03NDk4NmZlZjU2MmMifQ==; express:sess.sig=drocH_UPjFBqjTIUXV65ReQGmA4; optimizelyEndUserId=oeu1469965743181r0.768988560885191; s_nr=1469965748502; _sg_b_n=1470312066963; optimizelySegments=%7B%22355640769%22%3A%22gc%22%2C%22356170728%22%3A%22false%22%2C%22356260792%22%3A%22search%22%2C%22376690076%22%3A%22none%22%7D; optimizelyBuckets=%7B%7D; newb=ypu%3Adefault; zone=480; s_cc=true; s_prop70=August; s_prop71=32; s_sq=%5B%5BB%5D%5D; sorted=false; __utma=150871230.453214553.1469965746.1472207220.1472210157.5; __utmb=150871230.2.10.1472210157; __utmc=150871230; __utmz=150871230.1469965746.1.1.utmcsr=google|utmccn=(organic)|utmcmd=organic|utmctr=(not%20provided); OX_sd=2; OX_plg=pm; s_vi=[CS]v1|2BD1974105194B4B-60000605E00048B4[CE]; OX_nd=537073653_8_1472210340610; s_ppv=search_results%2C78%2C17%2C4317; bucket=ypu%3Areview_register_t1; bucketsrc=front; location=geo_term%3ALos%20Angeles%2C%20CA%7Clat%3A34.0522342%7Clng%3A-118.2436849%7Ccity%3ALos%20Angeles%7Cstate%3ACA%7Cdisplay_geo%3ALos%20Angeles%2C%20CA; search_terms=food; _sg_b_p=%2Fsearch; _sg_b_v=8%3B4530%3B1472211411",
            "Host": "www.yellowpages.com",
            "Referer": response.url,
            "User-Agent": random.choice(USER_AGENT_LIST)
        }

        print response.url
        exts = response.xpath('//div[@class="pagination"]/p/text()').extract()
        if len(exts) < 1:
            return
        total = int(exts[0].split(" ")[1])
        links = self._get_page_links(total, response.url)
        for _ in links:
            yield scrapy.Request(_, headers=headers, callback=self.detail_parse)

    def detail_parse(self, response):
        print response.url
        city = self._get_city_from_url(response.url)
        filename = "{0}/{1}/{2}/{3}.csv".format(DATA_BASE_PATH, self.data_date, self.allowed_domains[0], city)
        contexts = response.xpath('//div[@class="search-results organic"]/div').extract()

        for c in contexts:
            s = Selector(text=c)
            item = YellowpageItem()
            item['filename'] = filename
            item['name'] = [_.replace(",", " ") for _ in s.xpath('//a[@class="business-name"]//text()').extract()]
            item['address'] = [_.replace(",", " ") for _ in s.xpath('//p[@class="adr"]//text()').extract()]
            item['phone'] = [_.replace(",", " ") for _ in
                             s.xpath('///div[@class="phones phone primary"]/text()').extract()]
            item['categories'] = [_.replace(",", " ") for _ in s.xpath('///div[@class="categories"]//text()').extract()]
            imgs = s.xpath('//div[@class="media-thumbnail"]/a/img/@src').extract()
            item['img'] = imgs[0] if len(imgs) > 0 else ''

            yield item

    @staticmethod
    def _get_city_from_url(url):
        url = url.replace('%2C+', '').replace('+', '')
        query = urlparse.urlparse(url).query
        parm = dict([(k, v[0]) for k, v in urlparse.parse_qs(query).items()])
        return parm.get('geo_location_terms')

    def _get_start_urls(self):
        urls = list()
        for (state, cities) in MyGlobals.americian_cities.items():
            for city in cities:
                loc = city.replace(' ', '+') + "%2C+" + state
                for (top, sec) in MyGlobals.find_cflt.items():
                    if sec:
                        for cflt in sec:
                            urls.append(
                                "{0}/search?search_terms={1}&geo_location_terms={2}".format(self.base_url, cflt, loc))
                    else:
                        urls.append(
                            "{0}/search?search_terms={1}&geo_location_terms={2}".format(self.base_url, top, loc))
        return urls

    def _get_page_links(self, total, url):
        links = [url]
        pages = int(math.ceil(total / float(self.pagesize)))
        for i in range(1, pages + 1):
            if i > 1:
                links.append(url + "?page=" + str(i))
        return links
