import re
import scrapy
from scrapy.loader import ItemLoader
from ..items import KuntaraItem
from itemloaders.processors import TakeFirst
import requests
from scrapy import Selector
pattern = r'(\xa0)?'

url = "https://www.kuntarahoitus.fi/wp/wp-admin/admin-ajax.php"

payload="action=loadmorebutton&query=null&page={}"
headers = {
  'authority': 'www.kuntarahoitus.fi',
  'pragma': 'no-cache',
  'cache-control': 'no-cache',
  'sec-ch-ua': '"Chromium";v="88", "Google Chrome";v="88", ";Not A Brand";v="99"',
  'accept': '*/*',
  'x-requested-with': 'XMLHttpRequest',
  'sec-ch-ua-mobile': '?0',
  'user-agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.190 Safari/537.36',
  'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
  'origin': 'https://www.kuntarahoitus.fi',
  'sec-fetch-site': 'same-origin',
  'sec-fetch-mode': 'cors',
  'sec-fetch-dest': 'empty',
  'referer': 'https://www.kuntarahoitus.fi/ajankohtaista/',
  'accept-language': 'en-US,en;q=0.9',
  'cookie': 'Snoobi_test=1; Snoobisession_kuntarahoitus_fi=672885; Snoobi30minute_kuntarahoitus_fi=672885; SnoobiID=170014028; CookieInformationConsent=%7B%22website_uuid%22%3A%2281590061-38e3-432e-95a1-ceda64cb0514%22%2C%22timestamp%22%3A%222021-03-12T13%3A47%3A39.970Z%22%2C%22consent_url%22%3A%22https%3A%2F%2Fwww.kuntarahoitus.fi%2F%22%2C%22consent_website%22%3A%22Kuntarahoitus%22%2C%22consent_domain%22%3A%22www.kuntarahoitus.fi%22%2C%22user_uid%22%3A%2281d42dd9-2c9d-4a62-ba9c-9c76c4150d9a%22%2C%22consents_approved%22%3A%5B%22cookie_cat_necessary%22%2C%22cookie_cat_functional%22%2C%22cookie_cat_statistic%22%2C%22cookie_cat_marketing%22%2C%22cookie_cat_unclassified%22%5D%2C%22consents_denied%22%3A%5B%5D%2C%22user_agent%22%3A%22Mozilla%2F5.0%20%28Windows%20NT%206.1%3B%20Win64%3B%20x64%29%20AppleWebKit%2F537.36%20%28KHTML%2C%20like%20Gecko%29%20Chrome%2F88.0.4324.190%20Safari%2F537.36%22%7D; PHPSESSID=pd58t82nc2b3p4287s990m2sd3'
}


class KuntaraSpider(scrapy.Spider):
	name = 'kuntara'
	start_urls = ['https://www.kuntarahoitus.fi/ajankohtaista/']
	page = 0

	def parse(self, response):
		data = requests.request("POST", url, headers=headers, data=payload.format(self.page))
		container = data.text
		post_links = Selector(text=container).xpath('//a/@href').getall()
		yield from response.follow_all(post_links,self.parse_post)

		if response.xpath('//div[@class="liftup-date"]/time/text()'):
			self.page += 1
			yield response.follow(response.url, self.parse, dont_filter=True)

	def parse_post(self, response):
		date = response.xpath('//div[@class="liftup-date"]/time/text()').get().split(' ')[1]
		title = response.xpath('//h1/text()').get()
		content = response.xpath('//p[@class="excerpt"]//text()').getall() + response.xpath('//div[@class="entry-content"]//text()[not (ancestor::script)]').getall()
		content = [p.strip() for p in content if p.strip()]
		content = re.sub(pattern, "",' '.join(content))

		item = ItemLoader(item=KuntaraItem(), response=response)
		item.default_output_processor = TakeFirst()

		item.add_value('title', title)
		item.add_value('link', response.url)
		item.add_value('content', content)
		item.add_value('date', date)

		yield item.load_item()
