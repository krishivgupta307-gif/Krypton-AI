import customtkinter as ctk
import threading
import time
from datetime import datetime
import os
from PIL import Image, ImageTk

try:
    import pyttsx3
except ImportError:
    pyttsx3 = None
try:
    import speech_recognition as sr
except ImportError:
    sr = None

from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate

# --- INITIALIZATION & GLOBALS ---
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

tts_enabled = False
tts_rate = 190
selected_voice_id = None
modelname = "def"
context = ""

template = """
Answer the question below.
Here is the conversation history: {context}
Question: {question}
Answer: 
"""
prompt = ChatPromptTemplate.from_template(template)
model = OllamaLLM(model=modelname)
chain = prompt | model

tts_lock = threading.Lock()
tts_engine = None


def init_global_tts():
    global tts_engine
    if pyttsx3 is not None and tts_engine is None:
        try:
            tts_engine = pyttsx3.init()
        except Exception as e:
            print(f"Failed to initialize master voice engine: {e}")


def speak_text_blocking(text):
    global tts_enabled, tts_rate, selected_voice_id, tts_engine
    if tts_enabled and tts_engine is not None and text.strip():
        with tts_lock:
            try:
                tts_engine.setProperty("rate", tts_rate)
                if selected_voice_id:
                    tts_engine.setProperty("voice", selected_voice_id)

                tts_engine.say(text)
                tts_engine.runAndWait()

                while tts_engine.isBusy():
                    time.sleep(0.1)

            except Exception as e:
                print(f"TTS Runtime Error: {e}")


def interrupt_tts():
    global tts_engine
    if tts_engine is not None:
        try:
            tts_engine.stop()
        except Exception as e:
            print(f"Error interrupting voice playback: {e}")


class KryptonApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        init_global_tts()

        # Window Settings
        self.title("Krypton AI")
        self.geometry("1100x750")
        self.minsize(800, 600)

        try:
            self.iconbitmap("logo.ico")
        except Exception:
            pass

        self.voice_assistant_mode = False
        self.is_speaking = False

        # Grid layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.themes = {
            "Vortex": {"bg_main": "#0f172a", "bg_sidebar": "#1e293b", "btn": "#3b82f6", "btn_hover": "#2563eb",
                       "user": "#3b82f6", "kry_label": "#60a5fa", "kry_text": "#22c55e"},
            "Pyro": {"bg_main": "#1a0505", "bg_sidebar": "#2b0b0b", "btn": "#ef4444", "btn_hover": "#dc2626",
                     "user": "#fef08a", "kry_label": "#ef4444", "kry_text": "#eab308"},
            "Terrashock": {"bg_main": "#051f0f", "bg_sidebar": "#064e3b", "btn": "#22c55e", "btn_hover": "#16a34a",
                           "user": "#fef08a", "kry_label": "#22c55e", "kry_text": "#eab308"},
            "Zephyr": {"bg_main": "#111827", "bg_sidebar": "#1f2937", "btn": "#06b6d4", "btn_hover": "#0891b2",
                       "user": "#67e8f9", "kry_label": "#eab308", "kry_text": "#ffffff"},
            "Plasma": {"bg_main": "#1a0b2e", "bg_sidebar": "#2d1b4e", "btn": "#d946ef", "btn_hover": "#c026d3",
                       "user": "#f472b6", "kry_label": "#d946ef", "kry_text": "#e879f9"},
            "Space": {"bg_main": "#070b14", "bg_sidebar": "#0f172a", "btn": "#6366f1", "btn_hover": "#4f46e5",
                      "user": "#818cf8", "kry_label": "#38bdf8", "kry_text": "#e0e7ff"},
            "Void": {"bg_main": "#000000", "bg_sidebar": "#0a0a0a", "btn": "#333333", "btn_hover": "#555555",
                     "user": "#a3a3a3", "kry_label": "#ffffff", "kry_text": "#d4d4d4"},
            "Heaven": {"bg_main": "#f8fafc", "bg_sidebar": "#f1f5f9", "btn": "#fbbf24", "btn_hover": "#f59e0b",
                       "user": "#2563eb", "kry_label": "#d97706", "kry_text": "#334155"}
        }

        # --- SIDEBAR ---
        self.sidebar = ctk.CTkFrame(self, width=260, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(2, weight=1)

        # --- LOGO HEADER FRAME ---
        self.logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.logo_frame.grid(row=0, column=0, padx=20, pady=(30, 20), sticky="ew")

        # Absolute Path Fallback: Finds exactly where this script file lives
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.logo_image_path = os.path.join(script_dir, "logo.jpg")

        if os.path.exists(self.logo_image_path):
            try:
                self.brand_img = ctk.CTkImage(light_image=Image.open(self.logo_image_path),
                                              dark_image=Image.open(self.logo_image_path),
                                              size=(35, 35))
                self.image_label = ctk.CTkLabel(self.logo_frame, image=self.brand_img, text="")
                self.image_label.pack(side="left", padx=(0, 10))
            except Exception as e:
                print(f"Error rendering logo image widget: {e}")
        else:
            # Check the current working directory as a last resort
            fallback_path = "logo.jpg"
            if os.path.exists(fallback_path):
                self.brand_img = ctk.CTkImage(light_image=Image.open(fallback_path),
                                              dark_image=Image.open(fallback_path),
                                              size=(35, 35))
                self.image_label = ctk.CTkLabel(self.logo_frame, image=self.brand_img, text="")
                self.image_label.pack(side="left", padx=(0, 10))
            else:
                print(f"Warning: Could not find 'logo.jpg' at {self.logo_image_path}")

        self.logo_label = ctk.CTkLabel(self.logo_frame, text="KRYPTON", font=ctk.CTkFont(size=26, weight="bold"))
        self.logo_label.pack(side="left")

        # Tabs System Setup
        self.tabview = ctk.CTkTabview(self.sidebar, width=240)
        self.tabview.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.tabview.add("Main")
        self.tabview.add("Settings Config")
        self.tabview.add("Actions")

        # --- TAB 1 ---
        self.sw_tts = ctk.CTkSwitch(self.tabview.tab("Main"), text="Enable TTS", command=self.toggle_tts)
        self.sw_tts.pack(pady=(20, 10), padx=10, anchor="w")

        self.sw_assistant = ctk.CTkSwitch(self.tabview.tab("Main"), text="Voice Assistant Mode",
                                          command=self.toggle_assistant_mode)
        self.sw_assistant.pack(pady=(10, 10), padx=10, anchor="w")

        # --- TAB 2 ---
        self.lbl_person = ctk.CTkLabel(self.tabview.tab("Settings Config"), text="Personality Profile:",
                                       font=ctk.CTkFont(size=13))
        self.lbl_person.pack(pady=(10, 0), anchor="w", padx=10)
        self.opt_person = ctk.CTkOptionMenu(self.tabview.tab("Settings Config"),
                                            values=["Default", "Chill", "Formal", "Brainstormer", "Chaty"],
                                            command=self.change_personality)
        self.opt_person.pack(pady=(5, 10), padx=10, fill="x")

        self.lbl_theme = ctk.CTkLabel(self.tabview.tab("Settings Config"), text="System Theme Color:",
                                      font=ctk.CTkFont(size=13))
        self.lbl_theme.pack(pady=(5, 0), anchor="w", padx=10)
        self.opt_theme = ctk.CTkOptionMenu(self.tabview.tab("Settings Config"),
                                           values=["Vortex", "Pyro", "Terrashock", "Zephyr", "Plasma", "Space", "Void",
                                                   "Heaven"], command=self.change_theme)
        self.opt_theme.pack(pady=(5, 10), padx=10, fill="x")

        self.lbl_rate = ctk.CTkLabel(self.tabview.tab("Settings Config"), text="Speech Engine Speed:",
                                     font=ctk.CTkFont(size=13))
        self.lbl_rate.pack(pady=(5, 0), anchor="w", padx=10)
        self.opt_rate = ctk.CTkOptionMenu(self.tabview.tab("Settings Config"), values=["Slow", "Normal", "Fast"],
                                          command=self.change_speech_rate)
        self.opt_rate.pack(pady=(5, 10), padx=10, fill="x")

        self.lbl_lang = ctk.CTkLabel(self.tabview.tab("Settings Config"), text="Language Pack Accents:",
                                     font=ctk.CTkFont(size=13))
        self.lbl_lang.pack(pady=(5, 0), anchor="w", padx=10)
        self.opt_lang = ctk.CTkOptionMenu(self.tabview.tab("Settings Config"),
                                          values=["English (US)", "Indian English", "Hindi", "Spanish", "Tamil",
                                                  "Telugu"], command=self.change_voice_language)
        self.opt_lang.pack(pady=(5, 20), padx=10, fill="x")

        # --- TAB 3 ---
        self.btn_clear = ctk.CTkButton(self.tabview.tab("Actions"), text="Clear Chat", command=self.clear_chat)
        self.btn_clear.pack(pady=(20, 10), padx=10, fill="x")

        self.btn_export = ctk.CTkButton(self.tabview.tab("Actions"), text="Export Chat Log", command=self.export_chat)
        self.btn_export.pack(pady=(0, 10), padx=10, fill="x")

        self.status_label = ctk.CTkLabel(self.sidebar, text="Status: Idle", font=ctk.CTkFont(size=12, slant="italic"))
        self.status_label.grid(row=3, column=0, pady=(10, 20))

        # --- MAIN CHAT AREA ---
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self.main_frame.grid(row=0, column=1, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)

        self.chat_display = ctk.CTkTextbox(self.main_frame, font=("SF Pro", 18), wrap="word", border_spacing=20)
        self.chat_display.grid(row=0, column=0, sticky="nsew")
        self.chat_display.bind("<Key>", lambda e: "break")

        self.input_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.input_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=20)
        self.input_frame.grid_columnconfigure(0, weight=1)

        self.entry = ctk.CTkEntry(self.input_frame, placeholder_text="Message Krypton...", font=("SF Pro", 16),
                                  height=55)
        self.entry.grid(row=0, column=0, padx=(0, 10), sticky="ew")
        self.entry.bind("<Return>", lambda event: self.send_message())

        self.mic_btn = ctk.CTkButton(self.input_frame, text="◯", width=55, height=55, font=("SF Pro", 24, "bold"),
                                     command=self.toggle_voice_input)
        self.mic_btn.grid(row=0, column=1, padx=(0, 10))

        self.send_btn = ctk.CTkButton(self.input_frame, text="Send", width=90, height=55, font=("SF Pro", 16, "bold"),
                                      command=self.send_message)
        self.send_btn.grid(row=0, column=2)

        self.change_theme("Vortex")
        self.append_chat("System", "Welcome to Krypton Framework V1.2 GUI Dashboard.", "system")

    def change_speech_rate(self, choice):
        global tts_rate
        if choice == "Slow":
            tts_rate = 140
        elif choice == "Fast":
            tts_rate = 230
        else:
            tts_rate = 190
        self.append_chat("System", f"Speech rate engine adjusted to: {choice.lower()}", "system")

    def change_voice_language(self, choice):
        presets = {
            "English (US)": ["en_us", "english", "zira", "david"],
            "Indian English": ["en_in", "india", "heera", "ravi", "veena"],
            "Hindi": ["hi_in", "hindi", "kalpana", "hemant"],
            "Spanish": ["es_es", "es_mx", "spanish", "sabina", "helena"],
            "Tamil": ["ta_in", "tamil", "vani"],
            "Telugu": ["te_in", "telugu", "chitra"]
        }
        target_keys = presets.get(choice, ["english"])
        threading.Thread(target=self._apply_preset_language_worker, args=(target_keys, choice), daemon=True).start()

    def _apply_preset_language_worker(self, target_keys, choice_name):
        global selected_voice_id, tts_engine
        if tts_engine is None:
            return
        found = False
        try:
            voices = tts_engine.getProperty('voices')
            for voice in voices:
                voice_info = f"{voice.name} {voice.id}".lower()
                voice_langs = [str(l).lower() for l in voice.languages] if voice.languages else []
                if any(key in voice_info for key in target_keys) or any(
                        any(key in lang for lang in voice_langs) for key in target_keys):
                    selected_voice_id = voice.id
                    found = True
                    self.after(0, self.append_chat, "System", f"Switched voice engine accent to: {voice.name}",
                               "system")
                    break
            if not found:
                self.after(0, self.append_chat, "System",
                           f"[Note: Voice language pack for '{choice_name}' not detected on this machine.]", "system")
        except Exception as e:
            print(f"Voice selection engine crash: {e}")

    def change_personality(self, choice):
        global modelname, model, chain
        options = {"Default": "def", "Chill": "chill", "Formal": "formal", "Brainstormer": "idea", "Chaty": "chat"}
        modelname = options.get(choice, "def")
        model = OllamaLLM(model=modelname)
        chain = prompt | model
        self.append_chat("System", f"Personality synchronized to: {choice}.", "system")

    def change_theme(self, choice):
        theme = self.themes.get(choice, self.themes["Vortex"])
        text_color = "#000000" if choice == "Heaven" else "#ffffff"

        self.configure(fg_color=theme["bg_main"])
        self.main_frame.configure(fg_color=theme["bg_main"])
        self.chat_display.configure(fg_color=theme["bg_main"])
        self.sidebar.configure(fg_color=theme["bg_sidebar"])
        self.tabview.configure(fg_color=theme["bg_main"])

        self.entry.configure(fg_color=theme["bg_sidebar"], border_color=theme["btn"], text_color=theme["kry_text"])
        self.sw_tts.configure(progress_color=theme["btn"], text_color=theme["kry_text"])
        self.sw_assistant.configure(progress_color=theme["btn"], text_color=theme["kry_text"])

        buttons = [self.send_btn, self.btn_clear, self.btn_export]
        for btn in buttons:
            btn.configure(fg_color=theme["btn"], hover_color=theme["btn_hover"], text_color=text_color)

        if self.status_label.cget("text") not in ["Status: Listening...", "Status: Thinking..."]:
            self.mic_btn.configure(fg_color=theme["btn"], hover_color=theme["btn_hover"], text_color=text_color)

        menus = [self.opt_person, self.opt_theme, self.opt_rate, self.opt_lang]
        for menu in menus:
            menu.configure(fg_color=theme["btn"], button_color=theme["btn_hover"], button_hover_color=theme["btn"],
                           text_color=text_color)

        self.logo_label.configure(text_color=theme["kry_label"])
        self.lbl_person.configure(text_color=theme["kry_label"])
        self.lbl_theme.configure(text_color=theme["kry_label"])
        self.lbl_rate.configure(text_color=theme["kry_label"])
        self.lbl_lang.configure(text_color=theme["kry_label"])
        self.status_label.configure(text_color=theme["kry_text"])

        self.chat_display.tag_config("user", foreground=theme["user"], justify="left")
        self.chat_display.tag_config("kry_label", foreground=theme["kry_label"], justify="left")
        self.chat_display.tag_config("kry_text", foreground=theme["kry_text"], justify="left")
        self.chat_display.tag_config("system", foreground=theme["btn_hover"], justify="left")

    def toggle_tts(self):
        global tts_enabled
        tts_enabled = self.sw_tts.get()

    def toggle_assistant_mode(self):
        self.voice_assistant_mode = self.sw_assistant.get()
        if self.voice_assistant_mode:
            self.sw_tts.select()
            self.toggle_tts()
            self.append_chat("System", "Voice Assistant Mode Enabled.", "system")
            self.toggle_voice_input()
        else:
            self.append_chat("System", "Voice Assistant Mode Disabled.", "system")

    def clear_chat(self):
        global context
        self.chat_display.delete("1.0", "end")
        context = ""
        self.append_chat("System", "Chat logs reset successfully.", "system")

    def export_chat(self):
        filename = f"Krypton_Log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(self.chat_display.get("1.0", "end"))
        self.append_chat("System", f"Chat saved to path: {os.path.abspath(filename)}", "system")

    def update_status(self, status_text):
        self.status_label.configure(text=f"Status: {status_text}")

    def append_chat(self, sender, text, tag, end="\n\n"):
        self.chat_display.insert("end", f"{sender}: ",
                                 tag if sender == "System" else ("user" if sender == "You" else "kry_label"))
        self.chat_display.insert("end", f"{text}{end}", tag)
        self.chat_display.see("end")

    def append_stream(self, text, tag="kry_text"):
        self.chat_display.insert("end", text, tag)
        self.chat_display.see("end")

    def send_message(self, voice_text=None):
        user_text = voice_text if voice_text is not None else self.entry.get().strip()
        if not user_text:
            return

        interrupt_tts()
        self.is_speaking = False

        self.entry.delete(0, "end")
        self.append_chat("You", user_text, "user")

        if user_text.lower() in ["exit", "quit", "bye"]:
            self.append_chat("Krypton", "See you later!", "kry_text")
            speak_text_blocking("See you later!")
            self.after(2000, self.destroy)
            return

        self.disable_input()
        self.update_status("Thinking...")
        threading.Thread(target=self.generate_ai_response, args=(user_text,), daemon=True).start()

    def toggle_voice_input(self):
        if sr is None:
            self.append_chat("System", "SpeechRecognition module not detected.", "system")
            return
        if self.is_speaking:
            return
        self.mic_btn.configure(fg_color="#ef4444", text="⏺")
        self.update_status("Listening...")
        self.disable_input()
        threading.Thread(target=self.process_voice, daemon=True).start()

    def process_voice(self):
        if self.is_speaking:
            self.reset_mic_ui(force_loop_check=self.voice_assistant_mode)
            return
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)
            try:
                audio = recognizer.listen(source, timeout=18, phrase_time_limit=15)
                if self.is_speaking:
                    self.reset_mic_ui(force_loop_check=self.voice_assistant_mode)
                    return
                self.after(0, lambda: self.mic_btn.configure(fg_color="#ef4444", text="⏺"))
                self.update_status("Thinking...")
                text = recognizer.recognize_google(audio)
                self.after(0, lambda: self.entry.delete(0, "end"))
                self.after(0, lambda: self.entry.insert(0, text))
                self.after(100, lambda: self.send_message(voice_text=text))
            except Exception as e:
                self.reset_mic_ui(force_loop_check=self.voice_assistant_mode)

    def reset_mic_ui(self, force_loop_check=False):
        if self.is_speaking:
            return
        self.after(0, self.update_status, "Idle")
        self.after(0, self.enable_input)
        current_theme_name = self.opt_theme.get()
        theme_btn_color = self.themes.get(current_theme_name, self.themes["Vortex"])["btn"]
        text_color = "#000000" if current_theme_name == "Heaven" else "#ffffff"
        self.after(0, lambda: self.mic_btn.configure(fg_color=theme_btn_color, text="◯", text_color=text_color))
        if force_loop_check and self.voice_assistant_mode:
            self.after(1000, self.toggle_voice_input)

    def generate_ai_response(self, user_text):
        global context, chain
        self.chat_display.insert("end", "Krypton: ", "kry_label")
        full_result = ""
        try:
            self.after(0, lambda: self.mic_btn.configure(fg_color="#ef4444", text="⏺"))
            self.update_status("Thinking...")
            for chunk in chain.stream({"context": context, "question": user_text}):
                text_chunk = str(chunk)
                full_result += text_chunk
                self.after(0, self.append_stream, text_chunk)
            self.after(0, lambda: self.chat_display.insert("end", "\n\n"))
            context += f"\nUser: {user_text}\nAI: {full_result}"
            self.is_speaking = True
            self.update_status("Speaking...")
            speak_text_blocking(full_result.strip())
            time.sleep(0.4)
            self.is_speaking = False
            self.reset_mic_ui(force_loop_check=True)
        except Exception as e:
            self.is_speaking = False
            self.reset_mic_ui(force_loop_check=True)

    def disable_input(self):
        self.entry.configure(state="disabled")
        self.send_btn.configure(state="disabled")

    def enable_input(self):
        self.entry.configure(state="normal")
        self.send_btn.configure(state="normal")
        self.entry.focus()


if __name__ == "__main__":
    app = KryptonApp()
    app.mainloop()