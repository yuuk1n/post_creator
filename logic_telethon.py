import asyncio
import os
import random
import string
import shutil
import logging
from telethon import TelegramClient, functions, types
from telethon.errors import UsernameOccupiedError, FloodWaitError

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DEVICES = [
    ("Samsung SM-G998B", "Android 13"),
    ("iPhone 15 Pro Max", "iOS 17.1"),
    ("Xiaomi 13T Pro", "Android 14")
]

class TelethonLogic:
    def __init__(self, api_id, api_hash):
        self.api_id = api_id
        self.api_hash = api_hash
        self.device = random.choice(DEVICES)

    async def get_client(self, session_name):
        return TelegramClient(
            f"sessions/{session_name}", 
            self.api_id, self.api_hash,
            device_model=self.device[0],
            system_version=self.device[1]
        )

    async def create_and_setup_channel(self, session_file, title, about, username, avatar_path, bot_user, reactions):
        client = await self.get_client(session_file)
        await client.connect()
        logger.info(f"Сессия {session_file} подключена. Имитирую раздумья...")
        await asyncio.sleep(random.uniform(2, 4))
        
        try:
            # 1. Создание канала
            logger.info(f"Шаг 1: Создаю канал '{title}'")
            result = await client(functions.channels.CreateChannelRequest(title=title, about=about, megagroup=False))
            channel = result.chats[0]
            channel_id = int(f"-100{channel.id}")
            
            await asyncio.sleep(random.uniform(3, 5)) # Задержка после создания

            # 2. Установка ссылки (Username)
            suffix = ""
            current_user = username
            username_set = False
            
            logger.info(f"Шаг 2: Установка юзернейма")
            try:
                while True:
                    try:
                        target_user = f"{username}{suffix}"
                        logger.info(f"Пробую занять @{target_user}...")
                        await client(functions.channels.UpdateUsernameRequest(channel=channel, username=target_user))
                        current_user = target_user
                        username_set = True
                        break
                    except UsernameOccupiedError:
                        logger.warning(f"Занято. Жду секунду и меняю...")
                        await asyncio.sleep(2)
                        suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=2))
            except FloodWaitError as e:
                logger.error(f"ФЛУД на установку ссылки: ждать {e.seconds} сек. Оставляю приватным.")
                username_set = False

            await asyncio.sleep(random.uniform(3, 5)) # Задержка перед авой

            # 3. Аватарка
            if avatar_path and os.path.exists(avatar_path):
                logger.info(f"Шаг 3: Загружаю аватарку...")
                file = await client.upload_file(avatar_path)
                await client(functions.channels.EditPhotoRequest(channel=channel, photo=file))
                await asyncio.sleep(random.uniform(3, 5))

            # 4. Добавление бота в админы
            logger.info(f"Шаг 4: Назначаю бота {bot_user} админом...")
            await client(functions.channels.EditAdminRequest(
                channel=channel,
                user_id=bot_user,
                admin_rights=types.ChatAdminRights(
                    post_messages=True, edit_messages=True, delete_messages=True,
                    invite_users=True, change_info=True
                ),
                rank='Admin'
            ))
            
            await asyncio.sleep(random.uniform(4, 6)) # Критическая пауза для Bot API

            # 5. Реакции
            if reactions:
                logger.info(f"Шаг 5: Настройка реакций...")
                unique_reacs = list(set(reactions))
                await client(functions.messages.SetChatAvailableReactionsRequest(
                    peer=channel,
                    available_reactions=types.ChatReactionsSome(reactions=[types.ReactionEmoji(em) for em in unique_reacs])
                ))
                await asyncio.sleep(random.uniform(2, 4))

            # Итоговый URL
            final_url = f"https://t.me/{current_user}" if username_set else f"https://t.me/c/{channel.id}/1"
            
            logger.info(f"Все действия Telethon завершены успешно.")
            await client.disconnect()
            
            # Перенос сессии
            if not os.path.exists("old_sessions"): os.makedirs("old_sessions")
            shutil.move(f"sessions/{session_file}.session", f"old_sessions/{session_file}.session")
            
            return final_url, channel_id

        except Exception as e:
            logger.error(f"Ошибка в TelethonLogic: {e}")
            await client.disconnect()
            raise e

    async def check_balances(self, session_file):
        client = await self.get_client(session_file)
        await client.connect()
        results = []
        try:
            for target in ["@CryptoBot", "@wallet"]:
                logger.info(f"Проверяю {target}...")
                await client.send_message(target, "/start")
                await asyncio.sleep(random.uniform(2, 3))
                msgs = await client.get_messages(target, limit=1)
                results.append(f"📦 {target}:\n{msgs[0].text[:150]}...")
            await client.disconnect()
            return "\n\n".join(results)
        except Exception as e:
            await client.disconnect()
            return f"Ошибка: {str(e)}"