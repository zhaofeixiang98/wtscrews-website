#!/usr/bin/env python3
"""
生成站点地图 sitemap.xml
每天早上2点自动执行
"""
import os
from pathlib import Path
from datetime import datetime
from xml.etree import ElementTree as ET
from xml.dom import minidom

BASE_URL = os.environ.get("BASE_URL", "https://wtscrews.com/pags")
ROOT_DIR = Path(__file__).resolve().parents[1]
PAGS_DIR = os.environ.get("PAGS_DIR", str(ROOT_DIR / "pags"))
OUTPUT_FILE = os.environ.get("OUTPUT_FILE", str(ROOT_DIR / "sitemap.xml"))

# 语言列表
LANGUAGES = ['en', 'zh', 'ja', 'ko', 'fr', 'de', 'es', 'ar', 'id']

# 主页面配置
MAIN_PAGES = {
    '': {'priority': '1.0', 'changefreq': 'weekly'},           # index.html
    'index.html': {'priority': '1.0', 'changefreq': 'weekly'},
    'products.html': {'priority': '0.9', 'changefreq': 'weekly'},
    'news.html': {'priority': '0.8', 'changefreq': 'weekly'},
    'about.html': {'priority': '0.6', 'changefreq': 'monthly'},
    'contact.html': {'priority': '0.7', 'changefreq': 'monthly'},
    'privacy-policy.html': {'priority': '0.4', 'changefreq': 'monthly'},
    'success.html': {'priority': '0.5', 'changefreq': 'monthly'},
    '404.html': {'priority': '0.1', 'changefreq': 'yearly'},
}

def get_lastmod(file_path):
    """获取文件最后修改时间"""
    try:
        timestamp = os.path.getmtime(file_path)
        return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
    except:
        return datetime.now().strftime('%Y-%m-%d')

def generate_sitemap():
    """生成sitemap.xml"""
    urlset = ET.Element('urlset')
    urlset.set('xmlns', 'http://www.sitemaps.org/schemas/sitemap/0.9')
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    for lang in LANGUAGES:
        lang_dir = os.path.join(PAGS_DIR, lang)
        if not os.path.exists(lang_dir):
            continue
        
        # 主目录页面
        for page, config in MAIN_PAGES.items():
            if page == '':
                loc = f"{BASE_URL}/{lang}/"
            else:
                loc = f"{BASE_URL}/{lang}/{page}"
            
            url = ET.SubElement(urlset, 'url')
            ET.SubElement(url, 'loc').text = loc
            ET.SubElement(url, 'lastmod').text = today
            ET.SubElement(url, 'changefreq').text = config['changefreq']
            ET.SubElement(url, 'priority').text = config['priority']
        
        # 产品页面
        products_dir = os.path.join(lang_dir, 'products')
        if os.path.exists(products_dir):
            for filename in sorted(os.listdir(products_dir)):
                if filename.endswith('.html'):
                    file_path = os.path.join(products_dir, filename)
                    loc = f"{BASE_URL}/{lang}/products/{filename}"
                    
                    url = ET.SubElement(urlset, 'url')
                    ET.SubElement(url, 'loc').text = loc
                    ET.SubElement(url, 'lastmod').text = get_lastmod(file_path)
                    ET.SubElement(url, 'changefreq').text = 'monthly'
                    ET.SubElement(url, 'priority').text = '0.7'
        
        # 新闻页面
        news_dir = os.path.join(lang_dir, 'news')
        if os.path.exists(news_dir):
            for filename in sorted(os.listdir(news_dir)):
                if filename.endswith('.html'):
                    file_path = os.path.join(news_dir, filename)
                    loc = f"{BASE_URL}/{lang}/news/{filename}"
                    
                    url = ET.SubElement(urlset, 'url')
                    ET.SubElement(url, 'loc').text = loc
                    ET.SubElement(url, 'lastmod').text = get_lastmod(file_path)
                    ET.SubElement(url, 'changefreq').text = 'weekly'
                    ET.SubElement(url, 'priority').text = '0.6'
    
    # 保存文件
    xml_str = minidom.parseString(ET.tostring(urlset, encoding='unicode')).toprettyxml(indent="  ")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(xml_str)
    
    print(f"Sitemap generated: {OUTPUT_FILE}")

if __name__ == '__main__':
    generate_sitemap()