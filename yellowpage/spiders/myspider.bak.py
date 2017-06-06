# /usr/bin/env python
# -*- coding: utf-8 -*-
import os
import re
import sys
import errno
import math
import scrapy
import codecs
from scrapy.selector import Selector
from yellowpagespider.items import YellowpageItem

reload(sys)
sys.setdefaultencoding('utf-8')


class YellowPageSpider(scrapy.Spider):
    name = "yellowpagespider"
    pagesize = 30

    def __init__(self, term=None, location=None, *args, **kwargs):
        super(YellowPageSpider, self).__init__(*args, **kwargs)

        self.term = "+".join(self._preprocess(term))
        self.location = "+".join(self._preprocess(location))
        self.allowed_domains = ["www.yellowpages.com"]

        url = "http://www.yellowpages.com"
        conditions = []
        if term:
            conditions.append("search_terms={0}".format(self.term))
        if location:
            conditions.append("geo_location_terms={0}".format(self.location))
        self.start_urls = [url + "/search?" + '&'.join(conditions)] if len(conditions) > 0 else []

    def _preprocess(self, parameter):
        match = re.compile(r'\w+').findall(parameter)
        if match:
            return match
        else:
            return []

    def _create_links(self, total):
        links = []
        pages = int(math.ceil(total / float(self.pagesize)))
        for i in range(1, pages):
            links.append(self.start_urls[0] + "?page=" + str(i))
        return links

    def parse(self, response):
        print response.url
        exts = response.xpath('//div[@class="pagination"]/p/text()').extract()
        if len(exts) < 1:
            return
        total = int(exts[0].split(" ")[1])
        links = self._create_links(total)
        for _ in links:
            yield scrapy.Request(_, callback=self.detail_parse)

    def detail_parse(self, response):
        contexts = response.xpath('//div[@class="search-results organic"]/div').extract()

        filename = "data/{0}/{1}.csv".format(self.location.lower(), self.term.lower())
        if filename:
            if not os.path.exists(os.path.dirname(filename)):
                try:
                    os.makedirs(os.path.dirname(filename))
                except OSError as exc:
                    if exc.errno != errno.EEXIST:
                        raise
            with codecs.open(filename, 'w', 'utf-8') as f:
                f.write("name, address, phone, categories\n")

        for c in contexts:
            s = Selector(text=c)
            item = YellowpageItem()
            item['name'] = [_.replace(",", " ") for _ in s.xpath('//a[@class="business-name"]//text()').extract()]
            item['address'] = [_.replace(",", " ") for _ in s.xpath('//p[@class="adr"]//text()').extract()]
            item['phone'] = [_.replace(",", " ") for _ in s.xpath('///div[@class="phones phone primary"]/text()').extract()]
            item['categories'] = [_.replace(",", " ") for _ in s.xpath('///div[@class="categories"]//text()').extract()]

            with codecs.open(filename, 'a', 'utf-8') as f:
                f.write(
                    "{0},{1},{2},{3}\n".format(' '.join(item['name']), ' '.join(item['address']),
                                               ' '.join(item['phone']),
                                               ' '.join(item['categories'])))
            yield item
