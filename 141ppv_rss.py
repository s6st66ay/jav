import requests
from bs4 import BeautifulSoup
import feedgen.feed
from lxml.etree import CDATA
from datetime import datetime,timedelta
import time
import random
import os,sys,re,json
import pytz
from langdetect import detect, DetectorFactory

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from sendNotify import send  # 导入青龙面板的通知模块
# from notify import send

# 基础配置
BASE_URL = "https://www.141ppv.com/date/"
OUTPUT_FILE = "./xml/141ppv-torrent-rss.xml"  # RSS 输出路径，需根据实际环境修改
PROXY = None  # 可选代理，例如 {"http": "http://proxy_ip:port", "https": "http://proxy_ip:port"}

# 复杂的 Headers，模拟真实浏览器
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36 Edg/133.0.0.0"
    # "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7" # 添加 Referer，可能需要动态调整 
}

def fetch_page(today, page_num, retries=100):
    """抓取指定页面，支持重试机制"""
    url = f"{BASE_URL}{today}?page={page_num}"
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=HEADERS, proxies=PROXY, timeout=10)
            response.encoding = 'UTF-8'
            response.raise_for_status()
            time.sleep(random.uniform(1, 10))  # 随机延迟，模拟人类行为
            return response.text
        except requests.RequestException as e:
            print(f"抓取页面 {url} 失败 (尝试 {attempt+1}/{retries}): {e}")
            if attempt < retries - 1:
                time.sleep(random.uniform(2, 10))  # 重试前稍长延迟
            else:
                return None

def parse_page(html):
    """解析页面内容，提取标题、链接和描述等"""
    soup = BeautifulSoup(html, 'html.parser')
    torrent_list = soup.find_all('div', class_='card mb-3')
    items = []
    
    # 假设每个条目在 <div class="torrent-item"> 中，需根据实际网页结构调整
    # for row in soup.select('card mb-3'):  # 选择器需根据实际网页调整
    for row in torrent_list:  # 选择器需根据实际网页调整
        # print(row)
        # title = torrent.select_one('.title').get_text(strip=True) if torrent.select_one('.title') else "无标题"
        # link = torrent.select_one('a')['href'] if torrent.select_one('a') else "#"
        # description = torrent.select_one('.description').get_text(strip=True) if torrent.select_one('.description') else "无描述"
        # pub_date = datetime.now().isoformat()  # 当前时间作为发布日期
        # 提取单元格中的数据
        title = row.find('h5', class_='title is-4 is-spaced').text.strip()
        turl = row.find('h5', class_='title is-4 is-spaced').find('a')['href']
        # print(title)
        link = row.find('div', class_='card-content is-flex').find('a', class_='button is-primary is-fullwidth')['href']
        # print(link)
        image_url = row.find('div', class_='column').find('img')['onerror']
        image_url = re.findall(r"'(.*?)'", image_url)[0]
        # print(image_url)
        desc = row.find('p', class_='level has-text-grey-dark').text.strip()
        # print(desc)
        pub_date = datetime.now().isoformat()

        items.append({
            "title": title,
            "link": link,
            'image_url': image_url,
            'turl': f"https://www.141ppv.com{turl}",
            "description": desc,
            "pub_date": pub_date
        })
    return items

def translate(text, retries=3):
    if not text:
        return None
    headers = {'Content-Type': 'application/json'}
    url = "http://192.168.2.1:1188/translate?token=sony420"
    language = detect(text)
    print(text,"|",language)
    # if language != 'ja':  language = 'en'
    payload = {
        "source_lang": 'AUTO',
        "target_lang": "ZH",
        "text": text
    }
    for attempt in range(retries):
        try:
            response = requests.post(url, headers=headers, json=payload, proxies=PROXY, timeout=10)
            response.raise_for_status()
            time.sleep(random.uniform(1, 10))  # 随机延迟，模拟人类行为
            return response.text
        except requests.RequestException as e:
            print(f"翻译内容 {url} 失败 (尝试 {attempt+1}/{retries}): {e}")
            if attempt < retries - 1:
                time.sleep(random.uniform(2, 10))  # 重试前稍长延迟
            else:
                return None

def generate_rss(items):
    """生成 RSS 文件"""
    feed = feedgen.feed.FeedGenerator()
    feed.title('141PPV Torrent Feed')
    feed.link(href='https://www.141ppv.com/', rel='alternate')
    feed.description('每日更新的 141PPV_TORRENT 数据 RSS 订阅')
    feed.language('en')

    items = sorted(items, key=lambda x: x["title"])
    for item in items:
        entry = feed.add_entry()
        if re.search(r"(無修正|無・中出|無・顔出|【無|未修正)", item['description']):
            entry.title(item['title'] + " 【無修正】")
        else:
            entry.title(item['title'])
        
        entry.link(href=item['link'])
        # re_translate = translate(item['description'], 5)
        # if not re_translate:
        #     translate_text = {'data': ''}
        # else:
        #     translate_text = json.loads(re_translate)
        # entry.description(CDATA(f"<img src='{item['image_url']}'/><p><a href='{item['turl']}'>介绍</a>：{item['description']}</p><p>译文：{translate_text['data']}</p>"))
        entry.description(CDATA(f"<img src='{item['image_url']}'/><p><a href='{item['turl']}'>介绍</a>：{item['description']}</p>"))
        entry.pubDate(datetime.now(pytz.UTC))

    # 保存到文件
    feed.rss_file(OUTPUT_FILE, pretty=True)
    print(f"RSS 文件已生成: {OUTPUT_FILE}")

def main():
    all_items = []
    page_num = 1
    mess_s = []
    # 获取当天的日期
    now = datetime.now()
    # 判断是否在下午4点（16:00）前
    if now.hour < 6:
        target_date = now.date() - timedelta(days=1)  # 显示昨天
    else:
        target_date = now.date()  # 显示今天
    today = target_date.strftime("%Y/%m/%d")
    # today = '2026/02/08'

    titel = f"获取 www.141ppv.com {today} 数据"    

    while True:
        html = fetch_page(today, page_num)
        if not html:
            print(f"无法继续抓取，可能已到最后一页或被屏蔽")
            mess_s.append(f"无法继续抓取，可能已到最后一页或被屏蔽")
            break
        
        items = parse_page(html)
        if not items:  # 如果页面没有数据，假设已到最后一页
            print(f"第 {page_num} 页无数据，停止抓取")
            mess_s.append(f"第 {page_num} 页无数据，停止抓取")
            break
        
        all_items.extend(items)
        print(f"已抓取第 {page_num} 页，条目数: {len(items)}")
        mess_s.append(f"已抓取第 {page_num} 页，条目数: {len(items)}")
        page_num += 1
    
    if all_items:
        generate_rss(all_items)
    else:
        print("未抓取到任何数据")
        mess_s.append("未抓取到任何数据")

    content = '\n'.join(map(str, mess_s))
    send(titel, content)

if __name__ == "__main__":
    main()