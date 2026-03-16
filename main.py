import telebot
from telebot import types
from tkinter import filedialog, messagebox
from PIL import ImageGrab, Image # Добавили Image для проверки типа
import os
import re
import customtkinter as ctk
from gui_base import GuiStructure, HAS_DND

# --- НАСТРОЙКИ ---
BOT_TOKEN = '8797384819:AAFnnavrCjTRABCbdopOnAtgVtUn-_96HyY'
bot = telebot.TeleBot(BOT_TOKEN)

class App(GuiStructure):
    def __init__(self):
        super().__init__()

        # Привязываем функции к кнопкам
        self.btn_browse.configure(command=self.browse_image)
        self.send_btn.configure(command=self.send_post)

        if self._dnd_active:
            from tkinterdnd2 import DND_FILES
            self.drop_target_register(DND_FILES)
            self.dnd_bind('<<Drop>>', self.handle_drop)

        # Важно: Сначала инициализируем все бинды
        self.init_all_bindings()

    def init_all_bindings(self):
        # 1. Скролл
        self.bind_all("<Button-4>", self._on_mousewheel)
        self.bind_all("<Button-5>", self._on_mousewheel)

        # 2. Общие поля (Канал, количество в ряд)
        self.add_common_binds(self.channel_entry)
        self.add_common_binds(self.row_width_entry)

        # 3. Динамические кнопки
        for t_e, u_e in self.btns_inputs:
            self.add_common_binds(t_e)
            self.add_common_binds(u_e)

        # 4. ТЕКСТОВОЕ ПОЛЕ (Свое форматирование)
        self.setup_text_formatting(self.text_msg)

        # 5. ПОЛЕ МЕДИА (Особый приоритет)
        # Сначала вешаем Ctrl+A (выделить все), но НЕ вешаем стандартный Ctrl+V
        self.media_path.bind("<Control-a>", lambda e: self.select_all(e, self.media_path))
        self.media_path.bind("<Control-A>", lambda e: self.select_all(e, self.media_path))
        # Вешаем нашу крутую вставку (картинка + текст)
        self.media_path.bind("<Control-v>", self.handle_media_paste)
        self.media_path.bind("<Control-V>", self.handle_media_paste)

    def process_media_content(self):
        """Улучшенная логика захвата медиа из буфера"""
        try:
            # Пытаемся взять картинку (скриншот)
            img = ImageGrab.grabclipboard()
            
            if img:
                # Если это именно объект картинки (скриншот)
                if isinstance(img, Image.Image):
                    file_path = os.path.join(os.getcwd(), "last_paste.png")
                    img.save(file_path, "PNG")
                    self.media_path.delete(0, "end")
                    self.media_path.insert(0, file_path)
                    return
                
                # Если в буфере список файлов (например, скопировали файл в проводнике)
                elif isinstance(img, (list, tuple)):
                    file_path = img[0].strip('{}') # Убираем скобки tcl если есть
                    if os.path.exists(file_path):
                        self.media_path.delete(0, "end")
                        self.media_path.insert(0, file_path)
                        return
        except Exception as e:
            print(f"Clipboard Image Error: {e}")

        # Если картинки нет, пробуем достать текст (путь)
        try:
            clipboard_text = self.clipboard_get().strip()
            # Убираем мусор из пути, если файл скопирован как текст
            clean_path = clipboard_text.replace('file://', '').strip('"').strip("'")
            if os.path.exists(clean_path):
                self.media_path.delete(0, "end")
                self.media_path.insert(0, clean_path)
            else:
                # Если это просто текст, а не путь, вставляем как текст
                self.media_path.delete(0, "end")
                self.media_path.insert(0, clipboard_text)
        except:
            pass

    # --- ОСТАЛЬНЫЕ ФУНКЦИИ (БЕЗ ИЗМЕНЕНИЙ) ---

    def handle_media_paste(self, event=None):
        # Небольшая задержка, чтобы буфер обмена успел "отдать" данные
        self.after(50, self.process_media_content)
        return "break"

    def _on_mousewheel(self, event):
        widget = self.winfo_containing(event.x_root, event.y_root)
        if widget and ("textbox" in str(widget).lower() or "text" in str(widget).lower()):
            return 
        if event.num == 4:
            self.main_frame._parent_canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.main_frame._parent_canvas.yview_scroll(1, "units")

    def add_common_binds(self, widget):
        widget.bind("<Control-a>", lambda e: self.select_all(e, widget))
        widget.bind("<Control-A>", lambda e: self.select_all(e, widget))
        if isinstance(widget, ctk.CTkEntry):
            widget.bind("<Control-v>", lambda e: self.handle_entry_paste(e, widget))

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
        widget.bind("<Control-v>", lambda e: self.handle_text_paste(e, widget))

    def handle_text_paste(self, event, widget):
        try:
            text = self.clipboard_get()
            if widget.tag_ranges("sel"):
                widget.delete("sel.first", "sel.last")
            widget.insert("insert", text)
        except: pass
        return "break"

    def handle_entry_paste(self, event, widget):
        try:
            text = self.clipboard_get()
            try:
                start = widget.index("sel.first")
                end = widget.index("sel.last")
                widget.delete(start, end)
            except: pass
            widget.insert("insert", text)
        except: pass
        return "break"

    def wrap_selection(self, widget, open_tag, close_tag):
        try:
            if widget.tag_ranges("sel"):
                start, end = widget.index("sel.first"), widget.index("sel.last")
                content = widget.get(start, end)
                widget.delete(start, end)
                widget.insert(start, f"{open_tag}{content}{close_tag}")
        except: pass
        return "break"

    def add_hyperlink(self, widget):
        url = ctk.CTkInputDialog(text="Введите URL:", title="Ссылка").get_input()
        if url:
            url = url.strip()
            if url.startswith("@"): url = f"https://t.me/{url[1:]}"
            elif not url.startswith(("http://", "https://")) and not url.startswith("-"): url = f"https://t.me/{url}"
            self.wrap_selection(widget, f'<a href="{url}">', '</a>')
        return "break"

    def handle_drop(self, event):
        path = event.data.strip('{}') 
        if os.path.exists(path):
            self.media_path.delete(0, "end")
            self.media_path.insert(0, path)

    def browse_image(self):
        file = filedialog.askopenfilename()
        if file:
            self.media_path.delete(0, "end")
            self.media_path.insert(0, file)

    def send_post(self):
        chan = self.channel_entry.get().strip()
        text = self.text_msg.get("0.0", "end-1c").strip()
        media = self.media_path.get().strip()

        if not chan:
            messagebox.showerror("Ошибка", "Введите канал!")
            return

        if not chan.startswith("-100") and not chan.startswith("@"):
            chan = "@" + chan.split('/')[-1]

        try:
            r_w = int(self.row_width_entry.get()) if self.row_width_entry.get().isdigit() else 1
            markup = types.InlineKeyboardMarkup(row_width=r_w)
            btns = []
            for t_e, u_e in self.btns_inputs:
                t, u = t_e.get().strip(), u_e.get().strip()
                if t and u:
                    clean_t = re.sub(r'<[^>]+>', '', t)
                    if u.startswith("@"): u = f"https://t.me/{u[1:]}"
                    elif not u.startswith("http"): u = f"https://t.me/{u}"
                    btns.append(types.InlineKeyboardButton(text=clean_t, url=u))
            markup.add(*btns)

            if media and os.path.exists(media):
                with open(media, 'rb') as f:
                    ext = media.lower()
                    if ext.endswith(('.mp4', '.mov')):
                        bot.send_video(chan, f, caption=text, reply_markup=markup, parse_mode="HTML")
                    else:
                        bot.send_photo(chan, f, caption=text, reply_markup=markup, parse_mode="HTML")
            else:
                bot.send_message(chan, text, reply_markup=markup, parse_mode="HTML")
            
            messagebox.showinfo("Успех", "Готово!")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

if __name__ == "__main__":
    app = App()
    app.mainloop()