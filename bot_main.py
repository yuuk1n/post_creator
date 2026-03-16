import customtkinter as ctk
from tkinter import filedialog, messagebox
import telebot
from telebot import types
from PIL import ImageGrab
import os
import re

# Проверка наличия библиотеки Drag-and-Drop
try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
    HAS_DND = True
except ImportError:
    HAS_DND = False

# --- НАСТРОЙКИ ---
BOT_TOKEN = '8797384819:AAFnnavrCjTRABCbdopOnAtgVtUn-_96HyY'
bot = telebot.TeleBot(BOT_TOKEN)

# Базовый класс для поддержки DND
if HAS_DND:
    class BaseApp(ctk.CTk, TkinterDnD.DnDWrapper):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            try:
                self.TkdndVersion = TkinterDnD._load_tkdnd(self)
                self._dnd_active = True
            except:
                self._dnd_active = False
else:
    class BaseApp(ctk.CTk):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._dnd_active = False

class App(BaseApp):
    def __init__(self):
        super().__init__()

        self.title("TG Post Builder Pro")
        self.geometry("650x950")
        ctk.set_appearance_mode("dark")

        # Основной контейнер с прокруткой
        self.main_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Умный скролл для Linux
        self.bind_all("<Button-4>", self._on_mousewheel)
        self.bind_all("<Button-5>", self._on_mousewheel)

        # ЗАГОЛОВОК
        self.header = ctk.CTkLabel(self.main_frame, text="TG CONSTRUCTOR", font=("Impact", 35), text_color="#24A1DE")
        self.header.pack(pady=15)

        # КАНАЛ
        self.chan_card = ctk.CTkFrame(self.main_frame, fg_color="#2B2B2B", corner_radius=15)
        self.chan_card.pack(pady=10, padx=20, fill="x")
        self.channel_entry = ctk.CTkEntry(self.chan_card, placeholder_text="Ссылка на канал или ID (-100...)", width=500, height=45)
        self.channel_entry.pack(pady=15, padx=15)
        self.add_common_binds(self.channel_entry)

        # ТЕКСТ ПОСТА
        self.text_card = ctk.CTkFrame(self.main_frame, fg_color="#2B2B2B", corner_radius=15)
        self.text_card.pack(pady=10, padx=20, fill="x")
        ctk.CTkLabel(self.text_card, text="ТЕКСТ ПОСТА (Ctrl+B, I, K, A, Z, V)", font=("Arial", 12, "bold")).pack(pady=(10,0))
        
        self.text_msg = ctk.CTkTextbox(self.text_card, width=500, height=180, border_width=2, font=("Consolas", 15), undo=True)
        self.text_msg.pack(pady=15, padx=15)
        self.setup_text_formatting(self.text_msg)

        # МЕДИА
        self.media_card = ctk.CTkFrame(self.main_frame, fg_color="#2B2B2B", corner_radius=15)
        self.media_card.pack(pady=10, padx=20, fill="x")
        ctk.CTkLabel(self.media_card, text="МЕДИА (Путь или Ctrl+V для скриншота)", font=("Arial", 12, "bold")).pack(pady=(10,0))
        
        self.media_path = ctk.CTkEntry(self.media_card, placeholder_text="Путь к файлу...", height=35)
        self.media_path.pack(side="left", fill="x", expand=True, padx=(15, 5), pady=15)
        self.media_path.bind("<Control-v>", self.handle_media_paste)
        self.add_common_binds(self.media_path)

        self.btn_browse = ctk.CTkButton(self.media_card, text="ОБЗОР", width=80, fg_color="#24A1DE", command=self.browse_image)
        self.btn_browse.pack(side="right", padx=(5, 15))

        # КНОПКИ
        self.btn_card = ctk.CTkFrame(self.main_frame, fg_color="#2B2B2B", corner_radius=15)
        self.btn_card.pack(pady=10, padx=20, fill="x")
        
        self.row_width_entry = ctk.CTkEntry(self.btn_card, placeholder_text="В ряд", width=60)
        self.row_width_entry.pack(pady=10)
        self.row_width_entry.insert(0, "1")
        self.add_common_binds(self.row_width_entry)

        self.btns_inputs = []
        for i in range(5):
            f = ctk.CTkFrame(self.btn_card, fg_color="transparent")
            f.pack(pady=2, padx=10, fill="x")
            t = ctk.CTkEntry(f, placeholder_text=f"Название кнопки {i+1}", width=180)
            t.pack(side="left", padx=2, fill="x", expand=True)
            self.add_common_binds(t)
            
            u = ctk.CTkEntry(f, placeholder_text=f"@link или ссылка", width=180)
            u.pack(side="left", padx=2, fill="x", expand=True)
            self.add_common_binds(u)
            self.btns_inputs.append((t, u))

        # КНОПКА ПУСК
        self.send_btn = ctk.CTkButton(self.main_frame, text="🚀 ОПУБЛИКОВАТЬ", command=self.send_post, 
                                     fg_color="#28a745", hover_color="#218838", height=65, font=("Arial", 22, "bold"))
        self.send_btn.pack(pady=30, padx=20, fill="x")

        if self._dnd_active:
            self.drop_target_register(DND_FILES)
            self.dnd_bind('<<Drop>>', self.handle_drop)

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
                start = widget.index("sel.first")
                end = widget.index("sel.last")
                content = widget.get(start, end)
                widget.delete(start, end)
                widget.insert(start, f"{open_tag}{content}{close_tag}")
        except: pass
        return "break"

    def add_hyperlink(self, widget):
        url = ctk.CTkInputDialog(text="Введите URL или @username:", title="Вставка гиперссылки").get_input()
        if url:
            url = url.strip()
            # Микрофикс: авто-формат ссылки
            if url.startswith("@"):
                url = f"https://t.me/{url[1:]}"
            elif not url.startswith(("http://", "https://")) and not url.startswith("-"):
                url = f"https://t.me/{url}"
                
            self.wrap_selection(widget, f'<a href="{url}">', '</a>')
        return "break"

    def handle_drop(self, event):
        path = event.data.strip('{}') 
        if os.path.exists(path):
            self.media_path.delete(0, "end")
            self.media_path.insert(0, path)

    def handle_media_paste(self, event=None):
        self.after(50, self.process_media_content)
        return "break"

    def process_media_content(self):
        try:
            img = ImageGrab.grabclipboard()
            if img:
                file_path = os.path.join(os.getcwd(), "last_paste.png")
                img.save(file_path, "PNG")
                self.media_path.delete(0, "end")
                self.media_path.insert(0, file_path)
                return
        except: pass
        try:
            clipboard_text = self.clipboard_get().strip()
            clean_path = clipboard_text.replace('file://', '')
            if os.path.exists(clean_path):
                self.media_path.delete(0, "end")
                self.media_path.insert(0, clean_path)
        except: pass

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