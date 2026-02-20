import requests
from bs4 import BeautifulSoup
import feedgen.feed
from lxml.etree import CDATA
import datetime
import time
import random
import os,re,json
import pytz
from langdetect import detect, DetectorFactory

# 基础配置
# BASE_URL = "https://www.141jav.com/search/"
BASE_URL = "https://www.141jav.com/date/"
OUTPUT_FILE = "./xml/114jav-search-rss.xml"  # RSS 输出路径，需根据实际环境修改
PROXY = None  # 可选代理，例如 {"http": "http://proxy_ip:port", "https": "http://proxy_ip:port"}

# 复杂的 Headers，模拟真实浏览器
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36 Edg/133.0.0.0"
    # "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    # "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
    # "Accept-Encoding": "gzip, deflate, br, zstd",
    # # "cookie": "dom3ic8zudi28v8lr6fgphwffqoz0j6c=7759ccbb-54fb-480b-ba20-4e0713e056e2; sc_is_visitor_unique=rx8334861.1734661412.027C579DD2454F9D9C88A8DF2382B32E.70.70.70.70.69.64.46.29.15; cf_clearance=.tMGmAxlXe5bnGEfVyI7hBW7BwqWBCo3Aefs.r1BeL4-1740229481-1.2.1.1-4FVKq4Zw_VqWhL7Mfp.Blir8zXWkNRQolwGV8qIDVvSMMfZXIRA2Zx.gq4JoY7t9c2jVdMJddC3Zg.AwPhuOoTDEyyooewdmmx3vSUrH4Ssy1f12i5hNb4SFPTu4aTUq4M9cuSTIBRWPfNsbwKYSOW8Ae6h_FZ_KH_0jcUmJpJW5V96vdpjeS4fvIMkLQcHCItojfPwKwD7wXvsY_d5BPDLDkZCnBW0_Uiyb1Qc5z7bihlx6lzf5dRhaBhmbsrc7Dppv740630V_yoqXLXGm3wzBEYJMswG0O1zu3U5o.7s",
    # "Connection": "keep-alive",
    # "Upgrade-Insecure-Requests": "1",
    # "Sec-Fetch-Dest": "document",
    # "Sec-Fetch-Mode": "navigate",
    # "Sec-Fetch-Site": "same-origin",
    # "Sec-Fetch-User": "?1",
    # "Cache-Control": "max-age=0",
    # "Referer": "https://www.141jav.com/"  # 添加 Referer，可能需要动态调整
}

def fetch_page(search_text, page_num, retries=20):
    """抓取指定页面，支持重试机制"""
    url = f"{BASE_URL}{search_text}?page={page_num}"
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
        # if re.findall(r"FHDC",link):
        #    title = f"【FHDC】{title}"
        #    print(title)
        # else:
        #    continue
        image_url = row.find('div', class_='column').find('img')['onerror']
        # image_url = row.find('div', class_='column').find('img')
        image_url = re.findall(r"'(.*?)'", image_url)[0]
        # print(image_url)
        desc = row.find('p', class_='level has-text-grey-dark').text.strip()
        panels = row.find_all('a', class_='panel-block')
        # for panel in panels:
            # print(panel)
            # panel['href'] = f"https://www.141jav.com{panel['href']}"
            # panel = f"<li>{panel}</li>"
            # print(panel)

        # print(desc)
        pub_date = datetime.datetime.now().isoformat()

        items.append({
            "title": title,
            "link": link,
            'image_url': image_url,
            'turl': f"https://www.141jav.com{turl}",
            "description": desc,
            'panel': panels,
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
            response = requests.post(url, headers=headers, json=payload, proxies=PROXY, timeout=5)
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
    feed.title('114JAV Search Feed')
    feed.link(href='https://www.141jav.com/', rel='alternate')
    feed.description('114JAV SEARCH 数据 RSS 订阅')
    feed.language('en')
    ii = 0
 
    for item in items:
        # entry = feed.add_entry()
        # entry.title(item['title'])
        # entry.link(href=item['link'])
        if re.findall(r"FHDC",item['link']):
           entry = feed.add_entry()
           item['title'] = f"【FHDC】{item['title']}"
           entry.title(item['title'])
           ii = ii + 1
           print(f"<{ii}> {item['title']}")
        else:
           continue
        entry.link(href=item['link'])
        urls = ''
        for panel in item['panel']:
            url = f"https://www.141jav.com{panel['href']}"
            name = panel.text.strip()
            urls = urls + f"<li><a href='{url}'>{name}</a></li>"

        entry.description(CDATA(f"<a href='{item['turl']}'>{item['title']}</a><img src='{item['image_url']}'/><p>介绍：{item['description']}</p><p>{urls}</p>")),
        # re_translate = translate(item['description'], 1)
        # if not re_translate:
        #     translate_text = {'data': ''}
        # else:
        #     translate_text = json.loads(re_translate)

        # print(translate_text)
        # entry.description(CDATA(f"<img src='{item['image_url']}'/><p><a href='{item['turl']}'>介绍</a>：{item['description']}</p><p>译文：{translate_text['data']}</p><p>{urls}</p>")),
        entry.pubDate(datetime.datetime.now(pytz.UTC))

    # 保存到文件
    if ii == 0:
        return
    feed.rss_file(OUTPUT_FILE, pretty=True)
    print(f"RSS 文件已生成: {OUTPUT_FILE}")

def main():
    all_items = []
    page_num = 1
    day = 0
    # 获取当天的日期
    # today = datetime.now().strftime("%Y/%m/%d")
    if os.environ.get("SEARCH_DATE"):
        print("已获取并使用Env环境 category")
        s_text = os.environ["SEARCH_DATE"]
    else:
        print("未获取到正确的Category")
        return
    # s_text = '2025/08/08'
    # s_text = "SONE823"

    for i in range(8):
        while True:
            html = fetch_page(s_text, page_num)
            if not html:
                print(f"无法继续抓取，可能已到最后一页或被屏蔽")
                break
            
            items = parse_page(html)
            if not items:  # 如果页面没有数据，假设已到最后一页
                print(f"第 {page_num} 页无数据，停止抓取")
                break
            
            all_items.extend(items)
            print(f"已抓取 {s_text} 第 {page_num} 页，条目数: {len(items)}")
            page_num += 1
            # break
        
        s_text = (datetime.datetime.strptime(s_text, "%Y/%m/%d") + datetime.timedelta(days=1)).strftime("%Y/%m/%d")
        print(s_text)
        page_num = 1
    
    if all_items:
        generate_rss(all_items)
    else:
        print("未抓取到任何数据")

if __name__ == "__main__":
    main()