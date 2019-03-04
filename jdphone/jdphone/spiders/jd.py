# -*- coding: utf-8 -*-
import scrapy
import time
import json
from ..items import JdphoneItem
from scrapy.selector import Selector


class JdSpider(scrapy.Spider):
    name = 'jd'
    allowed_domains = ['jd.com']
    start_urls = ['http://jd.com/']
    keyword = "手机"
    page = 1
    url = "https://search.jd.com/Search?" \
          "keyword=%s&enc=utf-8&wq=%s&cid2=653&qrst=1&rt=1&stop=1&vt=2&cid3=655&page=%s&s=59&click=0"
    next_url = "https://search.jd.com/s_new.php?keyword=%s&enc=utf-8&qrst=1&rt=1&stop=1&vt=2&suggest=1.his.0.0&cid2=653&cid3=655&page=%s&s=28&scrolling=y&log_id=1551336158.44375&tpl=3_M&show_items=%s"
    comments_count_url = "https://club.jd.com/comment/productCommentSummaries.action?referenceIds=%s&callback=jQuery4359560&_=%s"

    def start_requests(self):
        yield scrapy.Request(self.url % (self.keyword, self.keyword, self.page), callback=self.parse)

    def parse(self, response):
        """
        爬取每页前三十个商品，数据直接展示在原网页中的
        :param response: 
        :return: 
        """
        ids = []
        for li in Selector(response).xpath('//li[@class="gl-item"]'):
            item = JdphoneItem()
            title = li.xpath('div/div[@class="p-img"]/a/@title').extract()
            price = li.xpath('div/div[@class="p-price"]//i/text()').extract()
            url = li.xpath('div/div[@class="p-img"]/a/@href').extract()

            id = li.xpath('@data-pid').extract()
            ids.append(''.join(id))

            item['id'] = ''.join(id)
            item['title'] = ''.join(title)
            item['price'] = ''.join(price)
            item['url'] = ''.join(url)

            if item['url'].startswith('//'):
                item['url'] = 'https:' + item['url']
            elif not item['url'].startswith('https:'):
                item['info'] = None
                yield item
                continue
            yield scrapy.Request(item['url'], callback=self.info_parse, meta={'item': item})
        headers = {
            'referer': response.url
        }
        self.page += 1
        yield scrapy.Request(self.next_url % (self.keyword, self.page, ','.join(ids)),
                             callback=self.next_parse, headers=headers)

    def next_parse(self, response):
        # 解析后30个条目
        ids = []
        for li in Selector(response).xpath('//*[@id="J_goodsList"]/ul/li'):
            item = JdphoneItem()
            title = li.xpath('div/div[@class="p-img"]/a/@title').extract()
            price = li.xpath('div/div[@class="p-price"]//i/text()').extract()
            url = li.xpath('div/div[@class="p-img"]/a/@href').extract()

            id = li.xpath('@data-pid').extract()
            ids.append(id)
            item['id'] = ''.join(id)
            item['title'] = ''.join(title)
            item['price'] = ''.join(price)
            item['url'] = ''.join(url)

            if item['url'].startswith('//'):
                item['url'] = 'https:' + item['url']
            elif not item['url'].startswith('https:'):
                item['info'] = None
                yield item
                continue

            yield scrapy.Request(item['url'], callback=self.info_parse, meta={"item": item})
        if self.page < 200:
            self.page += 1
            yield scrapy.Request(self.url % (self.keyword, self.keyword, self.page), callback=self.parse)

    def info_parse(self, response):
        # 解析详情页
        item = response.meta['item']
        item['info'] = {}
        type = Selector(response).xpath('//div[@class="inner border"]/div[@class="head"]/a/text()').extract_first()
        name = Selector(response).xpath('//div[@class="item ellipsis"]/text()').extract_first()
        item['info']['type'] = ''.join(type)
        item['info']['name'] = ''.join(name)
        for div in Selector(response).xpath('//div[@class="Ptable"]/div'):
            h3 = ''.join(div.xpath('h3/text()').extract())
            if h3 == '':
                h3 = '未知'
            dt = div.xpath('dl/dl/dt/text()').extract()
            dd = div.xpath('dl/dl/dd/text()').extract()
            item['info'][h3] = {}
            for t, d in zip(dt, dd):
                item['info'][h3][t.strip().replace('\n', '')] = d.strip().replace('\n', '')
        yield scrapy.Request(self.comments_count_url % (item['id'], int(time.time() * 1000)),
                             callback=self.comments_parse, meta={'item': item})

    def comments_parse(self, response):
        # 抓取评论数量
        item = response.meta['item']
        # 返回的评论数量是json数据
        response_dict = json.loads(response.text.split('(')[1].split(')')[0])
        item['comments_count'] = response_dict['CommentsCount'][0]['CommentCount']
        return item
