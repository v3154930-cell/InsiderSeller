import time
import threading
import os
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

from config import NEWS_CHECK_INTERVAL, CATEGORIES_LEVEL1, PLATFORMS_LEVEL2
from db import (
    init_db, get_user_subscriptions, save_user_subscriptions,
    update_category_subscription, update_platform_subscription,
    should_send_news_to_user, is_news_sent_to_user, mark_news_sent,
    get_full_news, get_all_users
)
from max_api import (
    send_message, send_news_card, send_full_news, answer_callback,
    get_updates, delete_message
)
from rss_parser import process_all_rss_feeds

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path == '/health':
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'OK')
        else:
            self.send_response(404)
        self.end_headers()
    
    def log_message(self, format, *args):
        pass

def run_health_server():
    port = int(os.environ.get('PORT', 8000))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

last_update_id = 0

def get_categories_keyboard(current_subs):
    buttons = []
    
    for cat in CATEGORIES_LEVEL1:
        is_selected = current_subs.get(cat["id"], False)
        status = "✅" if is_selected else "⬜"
        buttons.append([{
            "type": "callback",
            "text": f"{status} {cat['name']}",
            "payload": f"toggle_cat_{cat['id']}"
        }])
    
    buttons.append([{
        "type": "callback",
        "text": "✅ ДАЛЕЕ",
        "payload": "categories_done"
    }])
    
    return {
        "type": "inline_keyboard",
        "payload": {"buttons": buttons}
    }

def get_platforms_keyboard(current_subs):
    buttons = []
    row = []
    
    for plat in PLATFORMS_LEVEL2:
        is_selected = current_subs.get(plat["id"], False)
        status = "✅" if is_selected else "⬜"
        row.append({
            "type": "callback",
            "text": f"{status} {plat['icon']} {plat['name']}",
            "payload": f"toggle_plat_{plat['id']}"
        })
        if len(row) == 2:
            buttons.append(row)
            row = []
    
    if row:
        buttons.append(row)
    
    buttons.append([{
        "type": "callback",
        "text": "✅ СОХРАНИТЬ",
        "payload": "platforms_done"
    }])
    
    return {
        "type": "inline_keyboard",
        "payload": {"buttons": buttons}
    }

def get_settings_keyboard(current_subs):
    buttons = []
    
    for cat in CATEGORIES_LEVEL1:
        is_selected = current_subs.get(cat["id"], False)
        status = "✅" if is_selected else "❌"
        buttons.append([{
            "type": "callback",
            "text": f"{status} {cat['name']}",
            "payload": f"toggle_cat_{cat['id']}"
        }])
    
    if current_subs.get("marketplaces", False):
        buttons.append([{
            "type": "callback",
            "text": "📦 Детализация маркетплейсов",
            "payload": "show_platforms_settings"
        }])
    
    buttons.append([{
        "type": "callback",
        "text": "✅ ЗАКРЫТЬ",
        "payload": "close_settings"
    }])
    
    return {
        "type": "inline_keyboard",
        "payload": {"buttons": buttons}
    }

def get_platforms_settings_keyboard(current_subs):
    buttons = []
    row = []
    
    for plat in PLATFORMS_LEVEL2:
        is_selected = current_subs.get(plat["id"], False)
        status = "✅" if is_selected else "❌"
        row.append({
            "type": "callback",
            "text": f"{status} {plat['icon']} {plat['name']}",
            "payload": f"toggle_plat_{plat['id']}"
        })
        if len(row) == 2:
            buttons.append(row)
            row = []
    
    if row:
        buttons.append(row)
    
    buttons.append([{
        "type": "callback",
        "text": "◀️ НАЗАД",
        "payload": "back_to_settings"
    }])
    
    return {
        "type": "inline_keyboard",
        "payload": {"buttons": buttons}
    }

def send_start_message(chat_id):
    current_subs = get_user_subscriptions(chat_id)
    
    text = """🔥 **Добро пожаловать в Инсайдер Селер**

Ваш персональный агрегатор новостей для селлеров.

**Выберите, что вас интересует (можно несколько):**

✅ — подписано
⬜ — не подписано

👇 Нажмите на категорию, чтобы изменить подписку:"""
    
    attachments = [get_categories_keyboard(current_subs)]
    send_message(chat_id, text, attachments, format="markdown")

def send_platforms_selection(chat_id):
    current_subs = get_user_subscriptions(chat_id)
    
    text = """📦 **Выберите маркетплейсы (можно несколько):**

✅ — подписано
⬜ — не подписано

👇 Нажмите на платформу, чтобы изменить подписку:"""
    
    attachments = [get_platforms_keyboard(current_subs)]
    send_message(chat_id, text, attachments, format="markdown")

def send_subscription_confirmation(chat_id):
    subs = get_user_subscriptions(chat_id)
    
    selected_cats = []
    if subs.get("marketplaces"):
        selected_cats.append("📦 Маркетплейсы")
        platforms = []
        if subs.get("ozon"):
            platforms.append("🔵 Ozon")
        if subs.get("wb"):
            platforms.append("🟣 Wildberries")
        if subs.get("yandex"):
            platforms.append("🟡 Яндекс Маркет")
        if subs.get("avito"):
            platforms.append("🟠 Avito")
        if platforms:
            selected_cats.append(f"   → {', '.join(platforms)}")
    
    if subs.get("law"):
        selected_cats.append("⚖️ Законодательство")
    if subs.get("ecommerce"):
        selected_cats.append("📊 E-commerce и ритейл")
    if subs.get("blogs"):
        selected_cats.append("🎓 Блоги и лайфхаки интернет-торговли")
    
    if not selected_cats:
        text = "⚠️ Вы не выбрали ни одной категории. Новости приходить не будут.\n\nИспользуйте /settings, чтобы настроить подписки."
    else:
        text = f"""✅ **Настройки сохранены!**

Вы подписаны на:
{chr(10).join('• ' + s for s in selected_cats)}

📬 Новости с маркировкой важности будут приходить автоматически.

**Маркировка новостей:**
🔴 КРИТИЧНО — влияет на выручку
🟠 ВАЖНО — требует внимания
🟡 СРЕДНЕ — полезно знать
⚪ ИНФО — общая новость
⚖️ ЗАКОН — изменения в законодательстве

Изменить настройки: /settings"""
    
    send_message(chat_id, text, format="markdown")

def send_settings_message(chat_id):
    subs = get_user_subscriptions(chat_id)
    
    text = """⚙️ **Настройки подписок Инсайдер Селер**

✅ — подписано
❌ — не подписано

👇 Нажмите на категорию, чтобы изменить:"""
    
    attachments = [get_settings_keyboard(subs)]
    send_message(chat_id, text, attachments, format="markdown")

def send_platforms_settings(chat_id):
    subs = get_user_subscriptions(chat_id)
    
    text = """📦 **Настройка маркетплейсов**

✅ — подписано
❌ — не подписано

👇 Нажмите на платформу, чтобы изменить подписку:"""
    
    attachments = [get_platforms_settings_keyboard(subs)]
    send_message(chat_id, text, attachments, format="markdown")

def handle_callback(callback):
    global last_update_id
    
    user_id = callback.get("user", {}).get("id")
    callback_id = callback.get("id")
    payload = callback.get("payload", "")
    message = callback.get("message", {})
    message_id = message.get("id")
    
    if not user_id:
        return
    
    answer_callback(callback_id)
    
    if payload.startswith("toggle_cat_"):
        cat_id = payload.replace("toggle_cat_", "")
        subs = get_user_subscriptions(user_id)
        new_value = not subs.get(cat_id, False)
        update_category_subscription(user_id, cat_id, new_value)
        
        if cat_id == "marketplaces" and new_value:
            send_platforms_selection(user_id)
        else:
            message_text = message.get("text", "")
            if "settings" in message_text:
                send_settings_message(user_id)
            else:
                send_start_message(user_id)
    
    elif payload == "categories_done":
        send_subscription_confirmation(user_id)
    
    elif payload.startswith("toggle_plat_"):
        plat_id = payload.replace("toggle_plat_", "")
        subs = get_user_subscriptions(user_id)
        new_value = not subs.get(plat_id, False)
        update_platform_subscription(user_id, plat_id, new_value)
        
        message_text = message.get("text", "")
        if "settings" in message_text:
            send_platforms_settings(user_id)
        else:
            send_platforms_selection(user_id)
    
    elif payload == "platforms_done":
        send_subscription_confirmation(user_id)
    
    elif payload == "show_platforms_settings":
        send_platforms_settings(user_id)
    
    elif payload == "back_to_settings":
        send_settings_message(user_id)
    
    elif payload == "close_settings":
        if message_id:
            delete_message(user_id, message_id)
    
    elif payload.startswith("full_"):
        news_link = payload.replace("full_", "", 1)
        full_news = get_full_news(news_link)
        
        if full_news:
            full_news["link"] = news_link
            send_full_news(user_id, full_news)
        else:
            send_message(user_id, "❌ Не удалось загрузить полную версию новости.", format="markdown")
    
    elif payload == "hide":
        if message_id:
            delete_message(user_id, message_id)
    
    elif payload == "close":
        pass

def handle_message(message):
    user_id = message.get("from", {}).get("id")
    text = message.get("text", "").strip()
    
    if not user_id:
        return
    
    if text == "/start":
        send_start_message(user_id)
    elif text == "/settings":
        send_settings_message(user_id)
    else:
        send_message(user_id, "❓ Неизвестная команда. Используйте /start или /settings", format="markdown")

def send_news_to_subscribers():
    print("🔄 Проверка новых новостей...")
    
    news_list = process_all_rss_feeds()
    
    all_user_ids = get_all_users()
    
    for news in news_list:
        source_key = news.get("source_key")
        
        for user_id in all_user_ids:
            if should_send_news_to_user(user_id, source_key):
                if not is_news_sent_to_user(user_id, news["link"]):
                    send_news_card(user_id, news)
                    mark_news_sent(user_id, news["link"], news["title"], news["importance_level"])
                    print(f"  📤 Отправлено пользователю {user_id}: {news['title'][:30]}...")

def news_check_loop():
    while True:
        try:
            send_news_to_subscribers()
        except Exception as e:
            print(f"❌ Ошибка проверки новостей: {e}")
        time.sleep(NEWS_CHECK_INTERVAL)

def poll_updates():
    global last_update_id
    
    while True:
        try:
            updates = get_updates(offset=last_update_id + 1 if last_update_id else None)
            for update in updates:
                update_id = update.get("update_id")
                if update_id:
                    last_update_id = max(last_update_id, update_id)
                
                callback = update.get("callback_query")
                if callback:
                    handle_callback(callback)
                    continue
                
                message = update.get("message")
                if message:
                    handle_message(message)
        except Exception as e:
            print(f"❌ Ошибка poll_updates: {e}")
        time.sleep(1)

def main():
    print("=" * 50)
    print("🚀 ЗАПУСК БОТА ИНСАЙДЕР СЕЛЕР")
    print("=" * 50)
    
    init_db()
    
    news_thread = threading.Thread(target=news_check_loop, daemon=True)
    news_thread.start()
    print("✅ Поток проверки новостей запущен")
    
    poll_thread = threading.Thread(target=poll_updates, daemon=True)
    poll_thread.start()
    print("✅ Поток обработки сообщений запущен")
    
    health_thread = threading.Thread(target=run_health_server, daemon=True)
    health_thread.start()
    print(f"✅ Health server запущен на порту {os.environ.get('PORT', 8000)}")
    
    print("🤖 Бот работает...")
    print("=" * 50)
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Бот остановлен")

if __name__ == "__main__":
    main()