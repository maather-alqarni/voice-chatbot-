
import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import time
import threading
import queue

import customtkinter as ctk
import whisper
import cohere
from gtts import gTTS
import sounddevice as sd
from scipy.io.wavfile import write
import playsound

# ------------------------------------------------------------------
# CONFIGURATION
# ------------------------------------------------------------------
COHERE_API_KEY = "YOUR_COHERE_API_KEY_HERE"   # <-- put your Cohere API key here
WHISPER_MODEL_SIZE = "base"                    
COHERE_MODEL = "command-a-03-2025"
RECORD_SECONDS = 5
SAMPLE_RATE = 44100
REPLY_LANG = "ar"                              

# ------------------------------------------------------------------
# THEME
# ------------------------------------------------------------------
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

BG_COLOR = "#0f1115"
PANEL_COLOR = "#171a21"
BUBBLE_USER = "#2563eb"
BUBBLE_BOT = "#1f2430"
ACCENT = "#22d3a5"
TEXT_MUTED = "#8b93a7"

FONT_TITLE = ("Segoe UI Semibold", 20)
FONT_BODY = ("Segoe UI", 14)
FONT_SMALL = ("Segoe UI", 11)


class VoiceChatApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Voice Chatbot")
        self.geometry("640x760")
        self.configure(fg_color=BG_COLOR)
        self.minsize(480, 560)

        self.msg_queue = queue.Queue()
        self.is_busy = False
        self.chat_history = []  # Cohere-format chat history
        self.whisper_model = None
        self.cohere_client = None

        self._build_layout()
        self.after(100, self._process_queue)

        # Load heavy models in the background so the UI opens instantly
        threading.Thread(target=self._load_models, daemon=True).start()

    # ----------------------------------------------------------------
    # LAYOUT
    # ----------------------------------------------------------------
    def _build_layout(self):
        # Header
        header = ctk.CTkFrame(self, fg_color=PANEL_COLOR, height=64, corner_radius=0)
        header.pack(side="top", fill="x")
        header.pack_propagate(False)

        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.pack(side="left", padx=20)
        ctk.CTkLabel(title_frame, text="🎧 Voice Chatbot", font=FONT_TITLE,
                     text_color="white").pack(anchor="w", pady=(10, 0))
        self.status_label = ctk.CTkLabel(title_frame, text="Loading models…",
                                          font=FONT_SMALL, text_color=TEXT_MUTED)
        self.status_label.pack(anchor="w")

        self.status_dot = ctk.CTkLabel(header, text="●", font=("Segoe UI", 18),
                                        text_color="#f59e0b")
        self.status_dot.pack(side="right", padx=20)

        # Chat scroll area
        self.chat_frame = ctk.CTkScrollableFrame(self, fg_color=BG_COLOR)
        self.chat_frame.pack(side="top", fill="both", expand=True, padx=10, pady=10)

        self._add_bot_bubble(
            "أهلاً! اضغط زر المايك بالأسفل وتكلم، وبرد عليك صوتيًا ونصيًا."
        )

        # Footer / controls
        footer = ctk.CTkFrame(self, fg_color=PANEL_COLOR, height=110, corner_radius=0)
        footer.pack(side="bottom", fill="x")
        footer.pack_propagate(False)

        self.mic_button = ctk.CTkButton(
            footer, text="🎙️  Hold to talk", font=FONT_BODY,
            fg_color=ACCENT, hover_color="#1cb98d", text_color="#0f1115",
            corner_radius=30, height=52, width=220,
            command=self._on_mic_click, state="disabled",
        )
        self.mic_button.pack(pady=(16, 4))

        self.hint_label = ctk.CTkLabel(
            footer, text=f"Records {RECORD_SECONDS}s of audio each time you press it",
            font=FONT_SMALL, text_color=TEXT_MUTED,
        )
        self.hint_label.pack()

    def _add_user_bubble(self, text):
        self._add_bubble(text, align="e", bg=BUBBLE_USER, text_color="white")

    def _add_bot_bubble(self, text):
        self._add_bubble(text, align="w", bg=BUBBLE_BOT, text_color="white")

    def _add_bubble(self, text, align, bg, text_color):
        row = ctk.CTkFrame(self.chat_frame, fg_color="transparent")
        row.pack(fill="x", pady=6)

        bubble = ctk.CTkLabel(
            row, text=text, font=FONT_BODY, text_color=text_color,
            fg_color=bg, corner_radius=14, wraplength=420,
            justify="right", padx=14, pady=10,
        )
        if align == "e":
            bubble.pack(side="right", padx=(60, 10))
        else:
            bubble.pack(side="left", padx=(10, 60))

        # Auto-scroll to bottom
        self.chat_frame._parent_canvas.yview_moveto(1.0)

    # ----------------------------------------------------------------
    # MODEL LOADING
    # ----------------------------------------------------------------
    def _load_models(self):
        try:
            self.whisper_model = whisper.load_model(WHISPER_MODEL_SIZE)
            self.cohere_client = cohere.Client(COHERE_API_KEY)
            self.msg_queue.put(("ready", None))
        except Exception as e:
            self.msg_queue.put(("error", f"Failed to load models: {e}"))

    # ----------------------------------------------------------------
    # MIC BUTTON HANDLER
    # ----------------------------------------------------------------
    def _on_mic_click(self):
        if self.is_busy:
            return
        self.is_busy = True
        self.mic_button.configure(state="disabled", text="🎙️  Listening…")
        threading.Thread(target=self._run_pipeline, daemon=True).start()

    def _run_pipeline(self):
        try:
            # 1) Record
            audio_file = "input.wav"
            recording = sd.rec(int(RECORD_SECONDS * SAMPLE_RATE),
                                samplerate=SAMPLE_RATE, channels=1)
            sd.wait()
            write(audio_file, SAMPLE_RATE, recording)

            self.msg_queue.put(("status", "Transcribing…"))

            # 2) Speech to text
            result = self.whisper_model.transcribe(audio_file)
            user_text = result["text"].strip()

            if not user_text:
                self.msg_queue.put(("bot", "ما قدرت أسمع شيء، حاول مرة ثانية."))
                self.msg_queue.put(("status", "Ready"))
                self.msg_queue.put(("done", None))
                return

            self.msg_queue.put(("user", user_text))
            self.msg_queue.put(("status", "Thinking…"))

            # 3) LLM response
            response = self.cohere_client.chat(
                message=user_text,
                model=COHERE_MODEL,
                chat_history=self.chat_history,
            )
            bot_reply = response.text.strip()

            self.chat_history.append({"role": "USER", "message": user_text})
            self.chat_history.append({"role": "CHATBOT", "message": bot_reply})

            self.msg_queue.put(("bot", bot_reply))
            self.msg_queue.put(("status", "Speaking…"))

            # 4) Text to speech
            audio_out = f"response_{int(time.time())}.mp3"
            gTTS(text=bot_reply, lang=REPLY_LANG).save(audio_out)
            playsound.playsound(audio_out)

            self.msg_queue.put(("status", "Ready"))

        except Exception as e:
            self.msg_queue.put(("error", str(e)))
        finally:
            self.msg_queue.put(("done", None))

    # ----------------------------------------------------------------
    # QUEUE PROCESSING (runs on the main thread — safe for UI updates)
    # ----------------------------------------------------------------
    def _process_queue(self):
        try:
            while True:
                kind, payload = self.msg_queue.get_nowait()
                if kind == "ready":
                    self.status_label.configure(text="Ready")
                    self.status_dot.configure(text_color="#22c55e")
                    self.mic_button.configure(state="normal", text="🎙️  Hold to talk")
                elif kind == "status":
                    self.status_label.configure(text=payload)
                elif kind == "user":
                    self._add_user_bubble(payload)
                elif kind == "bot":
                    self._add_bot_bubble(payload)
                elif kind == "error":
                    self._add_bot_bubble(f"⚠️ Error: {payload}")
                    self.status_label.configure(text="Error")
                    self.status_dot.configure(text_color="#ef4444")
                elif kind == "done":
                    self.is_busy = False
                    self.mic_button.configure(state="normal", text="🎙️  Hold to talk")
        except queue.Empty:
            pass
        self.after(100, self._process_queue)


if __name__ == "__main__":
    app = VoiceChatApp()
    app.mainloop()
