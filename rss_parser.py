import fastfeedparser
import requests
from bs4 import BeautifulSoup
import re
import hashlib
from datetime import datetime
from config import (
    RSS_FEEDS, CRITICAL_KEYWORDS, LAW_KEYWORDS, 
    IMPORTANT_KEYWORDS, MEDIUM_KEYWORDS, IMPORTANCE_LEVELS
)
from db import save_full_news, get_full_news

def fetch_rss_feed(url):
    try:
        feed = fastfeedparser.parse(url)
        return feed
    except Exception as e:
        print(f"❌ Ошибка загрузки RSS {url}: {e}")
        return None

def analyze_importance(title, description, source):
    text = f"{title} {description}".lower()
    
    if any(keyword in text for keyword in LAW_KEYWORDS):
        return {
            "level": "law",
            "emoji": IMPORTANCE_LEVELS["law"]["emoji"],
            "text": IMPORTANCE_LEVELS["law"]["text"]
        }
    
    if any(keyword in text for keyword in CRITICAL_KEYWORDS):
        if "комисс" in text and ("вырос" in text or "повыс" in text or "рост" in text):
            return {
                "level": "critical",
                "emoji": IMPORTANCE_LEVELS["critical"]["emoji"],
                "text": IMPORTANCE_LEVELS["critical"]["text"]
            }
        if "логистик" in text and ("поднял" in text or "вырос" in text or "тариф" in text):
            return {
                "level": "critical",
                "emoji": IMPORTANCE_LEVELS["critical"]["emoji"],
                "text": IMPORTANCE_LEVELS["critical"]["text"]
            }
        return {
            "level": "critical",
            "emoji": IMPORTANCE_LEVELS["critical"]["emoji"],
            "text": IMPORTANCE_LEVELS["critical"]["text"]
        }
    
    if any(keyword in text for keyword in IMPORTANT_KEYWORDS):
        return {
            "level": "important",
            "emoji": IMPORTANCE_LEVELS["important"]["emoji"],
            "text": IMPORTANCE_LEVELS["important"]["text"]
        }
    
    if any(keyword in text for keyword in MEDIUM_KEYWORDS):
        return {
            "level": "medium",
            "emoji": IMPORTANCE_LEVELS["medium"]["emoji"],
            "text": IMPORTANCE_LEVELS["medium"]["text"]
        }
    
    return {
        "level": "info",
        "emoji": IMPORTANCE_LEVELS["info"]["emoji"],
        "text": IMPORTANCE_LEVELS["info"]["text"]
    }

def extract_image_from_entry(entry, link):
    if hasattr(entry, 'media_content') and entry.media_content:
        for media in entry.media_content:
            if media.get('type', '').startswith('image/'):
                return media.get('url')
    
    if hasattr(entry, 'enclosures') and entry.enclosures:
        for enc in entry.enclosures:
            if enc.get('type', '').startswith('image/'):
                return enc.get('url')
    
    try:
        response = requests.get(link, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            og_image = soup.find('meta', property='og:image')
            if og_image and og_image.get('content'):
                return og_image.get('content')
            
            first_img = soup.find('img')
            if first_img and first_img.get('src'):
                img_src = first_img.get('src')
                if img_src.startswith('http'):
                    return img_src
                elif img_src.startswith('/'):
                    from urllib.parse import urljoin
                    return urljoin(link, img_src)
    except Exception as e:
        print(f"⚠️ Ошибка извлечения изображения: {e}")
    
    return None

def extract_video_from_entry(entry, link):
    if hasattr(entry, 'enclosures') and entry.enclosures:
        for enc in entry.enclosures:
            if enc.get('type', '').startswith('video/'):
                return enc.get('url')
    
    content_text = ""
    if hasattr(entry, 'content') and entry.content:
        content_text = str(entry.content)
    if hasattr(entry, 'summary') and entry.summary:
        content_text += str(entry.summary)
    
    youtube_patterns = [
        r'(?:youtube\.com\/watch\?v=)([\w-]+)',
        r'(?:youtu\.be\/)([\w-]+)',
        r'(?:youtube\.com\/embed\/)([\w-]+)'
    ]
    
    for pattern in youtube_patterns:
        match = re.search(pattern, content_text, re.IGNORECASE)
        if match:
            video_id = match.group(1)
            return f"https://www.youtube.com/watch?v={video_id}"
    
    return None

def shorten_text(text, limit=200):
    if not text:
        return ""
    
    clean_text = re.sub(r'<[^>]+>', '', text)
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    
    if len(clean_text) <= limit:
        return clean_text
    
    shortened = clean_text[:limit]
    last_space = shortened.rfind(' ')
    if last_space > 0:
        shortened = shortened[:last_space]
    
    return shortened + "..."

def extract_full_text(link):
    try:
        response = requests.get(link, timeout=15, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            content_selectors = [
                'article', '.article-content', '.post-content', '.news-content',
                '.content', '.entry-content', '.full-story', '.text'
            ]
            
            content_text = ""
            for selector in content_selectors:
                elements = soup.select(selector)
                if elements:
                    for elem in elements:
                        content_text += elem.get_text(separator='\n', strip=True) + "\n"
                    break
            
            if content_text:
                content_text = re.sub(r'\n\s*\n', '\n\n', content_text)
                return content_text[:4000]
            
            body = soup.find('body')
            if body:
                content_text = body.get_text(separator='\n', strip=True)
                return content_text[:4000]
    
    except Exception as e:
        print(f"⚠️ Ошибка извлечения полного текста: {e}")
    
    return None

def get_entry_value(entry, *keys, default=''):
    for key in keys:
        val = getattr(entry, key, None)
        if val:
            return val
    return default

def process_rss_feed_for_source(source_key, source_config):
    all_news = []
    
    for url in source_config["urls"]:
        print(f"  📡 Парсинг: {url}")
        feed = fetch_rss_feed(url)
        
        if not feed or not hasattr(feed, 'entries'):
            continue
        
        for entry in feed.entries[:10]:
            link = get_entry_value(entry, 'link')
            if not link:
                continue
            
            title = get_entry_value(entry, 'title', default='Без заголовка')
            description = get_entry_value(entry, 'description', 'summary', 'content', default='')
            
            existing = get_full_news(link)
            if existing:
                all_news.append({
                    "id": hashlib.md5(link.encode()).hexdigest(),
                    "link": link,
                    "title": title,
                    "description": description,
                    "short_text": shorten_text(description),
                    "full_text": existing["full_text"],
                    "image_url": existing["image_url"],
                    "video_url": existing["video_url"],
                    "source_key": source_key,
                    "source_name": source_config["name"],
                    "source_icon": source_config["icon"],
                    "importance_level": existing["importance_level"],
                    "importance_emoji": existing["importance_emoji"]
                })
                continue
            
            importance = analyze_importance(title, description, source_config["name"])
            
            image_url = extract_image_from_entry(entry, link)
            video_url = extract_video_from_entry(entry, link)
            
            full_text = extract_full_text(link)
            if not full_text:
                full_text = description
            
            save_full_news(
                news_link=link,
                title=title,
                full_text=full_text,
                description=description,
                image_url=image_url,
                video_url=video_url,
                source=source_config["name"],
                source_icon=source_config["icon"],
                importance_level=importance["level"],
                importance_emoji=f"{importance['emoji']} {importance['text']}"
            )
            
            all_news.append({
                "id": hashlib.md5(link.encode()).hexdigest(),
                "link": link,
                "title": title,
                "description": description,
                "short_text": shorten_text(description),
                "full_text": full_text,
                "image_url": image_url,
                "video_url": video_url,
                "source_key": source_key,
                "source_name": source_config["name"],
                "source_icon": source_config["icon"],
                "importance_level": importance["level"],
                "importance_emoji": f"{importance['emoji']} {importance['text']}"
            })
    
    return all_news

def process_all_rss_feeds():
    all_news = []
    
    for source_key, source_config in RSS_FEEDS.items():
        if not source_config["urls"]:
            continue
        
        print(f"🔄 Проверка: {source_config['name']}")
        news = process_rss_feed_for_source(source_key, source_config)
        all_news.extend(news)
        print(f"  ✅ Найдено {len(news)} новостей")
    
    return all_news