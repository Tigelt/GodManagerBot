"""
Обработчик запланированных задач
"""

import asyncio
import logging
from datetime import datetime, time
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

class ScheduleHandler:
    """Обработчик запланированных задач"""
    
    def __init__(self, bot, config: dict):
        self.bot = bot
        self.config = config
        self.is_running = False
    
    async def start_scheduler(self):
        """Запуск планировщика"""
        if self.is_running:
            logger.warning("Планировщик уже запущен")
            return
        
        self.is_running = True
        logger.info("🕐 Планировщик запущен")
        
        # Запускаем фоновую задачу для проверки времени
        asyncio.create_task(self._scheduler_loop())
    
    async def _scheduler_loop(self):
        """Основной цикл планировщика"""
        while self.is_running:
            try:
                # Получаем текущее время в UTC+7 (Дананг)
                from datetime import timedelta
                now_utc7 = datetime.utcnow() + timedelta(hours=7)
                current_time = now_utc7.time()
                
                # Проверяем задачи по расписанию
                await self._check_scheduled_tasks(current_time)
                
                # Ждём 60 секунд до следующей проверки
                await asyncio.sleep(60)
                
            except Exception as e:
                logger.error(f"❌ Ошибка в планировщике: {e}")
                await asyncio.sleep(60)
    
    async def _check_scheduled_tasks(self, current_time: time):
        """Проверка и выполнение задач по расписанию"""
        
        # 10:00 — Завтрак
        if current_time.hour == 10 and current_time.minute == 0:
            await self._send_message("🌞 Время завтракать, братулёчек.\nПодкинь топливо в систему, день сам себя не сделает.")
        
        # 11:00 — Начало работы
        if current_time.hour == 11 and current_time.minute == 0:
            await self._send_message("⚙️ Приступаем к делу, брат.\nПервый раунд на 5 часов 11-17.\nСоберись — игра началась, и у нас преимущество.")
        
        # 12:00 — Таблетка магния
        if current_time.hour == 12 and current_time.minute == 0:
            await self._send_message("💊 Магний, братишка.\nБезмолвное подкрепление силы.")
        
        # 15:45 — Предупреждение о скором обеде
        if current_time.hour == 15 and current_time.minute == 45:
            await self._send_message("🍴 Осталось 15 минут до обеда.\nПодводи итоги первой половины дня, закругляй начатое.")
        
        # 16:00 — Разминка и обед
        if current_time.hour == 16 and current_time.minute == 0:
            await self._send_message("🥗 Время размяться, подышать, пообедать.\nКороткий ритуал силы — и снова в строй.")
        
        # 17:00 — Возвращение к работе
        if current_time.hour == 17 and current_time.minute == 0:
            await self._send_message("🚀 Время вернуться в поток.\nВторой раунд на 4 часа 17-21.")
        
        # 20:45 — Предупреждение о скором ужине
        if current_time.hour == 20 and current_time.minute == 45:
            await self._send_message("⏰ Скоро ужин, братулёчек.\nЗаканчивай текущие дела, настройся на мягкое приземление.")
        
        # 21:00 — Ужин и вечерняя зарядка
        if current_time.hour == 21 and current_time.minute == 0:
            await self._send_message("🍛 Время ужина и лёгкой зарядки.\nТело — твой двигатель, держи его в тонусе.")
        
        # 22:45 — Конец смены приближается
        if current_time.hour == 22 and current_time.minute == 45:
            await self._send_message("🌙 Скоро конец дня.")
        
        # 23:00 — Конец смены
        if current_time.hour == 23 and current_time.minute == 0:
            await self._send_message("🧘 Финиш.\nВсё сделано. Отпусти день, как стрелу в небо.")
        
        # 00:00 — Завершение дня
        if current_time.hour == 0 and current_time.minute == 0:
            await self._send_message("🌌 Спасибо за этот красивый день.\nДоброй ночи, родной. Время отходить ко сну — завтра новая охота.")
    
    async def _send_message(self, text: str):
        """Отправка сообщения пользователю"""
        print(f"📨 [SCHEDULER] {text}")
        
        try:
            await self.bot.send_message(
                chat_id=self.config['admin_chat_id'],
                text=text
            )
            logger.info(f"✅ Сообщение отправлено: {text[:50]}...")
        except Exception as e:
            logger.error(f"❌ Ошибка отправки сообщения: {e}")
            print(f"❌ Ошибка отправки сообщения: {e}")
    
    def stop_scheduler(self):
        """Остановка планировщика"""
        self.is_running = False
        logger.info("🛑 Планировщик остановлен")

