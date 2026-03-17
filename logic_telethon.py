import asyncio
import os
import random
import string
import shutil
import logging
from telethon import TelegramClient, functions, types
from telethon.errors import UsernameOccupiedError, FloodWaitError, UsernameInvalidError

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Твой список устройств
DEVICES =[("Samsung SM-G998B", "Android 13"), ("iPhone 15 Pro Max", "iOS 17.1")]

class TelethonLogic:
    def __init__(self, api_id, api_hash):
        self.api_id = api_id
        self.api_hash = api_hash
        self.device = random.choice(DEVICES)

    async def get_client(self, session_name):
        return TelegramClient(f"sessions/{session_name}", self.api_id, self.api_hash,
                              device_model=self.device[0], system_version=self.device[1])

    async def create_and_setup_channel(self, session_file, title, about, username, avatar_path, bot_user, reactions, progress_callback):
        logger.info(f"[Telethon] Подготовка клиента {session_file}...")
        client = await self.get_client(session_file)
        
        try:
            await asyncio.wait_for(client.connect(), timeout=20.0)
            logger.info("[Telethon] Соединение установлено.")
        except asyncio.TimeoutError:
            raise Exception("Файл сессии заблокирован! Убедись, что старое окно закрыто.")

        progress_callback(10, "Создаю канал...")
        await asyncio.sleep(random.uniform(2, 4))
        
        try:
            # 1. СОЗДАНИЕ КАНАЛА
            logger.info(f"[Telethon] Создание канала: {title}")
            result = await client(functions.channels.CreateChannelRequest(title=title, about=about, megagroup=False))
            channel = result.chats[0]
            channel_id = int(f"-100{channel.id}")
            
            progress_callback(30, "Настройка юзернейма...")
            await asyncio.sleep(random.uniform(2, 4))

            # 2. ЮЗЕРНЕЙМ
            current_user = username
            username_set = False
            suffix = ""
            try:
                while True:
                    try:
                        target_user = f"{username}{suffix}"
                        await client(functions.channels.UpdateUsernameRequest(channel=channel, username=target_user))
                        current_user = target_user
                        username_set = True
                        logger.info(f"[Telethon] Юзернейм @{current_user} привязан.")
                        break
                    except UsernameOccupiedError:
                        await asyncio.sleep(2)
                        suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=2))
                    except UsernameInvalidError:
                        raise Exception(f"Юзернейм @{target_user} недопустим (используй только английские буквы).")
            except FloodWaitError:
                username_set = False

            # 3. АВАТАРКА
            if avatar_path and os.path.exists(avatar_path):
                progress_callback(50, "Загрузка аватара...")
                file = await client.upload_file(avatar_path)
                await client(functions.channels.EditPhotoRequest(channel=channel, photo=file))
                logger.info("[Telethon] Аватар установлен.")
                await asyncio.sleep(2)

            # 4. АДМИН-ПРАВА БОТУ
            progress_callback(70, f"Настройка админа {bot_user}...")
            bot_entity = await client.get_input_entity(bot_user)
            await client(functions.channels.EditAdminRequest(
                channel=channel, user_id=bot_entity,
                admin_rights=types.ChatAdminRights(
                    post_messages=True, edit_messages=True, delete_messages=True,
                    invite_users=True, change_info=True
                ), rank='Admin'
            ))
            
            # 5. РЕАКЦИИ
            progress_callback(85, "Настройка реакций...")
            if reactions:
                await client(functions.messages.SetChatAvailableReactionsRequest(
                    peer=channel,
                    available_reactions=types.ChatReactionsSome(reactions=[types.ReactionEmoji(em) for em in set(reactions)])
                ))

            # 6. ОЧИСТКА СЕРВИСНЫХ СООБЩЕНИЙ
            progress_callback(90, "Очистка чата...")
            await asyncio.sleep(4)
            to_delete = []
            async for msg in client.iter_messages(channel, limit=20):
                if isinstance(msg, types.MessageService) or msg.action:
                    to_delete.append(msg.id)
            if to_delete:
                await client.delete_messages(channel, to_delete)
                logger.info(f"[Telethon] Системные уведомления удалены: {to_delete}")

            # --- НОВАЯ ФУНКЦИЯ: ВЫХОД ИЗ КАНАЛА ---
            progress_callback(95, "Выхожу из канала...")
            logger.info("[Telethon] Покидаю канал (функция 'Покинуть канал')...")
            await client(functions.channels.LeaveChannelRequest(channel=channel))
            logger.info("[Telethon] Аккаунт успешно покинул канал.")

            await client.disconnect()
            
            # Перемещаем сессию, чтобы не использовать её повторно
            if not os.path.exists("old_sessions"): os.makedirs("old_sessions")
            shutil.move(f"sessions/{session_file}.session", f"old_sessions/{session_file}.session")
            
            progress_callback(100, "Готово! Telethon завершил работу.")
            return current_user if username_set else None, channel_id

        except Exception as e:
            await client.disconnect()
            raise e