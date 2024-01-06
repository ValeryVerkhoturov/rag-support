from typing import Any

import scrapy
import os
import html2text

SITE_DOMAIN = os.getenv("SITE_DOMAIN")

class ContextSpider(scrapy.Spider):
    name = "context"
    allowed_domains = [SITE_DOMAIN]
    start_urls = [f'https://{SITE_DOMAIN}/']
    download_delay = 0.5

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self.h = html2text.HTML2Text()

    def parse(self, response):
        found_links = response.css('a::attr(href)').getall()
        text = self.h.handle(response.text)

        if 'text/html' in response.headers.get('Content-Type').decode():
            for href in found_links:
                if ((href.startswith('http') or href.startswith('/')) and
                        not (href.endswith(".xlsx") or href.endswith(".xls"))):
                    yield scrapy.Request(response.urljoin(href), self.parse)

        yield {
            'url': response.url,
            'text': text,
            'links': found_links
        }