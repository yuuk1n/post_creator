import customtkinter as ctk
import os

try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
    HAS_DND = True
except ImportError:
    HAS_DND = False

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

class GuiStructure(BaseApp):
    def __init__(self):
        super().__init__()

        self.title("TG Post Builder Pro")
        self.geometry("650x950")
        ctk.set_appearance_mode("dark")

        # Основной контейнер с прокруткой
        self.main_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # ЗАГОЛОВОК
        self.header = ctk.CTkLabel(self.main_frame, text="TG CONSTRUCTOR", font=("Impact", 35), text_color="#24A1DE")
        self.header.pack(pady=15)

        # КАНАЛ
        self.chan_card = ctk.CTkFrame(self.main_frame, fg_color="#2B2B2B", corner_radius=15)
        self.chan_card.pack(pady=10, padx=20, fill="x")
        self.channel_entry = ctk.CTkEntry(self.chan_card, placeholder_text="Ссылка на канал или ID (-100...)", width=500, height=45)
        self.channel_entry.pack(pady=15, padx=15)

        # ТЕКСТ ПОСТА
        self.text_card = ctk.CTkFrame(self.main_frame, fg_color="#2B2B2B", corner_radius=15)
        self.text_card.pack(pady=10, padx=20, fill="x")
        ctk.CTkLabel(self.text_card, text="ТЕКСТ ПОСТА (Ctrl+B, I, K, A, Z, V)", font=("Arial", 12, "bold")).pack(pady=(10,0))
        
        self.text_msg = ctk.CTkTextbox(self.text_card, width=500, height=180, border_width=2, font=("Consolas", 15), undo=True)
        self.text_msg.pack(pady=15, padx=15)

        # МЕДИА
        self.media_card = ctk.CTkFrame(self.main_frame, fg_color="#2B2B2B", corner_radius=15)
        self.media_card.pack(pady=10, padx=20, fill="x")
        ctk.CTkLabel(self.media_card, text="МЕДИА (Путь или Ctrl+V для скриншота)", font=("Arial", 12, "bold")).pack(pady=(10,0))
        
        self.media_path = ctk.CTkEntry(self.media_card, placeholder_text="Путь к файлу...", height=35)
        self.media_path.pack(side="left", fill="x", expand=True, padx=(15, 5), pady=15)

        self.btn_browse = ctk.CTkButton(self.media_card, text="ОБЗОР", width=80, fg_color="#24A1DE")
        self.btn_browse.pack(side="right", padx=(5, 15))

        # КНОПКИ (URL)
        self.btn_card = ctk.CTkFrame(self.main_frame, fg_color="#2B2B2B", corner_radius=15)
        self.btn_card.pack(pady=10, padx=20, fill="x")
        
        self.row_width_entry = ctk.CTkEntry(self.btn_card, placeholder_text="В ряд", width=60)
        self.row_width_entry.pack(pady=10)
        self.row_width_entry.insert(0, "1")

        self.btns_inputs = []
        for i in range(5):
            f = ctk.CTkFrame(self.btn_card, fg_color="transparent")
            f.pack(pady=2, padx=10, fill="x")
            t = ctk.CTkEntry(f, placeholder_text=f"Название кнопки {i+1}", width=180)
            t.pack(side="left", padx=2, fill="x", expand=True)
            u = ctk.CTkEntry(f, placeholder_text=f"@link или ссылка", width=180)
            u.pack(side="left", padx=2, fill="x", expand=True)
            self.btns_inputs.append((t, u))

        # КНОПКА ПУСК
        self.send_btn = ctk.CTkButton(self.main_frame, text="🚀 ОПУБЛИКОВАТЬ", 
                                     fg_color="#28a745", hover_color="#218838", height=65, font=("Arial", 22, "bold"))
        self.send_btn.pack(pady=30, padx=20, fill="x")