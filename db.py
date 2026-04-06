import sqlite3
from datetime import datetime

DB_NAME = "users.db"

def init_db():
    """Создаёт таблицы при первом запуске"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            subscribe_marketplaces INTEGER DEFAULT 0,
            subscribe_law INTEGER DEFAULT 0,
            subscribe_ecommerce INTEGER DEFAULT 0,
            subscribe_blogs INTEGER DEFAULT 0,
            subscribe_ozon INTEGER DEFAULT 0,
            subscribe_wb INTEGER DEFAULT 0,
            subscribe_yandex INTEGER DEFAULT 0,
            subscribe_avito INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sent_news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            news_link TEXT,
            news_title TEXT,
            importance_level TEXT,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS full_news (
            news_link TEXT PRIMARY KEY,
            title TEXT,
            full_text TEXT,
            description TEXT,
            image_url TEXT,
            video_url TEXT,
            source TEXT,
            source_icon TEXT,
            importance_level TEXT,
            importance_emoji TEXT,
            published_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ База данных инициализирована")

def get_user_subscriptions(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            subscribe_marketplaces, subscribe_law, subscribe_ecommerce, subscribe_blogs,
            subscribe_ozon, subscribe_wb, subscribe_yandex, subscribe_avito
        FROM users WHERE user_id = ?
    ''', (user_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            "marketplaces": bool(row[0]),
            "law": bool(row[1]),
            "ecommerce": bool(row[2]),
            "blogs": bool(row[3]),
            "ozon": bool(row[4]),
            "wb": bool(row[5]),
            "yandex": bool(row[6]),
            "avito": bool(row[7])
        }
    
    return {
        "marketplaces": False, "law": False, "ecommerce": False, "blogs": False,
        "ozon": False, "wb": False, "yandex": False, "avito": False
    }

def save_user_subscriptions(user_id, subscriptions):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO users (
            user_id, 
            subscribe_marketplaces, subscribe_law, subscribe_ecommerce, subscribe_blogs,
            subscribe_ozon, subscribe_wb, subscribe_yandex, subscribe_avito
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            subscribe_marketplaces = excluded.subscribe_marketplaces,
            subscribe_law = excluded.subscribe_law,
            subscribe_ecommerce = excluded.subscribe_ecommerce,
            subscribe_blogs = excluded.subscribe_blogs,
            subscribe_ozon = excluded.subscribe_ozon,
            subscribe_wb = excluded.subscribe_wb,
            subscribe_yandex = excluded.subscribe_yandex,
            subscribe_avito = excluded.subscribe_avito
    ''', (
        user_id,
        1 if subscriptions.get("marketplaces") else 0,
        1 if subscriptions.get("law") else 0,
        1 if subscriptions.get("ecommerce") else 0,
        1 if subscriptions.get("blogs") else 0,
        1 if subscriptions.get("ozon") else 0,
        1 if subscriptions.get("wb") else 0,
        1 if subscriptions.get("yandex") else 0,
        1 if subscriptions.get("avito") else 0
    ))
    
    conn.commit()
    conn.close()

def update_category_subscription(user_id, category_id, value):
    subs = get_user_subscriptions(user_id)
    subs[category_id] = value
    save_user_subscriptions(user_id, subs)

def update_platform_subscription(user_id, platform_id, value):
    subs = get_user_subscriptions(user_id)
    subs[platform_id] = value
    save_user_subscriptions(user_id, subs)

def get_users_by_topic(topic_field):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute(f'SELECT user_id FROM users WHERE {topic_field} = 1', ())
    rows = cursor.fetchall()
    
    conn.close()
    return [row[0] for row in rows]

def get_users_by_category(category):
    field_map = {
        "marketplaces": "subscribe_marketplaces",
        "law": "subscribe_law",
        "ecommerce": "subscribe_ecommerce",
        "blogs": "subscribe_blogs"
    }
    
    if category not in field_map:
        return []
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute(f'SELECT user_id FROM users WHERE {field_map[category]} = 1', ())
    rows = cursor.fetchall()
    
    conn.close()
    return [row[0] for row in rows]

def get_all_users():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('SELECT user_id FROM users', ())
    rows = cursor.fetchall()
    
    conn.close()
    return [row[0] for row in rows]

def should_send_news_to_user(user_id, source_key):
    subs = get_user_subscriptions(user_id)
    
    mapping = {
        "ozon": "ozon",
        "wb": "wb",
        "yandex": "yandex",
        "avito": "avito",
        "law": "law",
        "ecommerce": "ecommerce",
        "blogs": "blogs"
    }
    
    if source_key not in mapping:
        return False
    
    field = mapping[source_key]
    
    if source_key in ["ozon", "wb", "yandex", "avito"]:
        return subs.get("marketplaces", False) or subs.get(field, False)
    
    return subs.get(field, False)

def is_news_sent_to_user(user_id, news_link):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('SELECT 1 FROM sent_news WHERE user_id = ? AND news_link = ?', (user_id, news_link))
    exists = cursor.fetchone() is not None
    
    conn.close()
    return exists

def mark_news_sent(user_id, news_link, news_title, importance_level):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO sent_news (user_id, news_link, news_title, importance_level)
        VALUES (?, ?, ?, ?)
    ''', (user_id, news_link, news_title, importance_level))
    
    conn.commit()
    conn.close()

def save_full_news(news_link, title, full_text, description, image_url, video_url, 
                   source, source_icon, importance_level, importance_emoji):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT OR REPLACE INTO full_news (
            news_link, title, full_text, description, image_url, video_url, 
            source, source_icon, importance_level, importance_emoji
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (news_link, title, full_text, description, image_url, video_url, 
          source, source_icon, importance_level, importance_emoji))
    
    conn.commit()
    conn.close()

def get_full_news(news_link):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT title, full_text, description, image_url, video_url, source, source_icon, 
               importance_level, importance_emoji
        FROM full_news WHERE news_link = ?
    ''', (news_link,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            "title": row[0],
            "full_text": row[1],
            "description": row[2],
            "image_url": row[3],
            "video_url": row[4],
            "source": row[5],
            "source_icon": row[6],
            "importance_level": row[7],
            "importance_emoji": row[8]
        }
    return None