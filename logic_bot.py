import telebot
from telebot import types as bot_types
from telebot.apihelper import ApiTelegramException
import os
import time
import re
import logging

# Настройка логов, чтобы видеть действия бота в консоли
logger = logging.getLogger(__name__)

class BotLogic:
    def __init__(self, token):
        # Инициализация бота через токен
        self.bot = telebot.TeleBot(token)

    def repair_html(self, html):
        """
        Умная функция исправления HTML.
        Telegram очень капризный: если ссылка @username, он её удалит.
        Если теги пересекаются <b><a></b></a>, он выдаст ошибку 400.
        """
        # 1. Исправляем юзернеймы в ссылках на полные ссылки t.me
        html = re.sub(r'href=["\']@([^"\']+?)["\']', r'href="https://t.me/\1"', html)
        
        # 2. Базовая проверка закрытия тегов (чтобы не было Unmatched end tag)
        for tag in ['b', 'i', 'u', 's', 'a', 'code']:
            open_count = len(re.findall(f"<{tag}[^>]*>", html))
            close_count = len(re.findall(f"</{tag}>", html))
            # Если тег открыт больше раз, чем закрыт - дописываем закрывающие в конец
            if open_count > close_count:
                html += f"</{tag}>" * (open_count - close_count)
        return html

    def send_post(self, channel_id, username, text, media_path, btns):
        logger.info(f"[BotLogic] Готовлю публикацию для канала {channel_id}")
        
        # Пауза, чтобы Telegram успел прогрузить новый юзернейм в базе
        time.sleep(3)
        
        # Исправляем HTML перед отправкой
        text = self.repair_html(text)
        
        # Создаем кнопки
        markup = bot_types.InlineKeyboardMarkup()
        for t, u in btns:
            if t and u:
                u = u.strip()
                # Если в кнопке указали @username, делаем из него ссылку
                if not u.startswith("http"): u = f"https://t.me/{u.replace('@','')}"
                markup.add(bot_types.InlineKeyboardButton(t, url=u))

        msg = None
        try:
            # Если есть фото или видео
            if media_path and os.path.exists(media_path):
                logger.info(f"[BotLogic] Отправка медиа: {media_path}")
                with open(media_path, 'rb') as f:
                    # Проверка расширения (видео или фото)
                    if media_path.lower().endswith(('.mp4', '.mov')):
                        msg = self.bot.send_video(channel_id, f, caption=text, reply_markup=markup, parse_mode="HTML")
                    else:
                        msg = self.bot.send_photo(channel_id, f, caption=text, reply_markup=markup, parse_mode="HTML")
            else:
                # Если только текст
                logger.info("[BotLogic] Отправка текстового сообщения")
                msg = self.bot.send_message(channel_id, text, reply_markup=markup, parse_mode="HTML")
        
        except ApiTelegramException as e:
            logger.error(f"❌ Критическая ошибка Telegram API: {e}")
            # Выдаем подробное описание ошибки для пользователя в интерфейс
            raise Exception(f"Telegram отказал в публикации: {e.description}")

        # ГЕНЕРАЦИЯ ССЫЛКИ НА ПОСТ
        # Telegram всегда дает ID 3 первому посту, если системные удалены.
        if username:
            post_link = f"https://t.me/{username}/{msg.message_id}"
        else:
            # Если юзернейм не задан, создаем приватную ссылку через ID чата
            chat_id_str = str(channel_id).replace("-100", "")
            post_link = f"https://t.me/c/{chat_id_str}/{msg.message_id}"
            
        logger.info(f"[BotLogic] Успех! Ссылка: {post_link}")
        return post_link