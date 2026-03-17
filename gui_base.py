import customtkinter as ctk
import os

try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
    HAS_DND = True
except ImportError:
    HAS_DND = False

if HAS_DND:
    class BaseApp(ctk.CTk, TkinterDnD.DnDWrapper):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            try:
                self.TkdndVersion = TkinterDnD._load_tkdnd(self)
                self._dnd_active = True
            except: self._dnd_active = False
else:
    class BaseApp(ctk.CTk):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._dnd_active = False

class GuiStructure(BaseApp):
    def __init__(self):
        super().__init__()

        self.title("TG Post Builder Pro")
        self.geometry("1100x950")
        ctk.set_appearance_mode("dark")

        self.tabview = ctk.CTkTabview(self, width=1050, height=900)
        self.tabview.pack(padx=10, pady=10, fill="both", expand=True)
        
        self.tab_builder = self.tabview.add("🛠 Конструктор Канала")
        self.tab_post = self.tabview.add("📝 Пост и Превью")
        self.tab_settings = self.tabview.add("⚙ Настройки и Крипто")

        self.setup_builder_tab()
        self.setup_post_tab()
        self.setup_settings_tab()

    def setup_builder_tab(self):
        self.tab_builder_frame = ctk.CTkScrollableFrame(self.tab_builder, fg_color="transparent")
        self.tab_builder_frame.pack(fill="both", expand=True)

        ctk.CTkLabel(self.tab_builder_frame, text="КОНСТРУКТОР КАНАЛА", font=("Impact", 30), text_color="#24A1DE").pack(pady=15)

        self.chan_name = ctk.CTkEntry(self.tab_builder_frame, placeholder_text="Название канала", width=500)
        self.chan_name.pack(pady=5)
        self.chan_user = ctk.CTkEntry(self.tab_builder_frame, placeholder_text="Юзернейм", width=500)
        self.chan_user.pack(pady=5)
        self.chan_bio = ctk.CTkEntry(self.tab_builder_frame, placeholder_text="Описание (Bio)", width=500)
        self.chan_bio.pack(pady=5)

        f_av = ctk.CTkFrame(self.tab_builder_frame, fg_color="transparent")
        f_av.pack(pady=10)
        self.avatar_path = ctk.CTkEntry(f_av, placeholder_text="Путь к аватарке...", width=380)
        self.avatar_path.pack(side="left", padx=5)
        self.btn_avatar = ctk.CTkButton(f_av, text="АВАТАР", width=100)
        self.btn_avatar.pack(side="left", padx=5)

        # ТЕ САМЫЕ КНОПКИ ДЛЯ КРЕАТИВА
        f_creat = ctk.CTkFrame(self.tab_builder_frame, fg_color="transparent")
        f_creat.pack(pady=10)
        self.btn_load_creative = ctk.CTkButton(f_creat, text="📂 ЗАГРУЗИТЬ КРЕАТИВ", fg_color="#6f42c1")
        self.btn_load_creative.pack(side="left", padx=5)
        self.btn_save_creative = ctk.CTkButton(f_creat, text="💾 СОХРАНИТЬ КРЕАТИВ", fg_color="#17a2b8")
        self.btn_save_creative.pack(side="left", padx=5)

        ctk.CTkLabel(self.tab_builder_frame, text="РЕАКЦИИ").pack(pady=10)
        self.reac_frame = ctk.CTkFrame(self.tab_builder_frame, fg_color="#2B2B2B")
        self.reac_frame.pack(pady=5, padx=50, fill="x")
        
        self.emojis = ["👍", "❤️", "🔥", "🥰", "👏", "😁", "🤩", "🎉", "⚡️", "😇", "😍", "💯", "🤝", "🦄", "💊"]
        self.reac_vars = {}
        grid_f = ctk.CTkFrame(self.reac_frame, fg_color="transparent")
        grid_f.pack(pady=10)
        r, c = 0, 0
        for emoji in self.emojis:
            v = ctk.BooleanVar(value=True)
            cb = ctk.CTkCheckBox(grid_f, text=emoji, variable=v, width=70)
            cb.grid(row=r, column=c, padx=5, pady=5)
            self.reac_vars[emoji] = v
            c += 1
            if c > 4: c = 0; r += 1
            
        self.disable_reac = ctk.CTkSwitch(self.tab_builder_frame, text="ОТКЛЮЧИТЬ РЕАКЦИИ")
        self.disable_reac.pack(pady=10)

    def setup_post_tab(self):
        main_f = ctk.CTkFrame(self.tab_post, fg_color="transparent")
        main_f.pack(fill="both", expand=True)

        left = ctk.CTkFrame(main_f, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True, padx=10)

        self.text_msg = ctk.CTkTextbox(left, height=250, font=("Consolas", 15), undo=True)
        self.text_msg.pack(fill="x", pady=10)

        f_med = ctk.CTkFrame(left, fg_color="transparent")
        f_med.pack(fill="x")
        self.media_path = ctk.CTkEntry(f_med, placeholder_text="Путь к медиа...")
        self.media_path.pack(side="left", fill="x", expand=True, padx=5)
        self.btn_browse = ctk.CTkButton(f_med, text="ОБЗОР", width=80)
        self.btn_browse.pack(side="right", padx=5)

        self.btns_inputs = []
        for i in range(3):
            f = ctk.CTkFrame(left, fg_color="transparent")
            f.pack(fill="x", pady=2)
            t = ctk.CTkEntry(f, placeholder_text="Текст кнопки", width=150)
            t.pack(side="left", padx=2, expand=True, fill="x")
            u = ctk.CTkEntry(f, placeholder_text="URL", width=150)
            u.pack(side="left", padx=2, expand=True, fill="x")
            self.btns_inputs.append((t, u))

        self.send_btn = ctk.CTkButton(left, text="🚀 ЗАПУСТИТЬ", height=70, fg_color="green", font=("Arial", 20, "bold"))
        self.send_btn.pack(fill="x", pady=20)

        right = ctk.CTkFrame(main_f, width=350, fg_color="#0F0F0F", corner_radius=30)
        right.pack(side="right", padx=10, pady=10, fill="y")
        self.prev_text = ctk.CTkLabel(right, text="Превью...", wraplength=250, justify="left")
        self.prev_text.pack(pady=20, padx=10)

    def setup_settings_tab(self):
        self.tab_settings_frame = ctk.CTkScrollableFrame(self.tab_settings, fg_color="transparent")
        self.tab_settings_frame.pack(fill="both", expand=True)

        self.api_id_e = ctk.CTkEntry(self.tab_settings_frame, placeholder_text="API ID", width=400)
        self.api_id_e.pack(pady=5)
        self.api_hash_e = ctk.CTkEntry(self.tab_settings_frame, placeholder_text="API HASH", width=400)
        self.api_hash_e.pack(pady=5)
        self.bot_token_e = ctk.CTkEntry(self.tab_settings_frame, placeholder_text="BOT TOKEN", width=400)
        self.bot_token_e.pack(pady=5)
        self.bot_user_e = ctk.CTkEntry(self.tab_settings_frame, placeholder_text="BOT USER (@...)", width=400)
        self.bot_user_e.pack(pady=5)
        
        self.save_settings_btn = ctk.CTkButton(self.tab_settings_frame, text="СОХРАНИТЬ КОНФИГ")
        self.save_settings_btn.pack(pady=10)
        self.crypto_btn = ctk.CTkButton(self.tab_settings_frame, text="💰 КРИПТО БАЛАНС", fg_color="#cc7a00")
        self.crypto_btn.pack(pady=20)
        self.crypto_res = ctk.CTkTextbox(self.tab_settings_frame, height=200, width=500)
        self.crypto_res.pack(pady=10)