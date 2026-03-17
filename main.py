import asyncio
import os
import json
import base64
import logging
import traceback
from tkinter import Tk, filedialog
import eel

from logic_telethon import TelethonLogic
from logic_bot import BotLogic

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

eel.init('web')
os.makedirs("temp", exist_ok=True)

@eel.expose
def get_config():
    if os.path.exists("config.json"):
        with open("config.json", "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

@eel.expose
def save_config(data):
    with open("config.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    return "Конфиг сохранен"

@eel.expose
def save_file_from_b64(b64_data, filename):
    file_path = os.path.join("temp", filename)
    header, encoded = b64_data.split(",", 1)
    with open(file_path, "wb") as f:
        f.write(base64.b64decode(encoded))
    return file_path

@eel.expose
def browse_file():
    root = Tk()
    root.attributes('-topmost', True)
    root.withdraw()
    file_path = filedialog.askopenfilename()
    root.destroy()
    return file_path

def progress_callback(percent, text):
    eel.update_progress(percent, text)()

@eel.expose
def run_process(api_data, channel_data, post_data):
    try:
        logger.info("=== СТАРТ СОЗДАНИЯ КАНАЛА И ПОСТА ===")
        
        logger.info("[Шаг 1] Проверка папки sessions...")
        if not os.path.exists("sessions"):
            os.makedirs("sessions")
            
        sessions = [f.split('.')[0] for f in os.listdir("sessions") if f.endswith(".session")]
        if not sessions:
            logger.error("Нет файлов .session в папке sessions!")
            return {"status": "error", "msg": "Нет сессий в папке sessions!"}

        session_name = sessions[0]
        logger.info(f"[Шаг 2] Найдена сессия: {session_name}.session. Создаю TelethonLogic...")
        
        logic_t = TelethonLogic(int(api_data['api_id']), api_data['api_hash'])
        
        logger.info("[Шаг 3] Запускаю Telethon (асинхронный луп)...")
        # Используем безопасный луп, чтобы избежать дедлоков в Eel
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            username, channel_id = loop.run_until_complete(
                logic_t.create_and_setup_channel(
                    session_name,
                    channel_data['name'], channel_data['bio'], channel_data['user'],
                    channel_data['avatar_path'], api_data['bot_user'],
                    channel_data['reactions'],
                    progress_callback
                )
            )
        finally:
            loop.close()

        logger.info(f"[Шаг 4] Telethon завершил работу. Канал ID: {channel_id}, User: {username}")
        progress_callback(95, "Отправка поста через бота...")
        
        logger.info("[Шаг 5] Инициализация BotLogic...")
        logic_b = BotLogic(api_data['bot_token'])
        
        post_link = logic_b.send_post(
            channel_id, username,
            post_data['text'], post_data['media_path'], post_data['btns']
        )

        progress_callback(98, "Сохраняю ссылку...")
        logger.info("[Шаг 6] Сохранение ссылки в файл и буфер...")
        try:
            with open("saved_links.txt", "a", encoding="utf-8") as f:
                f.write(f"Канал: {channel_data['name']} | Ссылка: {post_link}\n")
            
            root = Tk()
            root.withdraw()
            root.clipboard_clear()
            root.clipboard_append(post_link)
            root.update()
            root.destroy()
            logger.info("Ссылка успешно скопирована в буфер обмена.")
        except Exception as ex:
            logger.error(f"Ошибка буфера обмена: {ex}")

        progress_callback(100, "Готово!")
        logger.info("=== ПРОЦЕСС УСПЕШНО ЗАВЕРШЕН ===")
        return {"status": "success", "link": post_link}
        
    except Exception as e:
        error_trace = traceback.format_exc()
        logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА В MAIN:\n{error_trace}")
        return {"status": "error", "msg": f"Ошибка: {str(e)}"}

if __name__ == '__main__':
    eel.start('index.html', size=(1200, 850), mode='chrome')