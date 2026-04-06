# Токен бота из MAX Business
MAX_BOT_TOKEN = "ВАШ_ТОКЕН_СЮДА"

# Интервал проверки RSS в секундах (600 = 10 минут, 7200 = 2 часа)
NEWS_CHECK_INTERVAL = 600

# MAX API URL
MAX_API_URL = "https://api.max.ru/bot/v1"

# ============================================================
# УРОВНИ ВАЖНОСТИ ДЛЯ МАРКИРОВКИ
# ============================================================

IMPORTANCE_LEVELS = {
    "critical": {"emoji": "🔴", "text": "КРИТИЧНО"},
    "important": {"emoji": "🟠", "text": "ВАЖНО"},
    "medium": {"emoji": "🟡", "text": "СРЕДНЕ"},
    "info": {"emoji": "⚪", "text": "ИНФО"},
    "law": {"emoji": "⚖️", "text": "ЗАКОН"}
}

# Ключевые слова для определения критичности (влияет на выручку)
CRITICAL_KEYWORDS = [
    "комиссия", "повышение комиссии", "изменение комиссии", "комисс",
    "штраф", "блокировка", "заморозка", "прибыль", "убыток",
    "тариф", "логистика", "рост тарифов", "подорожание"
]

# Ключевые слова для законов
LAW_KEYWORDS = [
    "закон", "289-ФЗ", "фас", "постановление", "регулирование",
    "платформенная экономика", "федеральный закон", "налог", "маркировка"
]

# Ключевые слова для важного
IMPORTANT_KEYWORDS = [
    "важно", "внимание", "обязательно", "изменение", "новое правило"
]

# Ключевые слова для среднего (аналитика)
MEDIUM_KEYWORDS = [
    "аналитика", "прогноз", "тренд", "статистика", "исследование"
]

# ============================================================
# RSS-ИСТОЧНИКИ
# ============================================================

RSS_FEEDS = {
    # Маркетплейсы
    "ozon": {
        "urls": [
            "https://www.retail.ru/rss/tag/ozon/",
            "https://vc.ru/rss/tag/ozon",
            "https://e-pepper.ru/news/rss.xml"
        ],
        "name": "Ozon",
        "icon": "🔵",
        "category": "marketplaces",
        "topic_field": "ozon"
    },
    "wb": {
        "urls": [
            "https://www.retail.ru/rss/tag/wildberries/",
            "https://vc.ru/rss/tag/wildberries"
        ],
        "name": "Wildberries",
        "icon": "🟣",
        "category": "marketplaces",
        "topic_field": "wb"
    },
    "yandex": {
        "urls": [
            "https://www.retail.ru/rss/tag/yandeks-market/"
        ],
        "name": "Яндекс Маркет",
        "icon": "🟡",
        "category": "marketplaces",
        "topic_field": "yandex"
    },
    "avito": {
        "urls": [
            "https://www.retail.ru/rss/tag/avito/"
        ],
        "name": "Avito",
        "icon": "🟠",
        "category": "marketplaces",
        "topic_field": "avito"
    },
    # Законодательство
    "law": {
        "urls": [],
        "name": "Законодательство",
        "icon": "⚖️",
        "category": "law",
        "topic_field": "law"
    },
    # E-commerce и ритейл
    "ecommerce": {
        "urls": [
            "https://www.retail.ru/rss/rubric/e-commerce/",
            "https://rb.ru/feeds/tag/ecommerce/",
            "https://www.comnews.ru/rss",
            "https://oborot.ru/rss/"
        ],
        "name": "E-commerce и ритейл",
        "icon": "📊",
        "category": "ecommerce",
        "topic_field": "ecommerce"
    },
    # Блоги и лайфхаки
    "blogs": {
        "urls": [
            "https://vc.ru/rss/tag/seLLLering",
            "https://vc.ru/rss/tag/marketplace"
        ],
        "name": "Блоги и лайфхаки интернет-торговли",
        "icon": "🎓",
        "category": "blogs",
        "topic_field": "blogs"
    }
}

# ============================================================
# КАТЕГОРИИ УРОВНЯ 1
# ============================================================

CATEGORIES_LEVEL1 = [
    {
        "id": "marketplaces",
        "name": "📦 Маркетплейсы",
        "description": "Ozon, WB, Яндекс Маркет, Avito",
        "icon": "📦",
        "children": ["ozon", "wb", "yandex", "avito"]
    },
    {
        "id": "law",
        "name": "⚖️ Законодательство",
        "description": "E-commerce, налоги, ФАС, 289-ФЗ",
        "icon": "⚖️",
        "children": ["law"]
    },
    {
        "id": "ecommerce",
        "name": "📊 E-commerce и ритейл",
        "description": "Тренды, аналитика, прогнозы",
        "icon": "📊",
        "children": ["ecommerce"]
    },
    {
        "id": "blogs",
        "name": "🎓 Блоги и лайфхаки интернет-торговли",
        "description": "VC.ru, телеграм-каналы селлеров",
        "icon": "🎓",
        "children": ["blogs"]
    }
]

# ============================================================
# ПЛАТФОРМЫ УРОВНЯ 2 (для маркетплейсов)
# ============================================================

PLATFORMS_LEVEL2 = [
    {"id": "ozon", "name": "Ozon", "icon": "🔵"},
    {"id": "wb", "name": "Wildberries", "icon": "🟣"},
    {"id": "yandex", "name": "Яндекс Маркет", "icon": "🟡"},
    {"id": "avito", "name": "Avito", "icon": "🟠"}
]