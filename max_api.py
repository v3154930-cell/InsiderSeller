import requests
import json
from config import MAX_BOT_TOKEN, MAX_API_URL

def send_message(chat_id, text, attachments=None, format="markdown"):
    url = f"{MAX_API_URL}/sendMessage"
    
    payload = {
        "chat_id": chat_id,
        "text": text,
        "format": format
    }
    
    if attachments:
        payload["attachments"] = attachments
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {MAX_BOT_TOKEN}"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Ошибка отправки: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Исключение: {e}")
        return None

def send_news_card(chat_id, news):
    importance_text = news.get("importance_emoji", "⚪ ИНФО")
    source_icon = news.get("source_icon", "📰")
    
    preview_text = f"""{importance_text} | {source_icon} {news['source_name']}

**{news['title']}**

{news['short_text']}

📎 _Нажмите кнопку ниже, чтобы прочитать полностью_"""
    
    attachments = []
    
    buttons = [
        {
            "type": "callback",
            "text": "📖 Читать полностью",
            "payload": f"full_{news['link']}"
        },
        {
            "type": "callback",
            "text": "❌ Скрыть",
            "payload": "hide"
        }
    ]
    
    attachments.append({
        "type": "inline_keyboard",
        "payload": {
            "buttons": [buttons]
        }
    })
    
    if news.get("image_url"):
        attachments.append({
            "type": "image",
            "payload": {"url": news["image_url"]}
        })
    
    return send_message(chat_id, preview_text, attachments, format="markdown")

def send_full_news(chat_id, news):
    importance_text = news.get("importance_emoji", "⚪ ИНФО")
    source_icon = news.get("source_icon", "📰")
    
    full_message = f"""{importance_text} | {source_icon} {news['source']}

**{news['title']}**

{news['full_text']}

📎 Источник: {news.get('link', '')}"""
    
    attachments = []
    
    attachments.append({
        "type": "inline_keyboard",
        "payload": {
            "buttons": [[{
                "type": "callback",
                "text": "✖️ Закрыть",
                "payload": "close"
            }]]
        }
    })
    
    if news.get("image_url"):
        attachments.append({
            "type": "image",
            "payload": {"url": news["image_url"]}
        })
    
    if news.get("video_url") and "youtube" in news["video_url"].lower():
        full_message += f"\n\n🎬 **Видео:** {news['video_url']}"
    
    return send_message(chat_id, full_message, attachments, format="markdown")

def delete_message(chat_id, message_id):
    url = f"{MAX_API_URL}/deleteMessage"
    
    payload = {"chat_id": chat_id, "message_id": message_id}
    headers = {"Authorization": f"Bearer {MAX_BOT_TOKEN}"}
    
    try:
        requests.post(url, json=payload, headers=headers, timeout=10)
    except Exception as e:
        print(f"❌ Ошибка удаления: {e}")

def answer_callback(callback_id, text=None):
    url = f"{MAX_API_URL}/answerCallback"
    
    payload = {"callback_id": callback_id}
    if text:
        payload["text"] = text
    
    headers = {"Authorization": f"Bearer {MAX_BOT_TOKEN}"}
    
    try:
        requests.post(url, json=payload, headers=headers, timeout=10)
    except Exception as e:
        print(f"❌ Ошибка answerCallback: {e}")

def get_updates(offset=None):
    url = f"{MAX_API_URL}/getUpdates"
    
    params = {"timeout": 30}
    if offset:
        params["offset"] = offset
    
    headers = {"Authorization": f"Bearer {MAX_BOT_TOKEN}"}
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=35)
        if response.status_code == 200:
            return response.json().get("result", [])
        return []
    except Exception as e:
        print(f"❌ Ошибка getUpdates: {e}")
        return []