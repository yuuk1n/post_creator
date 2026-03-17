import telebot
from telebot import types as bot_types
from tkinter import filedialog, messagebox
from PIL import ImageGrab, Image
import os
import re
import json
import threading
import asyncio
import time
import customtkinter as ctk

# Импортируем базу интерфейса и логику телетона
from gui_base import GuiStructure, HAS_DND
from logic_telethon import TelethonLogic

class App(GuiStructure):
    def __init__(self):
        super().__init__()
        
        # 1. Загрузка настроек API (из config.json)
        self.load_config()

        # 2. Привязка функций к кнопкам
        self.btn_browse.configure(command=self.browse_image)
        self.btn_avatar.configure(command=self.browse_avatar)
        self.send_btn.configure(command=self.run_process)
        self.save_settings_btn.configure(command=self.save_config)
        self.crypto_btn.configure(command=self.check_crypto)
        self.btn_load_creative.configure(command=self.load_creative)
        self.btn_save_creative.configure(command=self.save_creative)

        # 3. Drag & Drop (если поддерживается системой)
        if self._dnd_active:
            from tkinterdnd2 import DND_FILES
            self.drop_target_register(DND_FILES)
            self.dnd_bind('<<Drop>>', self.handle_drop)

        # 4. Инициализация всех горячих клавиш
        self.init_all_bindings()
        
        # Авто-загрузка шаблона при старте
        if os.path.exists("creative.json"):
            self.load_creative(silent=True)

    def init_all_bindings(self):
        """Настройка всех биндов: текст отдельно, фото отдельно"""
        # Глобальный скролл
        self.bind_all("<Button-4>", self._on_mousewheel)
        self.bind_all("<Button-5>", self._on_mousewheel)

        # 1. Текстовые поля (только текст)
        text_entries = [
            self.chan_name, self.chan_user, self.chan_bio,
            self.api_id_e, self.api_hash_e, self.bot_token_e, self.bot_user_e
        ]
        for w in text_entries:
            self.add_common_binds(w)

        # Поля кнопок под постом
        for t_e, u_e in self.btns_inputs:
            self.add_common_binds(t_e)
            self.add_common_binds(u_e)

        # Форматирование основного текста (Ctrl+B, I, K)
        self.setup_text_formatting(self.text_msg)
        
        # 2. Поля МЕДИА (Особая обработка Ctrl+V для картинок)
        for w in [self.media_path, self.avatar_path]:
            # Разрешаем выделение текста (Ctrl+A)
            w.bind("<Control-a>", lambda e, wid=w: self.select_all(e, wid))
            w.bind("<Control-A>", lambda e, wid=w: self.select_all(e, wid))
            # Вешаем универсальную вставку фото/пути
            w.bind("<Control-v>", lambda e, wid=w: self.handle_universal_paste(wid))
            w.bind("<Control-V>", lambda e, wid=w: self.handle_universal_paste(wid))

    def add_common_binds(self, widget):
        """Общие бинды для текстовых полей (A, V)"""
        widget.bind("<Control-a>", lambda e: self.select_all(e, widget))
        widget.bind("<Control-A>", lambda e: self.select_all(e, widget))
        widget.bind("<Control-v>", lambda e: self.handle_entry_paste(e, widget))
        widget.bind("<Control-V>", lambda e: self.handle_entry_paste(e, widget))

    def handle_entry_paste(self, event, widget):
        """Вставка только текста"""
        try:
            text = self.clipboard_get()
            # Проверка, чтобы не вставить бинарный код картинки в текст
            if text.startswith('\x89PNG') or "JFIF" in text[:10]:
                return "break"
            try:
                widget.delete("sel.first", "sel.last")
            except: pass
            widget.insert("insert", text)
        except: pass
        return "break"

    def handle_universal_paste(self, target_widget):
        """Обработка Ctrl+V для медиа полей"""
        # Делаем микро-задержку, чтобы буфер успел открыться
        self.after(50, lambda: self.process_clipboard_to_widget(target_widget))
        return "break"

    def process_clipboard_to_widget(self, target_widget):
        """Логика захвата скриншота или пути к файлу"""
        try:
            # 1. Пытаемся взять картинку (нужен xclip!)
            img = ImageGrab.grabclipboard()
            if img:
                if isinstance(img, Image.Image):
                    prefix = "avatar" if target_widget == self.avatar_path else "post"
                    path = os.path.join(os.getcwd(), f"last_{prefix}_paste.png")
                    img.save(path, "PNG")
                    target_widget.delete(0, "end")
                    target_widget.insert(0, path)
                    print(f"[CLIPBOARD] Сохранен скриншот: {path}")
                    return
                elif isinstance(img, (list, tuple)):
                    path = str(img[0]).strip('{}')
                    if os.path.exists(path):
                        target_widget.delete(0, "end")
                        target_widget.insert(0, path)
                        return

            # 2. Если картинки нет, проверяем текст
            text = self.clipboard_get()
            # Защита от мусора PNG в поле
            if text.startswith('\x89PNG') or "JFIF" in text[:10]:
                target_widget.delete(0, "end")
                print("[WARNING] В буфере картинка, но xclip не установлен или не видит её.")
                return

            text = text.strip()
            clean_path = text.replace('file://', '').strip('"').strip("'").strip('{}')
            
            target_widget.delete(0, "end")
            if os.path.exists(clean_path):
                target_widget.insert(0, clean_path)
            else:
                target_widget.insert(0, text)
        except Exception as e:
            print(f"Ошибка вставки: {e}")

    def select_all(self, event, widget):
        if isinstance(widget, ctk.CTkTextbox):
            widget.tag_add("sel", "1.0", "end")
        else:
            widget.select_range(0, 'end')
            widget.icursor('end')
        return "break"

    def setup_text_formatting(self, widget):
        self.add_common_binds(widget)
        widget.bind("<Control-b>", lambda e: self.wrap_selection(widget, "<b>", "</b>"))
        widget.bind("<Control-i>", lambda e: self.wrap_selection(widget, "<i>", "</i>"))
        widget.bind("<Control-k>", lambda e: self.add_hyperlink(widget))
        widget.bind("<KeyRelease>", self.update_preview)

    def wrap_selection(self, widget, open_tag, close_tag):
        try:
            if widget.tag_ranges("sel"):
                start, end = widget.index("sel.first"), widget.index("sel.last")
                content = widget.get(start, end)
                widget.delete(start, end)
                widget.insert(start, f"{open_tag}{content}{close_tag}")
                self.update_preview()
        except: pass
        return "break"

    def add_hyperlink(self, widget):
        url = ctk.CTkInputDialog(text="Введите URL:", title="Ссылка").get_input()
        if url:
            if not url.startswith("http"): 
                url = f"https://t.me/{url.replace('@','')}"
            self.wrap_selection(widget, f'<a href="{url}">', '</a>')
        return "break"

    def handle_drop(self, event):
        path = event.data.strip('{}') 
        if os.path.exists(path):
            if self.tabview.get() == "🛠 Конструктор Канала":
                self.avatar_path.delete(0, "end"); self.avatar_path.insert(0, path)
            else:
                self.media_path.delete(0, "end"); self.media_path.insert(0, path)

    def browse_image(self):
        f = filedialog.askopenfilename()
        if f: self.media_path.delete(0, "end"); self.media_path.insert(0, f)

    def browse_avatar(self):
        f = filedialog.askopenfilename()
        if f: self.avatar_path.delete(0, "end"); self.avatar_path.insert(0, f)

    def _on_mousewheel(self, event):
        try:
            widget = self.winfo_containing(event.x_root, event.y_root)
            if not widget or "text" in str(widget).lower(): 
                return
            direction = -1 if event.num == 4 else 1
            tab = self.tabview.get()
            if tab == "🛠 Конструктор Канала": 
                self.tab_builder_frame._parent_canvas.yview_scroll(direction, "units")
            elif tab == "⚙ Настройки и Крипто": 
                self.tab_settings_frame._parent_canvas.yview_scroll(direction, "units")
        except: pass

    # --- РАБОТА С ШАБЛОНАМИ ---

    def load_config(self):
        if os.path.exists("config.json"):
            with open("config.json", "r", encoding="utf-8") as f:
                d = json.load(f)
                self.api_id_e.insert(0, str(d.get("api_id", "")))
                self.api_hash_e.insert(0, d.get("api_hash", ""))
                self.bot_token_e.insert(0, d.get("bot_token", ""))
                self.bot_user_e.insert(0, d.get("bot_user", ""))

    def save_config(self):
        d = {"api_id": self.api_id_e.get(), "api_hash": self.api_hash_e.get(), "bot_token": self.bot_token_e.get(), "bot_user": self.bot_user_e.get()}
        with open("config.json", "w", encoding="utf-8") as f: 
            json.dump(d, f, indent=4)
        messagebox.showinfo("OK", "Конфиг API сохранен")

    def save_creative(self):
        data = {
            "name": self.chan_name.get(), "user": self.chan_user.get(), "bio": self.chan_bio.get(), "avatar": self.avatar_path.get(),
            "text": self.text_msg.get("1.0", "end-1c"), "media": self.media_path.get(),
            "btns": [[t.get(), u.get()] for t, u in self.btns_inputs if t.get().strip()],
            "reacs": [em for em, var in self.reac_vars.items() if var.get()]
        }
        with open("creative.json", "w", encoding="utf-8") as f: 
            json.dump(data, f, ensure_ascii=False, indent=4)
        messagebox.showinfo("OK", "Креатив сохранен")

    def load_creative(self, silent=False):
        if not os.path.exists("creative.json"): return
        with open("creative.json", "r", encoding="utf-8") as f:
            d = json.load(f)
            self.chan_name.delete(0, "end"); self.chan_name.insert(0, d.get("name", ""))
            self.chan_user.delete(0, "end"); self.chan_user.insert(0, d.get("user", ""))
            self.chan_bio.delete(0, "end"); self.chan_bio.insert(0, d.get("bio", ""))
            self.avatar_path.delete(0, "end"); self.avatar_path.insert(0, d.get("avatar", ""))
            self.text_msg.delete("1.0", "end"); self.text_msg.insert("1.0", d.get("text", ""))
            self.media_path.delete(0, "end"); self.media_path.insert(0, d.get("media", ""))
            for i, b in enumerate(d.get("btns", [])):
                if i < len(self.btns_inputs):
                    self.btns_inputs[i][0].delete(0, "end"); self.btns_inputs[i][0].insert(0, b[0])
                    self.btns_inputs[i][1].delete(0, "end"); self.btns_inputs[i][1].insert(0, b[1])
            saved = d.get("reacs", [])
            for em, v in self.reac_vars.items(): v.set(em in saved)
            self.update_preview()
            if not silent: messagebox.showinfo("OK", "Креатив загружен")

    def update_preview(self, event=None):
        t = re.sub(r'<[^>]+>', '', self.text_msg.get("1.0", "end-1c"))
        self.prev_text.configure(text=t if t.strip() else "Превью...")

    # --- ЗАПУСК ПОТОКОВ ---

    def run_process(self):
        if not self.api_id_e.get():
            messagebox.showerror("Ошибка", "Заполните API данные в настройках!")
            return
        threading.Thread(target=self._async_worker, daemon=True).start()

    def _async_worker(self):
        try:
            print("\n[SYSTEM] Старт процесса...")
            sessions = [f.split('.')[0] for f in os.listdir("sessions") if f.endswith(".session")]
            if not sessions:
                self.after(0, lambda: messagebox.showerror("Ошибка", "Нет сессий"))
                return
            
            logic = TelethonLogic(int(self.api_id_e.get()), self.api_hash_e.get())
            reacs = [] if self.disable_reac.get() else [em for em, v in self.reac_vars.items() if v.get()]
            
            # 1. Telethon (Создание канала)
            url, cid = asyncio.run(logic.create_and_setup_channel(
                sessions[0], self.chan_name.get(), self.chan_bio.get(),
                self.chan_user.get(), self.avatar_path.get(), self.bot_user_e.get(), reacs
            ))

            # Пауза для Bot API (Важно!)
            print(f"[SYSTEM] Канал создан: {url}. Синхронизация 6 секунд...")
            time.sleep(6)

            # 2. Бот (Постинг)
            print(f"[BOT] Отправляю пост в ID: {cid}")
            bot = telebot.TeleBot(self.bot_token_e.get())
            markup = bot_types.InlineKeyboardMarkup()
            for t_e, u_e in self.btns_inputs:
                if t_e.get() and u_e.get():
                    u = u_e.get().strip()
                    if not u.startswith("http"): u = f"https://t.me/{u.replace('@','')}"
                    markup.add(bot_types.InlineKeyboardButton(t_e.get(), url=u))

            txt = self.text_msg.get("1.0", "end-1c")
            med = self.media_path.get()
            
            if med and os.path.exists(med):
                with open(med, 'rb') as f:
                    if med.lower().endswith(('.mp4', '.mov')): 
                        bot.send_video(cid, f, caption=txt, reply_markup=markup, parse_mode="HTML")
                    else: 
                        bot.send_photo(cid, f, caption=txt, reply_markup=markup, parse_mode="HTML")
            else: 
                bot.send_message(cid, txt, reply_markup=markup, parse_mode="HTML")

            print("[BOT] Пост успешно опубликован!")
            self.after(0, lambda u=url: messagebox.showinfo("Готово", f"Создано!\n{u}"))
        except Exception as e:
            err = str(e)
            print(f"[ERROR] {err}")
            self.after(0, lambda m=err: messagebox.showerror("Ошибка цикла", m))

    def check_crypto(self):
        threading.Thread(target=self._crypto_worker, daemon=True).start()

    def _crypto_worker(self):
        try:
            sessions = [f.split('.')[0] for f in os.listdir("sessions") if f.endswith(".session")]
            if not sessions: return
            logic = TelethonLogic(int(self.api_id_e.get()), self.api_hash_e.get())
            res = asyncio.run(logic.check_balances(sessions[0]))
            self.after(0, lambda r=res: self._update_crypto_ui(r))
        except Exception as e:
            err = str(e)
            self.after(0, lambda m=err: messagebox.showerror("Крипто", m))

    def _update_crypto_ui(self, text):
        self.crypto_res.delete("1.0", "end"); self.crypto_res.insert("1.0", text)

if __name__ == "__main__":
    app = App()
    app.mainloop()