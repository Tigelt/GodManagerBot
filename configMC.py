# Заголовки запроса
headers = {
    'Authorization': 'Bearer 218308c31b56c829b5e21290eee3c0507e82dcaa',
    'Content-Type': 'application/json'
}

BOT_TOKEN = "7261041875:AAE5Ez4yBH9RE85aPu4FdTHoZLAKgC6fAiQ"

# Telethon настройки
API_ID = 14739654
API_HASH = '98c13db08224026ed85682c5ed3e1834'

# Telegram настройки
FORUM_CHAT_ID = '@shisha_danang'  # ID чата форума для публикации ассортимента
FORUM_THREAD_ID = 555  # ID ветки форума

# Канал с описаниями вкусов
FLAVOR_CHANNEL = '@gogoelis'
FLAVOR_THREAD_ID = 831  # ID ветки с описаниями вкусов

# Пути к файлам
DATA_DIR = "requestsMC/data/shisha/"
SESSION_FILE = "aimanager.session"
IMAGES_DIR = "images/brands/"

# Актуальный ассортимент брендов
ACTUAL_BRANDS = [
    "Musthave",
    "Darkside", 
    "Blackburn",
    "DS shot",
    "Chabacco",
    "Satyr",
    "Xperience",
    "Trofimoff's",
    "Overdose",
    "Starline",
    "Энтузиаст"
]

# Маппинг брендов к изображениям
BRAND_IMAGES = {
    "Musthave": "musthave.jpg",
    "Darkside": "darkside.JPG", 
    "Blackburn": "blackburn.JPG",
    "DS shot": "ds_shot.JPG",
    "Chabacco": "chabacco.JPG",
    "Satyr": "satyr.jpg",
    "Darkside Xperience": "darkside_xperience.JPG",
    "Trofimoff's": "trofimoff.jpg",
    "Overdose": "overdose.JPG",
    "Starline": "starline.jpg",
    "Энтузиаст": "entuziast.jpg"
}


organization_href = "https://api.moysklad.ru/api/remap/1.2/entity/organization/633ef336-39e0-11f0-0a80-065e00264b61"

botManagerState_href = "https://api.moysklad.ru/api/remap/1.2/entity/customerorder/metadata/states/636b5ae8-39e0-11f0-0a80-065e00264b95"
dostavlenState_href = "https://api.moysklad.ru/api/remap/1.2/entity/customerorder/metadata/states/636b5c3d-39e0-11f0-0a80-065e00264b98"

IvanActual_href = "https://api.moysklad.ru/api/remap/1.2/entity/store/5b0a00a8-3b99-11f0-0a80-09fd0007829f"
IvanActual_id = "f46aa6b7-8ec1-11ef-0a80-00b7000fc6f3"

PROJECT_HREFS = {
    "наличные": "https://api.moysklad.ru/api/remap/1.2/entity/project/23438132-4056-11f0-0a80-1b67001ad0ff",
    "перевод": "https://api.moysklad.ru/api/remap/1.2/entity/project/d70007c5-4055-11f0-0a80-1aa00019e2d0",
    "иванкр": "https://api.moysklad.ru/api/remap/1.2/entity/project/db108373-4054-11f0-0a80-0c380019fcec"
}

order_data = {
        "organization": {
            "meta": {
                "href": organization_href, 
                "type": "organization",
                "mediaType": "application/json"
            }
        },
        "store": {
            "meta": {
            "href": IvanActual_href,
            "type": "store",
            "mediaType": "application/json"
            }
        },
        "reserve": True
}

ABBREVIATIONS = {
    "bb": "Blackburn",
    "cb": "Chabacco",
    "ds": "Darkside",
    "mh": "Musthave",
    "sl": "Starline",
    "od": "Overdose",
    "энт": "Энтузиаст",
    "sr": "Satyr"
}
