import re
import time
import os

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from lxml import etree
import requests
import pandas as pd

from dotenv import load_dotenv

load_dotenv()


def get_cookie():
    _cookies = {}
    cookies_str = os.environ.get('COOKIES')
    for i in cookies_str.split(';'):
        name, value = i.split('=', 1)
        _cookies[name] = value
    return _cookies


def get_data(dom=None, cookies=None):
    names = dom.xpath('//div[@class="comment-item "]//span[@class="comment-info"]/a/text()')
    ratings = dom.xpath('//div[@class="comment-item "]//span[@class="comment-info"]/span[2]/@class')
    times = dom.xpath('//div[@class="comment-item "]//span[@class="comment-info"]/span[@class="comment-time "]/@title')
    messages = dom.xpath('//div[@class="comment-item "]/div[@class="comment"]//span[@class="short"]/text()')
    user_url = dom.xpath('//div[@class="comment-item "]//span[@class="comment-info"]/a/@href')
    votes = dom.xpath('//div[@class="comment-item "]//div[@class="comment"]//span[contains(@class, "votes")]/text()')

    cities = []
    load_times = []
    for i in user_url:
        res = requests.get(i, headers=headers, cookies=cookies)
        dom = etree.HTML(res.text, etree.HTMLParser(encoding='utf-8'))
        address = dom.xpath('//div[@class="basic-info"]//div[@class="user-info"]/a/text()')
        load_time = dom.xpath('//div[@class="basic-info"]//div[@class="user-info"]/div[@class="pl"]/text()')
        cities.append(address)
        load_times.append(load_time)
        print(f'这是第{i}个{address}, {load_time}')
        time.sleep(1)

    ratings = ['' if 'rating' not in i else int(re.findall(r'\d{2}', i)[0]) for i in ratings]
    load_times = ['' if i == [] else i[1].strip()[:-2] for i in load_times]
    cities = ['' if i == [] else i[0] for i in cities]

    print(f'ratings: {ratings}\nload_times: {load_times}\ncities: {cities}')

    data = pd.DataFrame({
        '用户名': names,
        '居住城市': cities,
        '加入时间': load_times,
        '评分': ratings,
        '发表时间': times,
        '短评正文': messages,
        '赞同数量': votes
    })

    return data


cookies = get_cookie()
print(cookies)
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.101.76 Safari/537.36'
}
options = Options()
options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
# options.add_argument("--headless")
service = Service("/usr/local/bin/chromedriver")  # 替换为实际 chromedriver 路径
driver = webdriver.Chrome(service=service, options=options)

url = "https://movie.douban.com/subject/26266893/comments?start=60&limit=20&status=P&sort=new_score"
driver.get(url)

all_data = pd.DataFrame()
wait = WebDriverWait(driver, 10)
count = 0
max = 5
while True:
    count += 1
    if count >= max:
        break
    wait.until(EC.element_to_be_clickable(
        (By.CSS_SELECTOR, '#comments > div:nth-child(20) > div.comment > h3 > span.comment-info > a')))
    page_source = driver.page_source
    dom = etree.HTML(driver.page_source)
    data = get_data(dom, cookies)
    all_data = pd.concat([all_data, data], axis=0)
    data.to_csv('douban.csv', index=False, mode='a', encoding='utf-8')
    print(f'这是第{count}页')
    if not driver.find_element(By.CSS_SELECTOR, '#paginator > a.next'):
        break
    confirm_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '#paginator > a.next')))
    confirm_btn.click()

all_data.to_csv('douban.csv', index=False, encoding='utf-8')
driver.quit()
