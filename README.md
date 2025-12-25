# GodManagerBot v2.0

Telegram бот для управления заказами кальянного табака с интеграцией Мой Склад и Google Sheets.

## Возможности

- 📦 Обработка заказов Shisha и Gastro
- 🔄 Синхронизация с Мой Склад
- 📊 Запись в Google Sheets
- 🏪 Управление ассортиментом
- 📱 Telegram интерфейс

## Структура проекта

```
GMB2/
├── core/                    # Ядро приложения
│   ├── bot.py              # Главный класс бота
│   └── handlers/           # Обработчики событий
│       ├── order_handler.py      # Обработка заказов
│       └── assortment_handler.py # Управление ассортиментом
├── services/               # Внешние сервисы
│   ├── moy_sklad.py        # API Мой Склад
│   ├── telegram_client.py  # Telegram клиент (Telethon)
│   ├── google_sheets.py    # Google Sheets API
│   └── notifications.py    # Уведомления
├── utils/                  # Утилиты
│   ├── parsers.py          # Парсинг сообщений
│   ├── validators.py       # Валидация данных
│   └── auth.py             # Аутентификация
├── data/                   # Данные
│   ├── FinalAssortment.json    # Финальный ассортимент
│   ├── ItemNameHref.json       # Связи товаров
│   ├── AgentNameHref.json      # Связи агентов
│   └── FlavorDescriptions.json # Описания вкусов
└── config/                 # Конфигурация
    └── settings.py         # Настройки
```

## Установка

1. Клонируйте репозиторий
2. Установите зависимости: `pip install -r requirements.txt`
3. Cкачать в корневую папку файл `.env`
4. Запустите: `python main.py`

## Docker
Для запуска через докер нужно использовать короткие команды из файла commands.sh
./commands.sh rebuild

```bash
docker-compose up -d
```

## Команды бота

- `/start` - Запуск бота
- `/assortment` - Публикация ассортимента
- `/updateassortment` - Обновление ассортимента
- `/baseflavor` - Обновление описаний вкусов
- `/inventory` - Показать инвентарь

## Лицензия

MIT 