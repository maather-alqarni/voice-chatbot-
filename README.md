# 🎧 Voice Chatbot — Whisper + Cohere + gTTS

A desktop app with a graphical interface that lets you talk to a chatbot by voice, and get a reply back both as text and speech in real time.

---

## 🧩 Pipeline

```
🎙️ Microphone
      ↓
Whisper (Speech-to-Text)
      ↓
Cohere LLM (Generate Response)
      ↓
gTTS (Text-to-Speech)
      ↓
🔊 Speaker
```

---

## 🛠️ Tools & Libraries Used

| Stage | Tool | Description |
|---|---|---|
| Speech-to-Text (STT) | [OpenAI Whisper](https://github.com/openai/whisper) | A speech recognition model that runs locally on the machine |
| Response Generation (LLM) | [Cohere](https://cohere.com) (model `command-a-03-2025`) | A large language model that generates natural responses via API |
| Text-to-Speech (TTS) | [gTTS](https://pypi.org/project/gTTS/) (Google Text-to-Speech) | Converts the bot's text reply into an MP3 audio file |
| Audio Playback | [playsound](https://pypi.org/project/playsound/) | Automatically plays the resulting audio file |
| Audio Recording | [sounddevice](https://pypi.org/project/sounddevice/) + [scipy](https://scipy.org/) | Records audio from the microphone and saves it as a WAV file |
| Graphical Interface (GUI) | [customtkinter](https://github.com/TomSchimansky/CustomTkinter) | A Python library for building modern, polished desktop interfaces |
| Audio Processing (during setup) | [FFmpeg](https://ffmpeg.org/) | Required by Whisper to process audio files |

---

## 🖥️ What We Built

1. **Built a single Python script** (`chatbot_gui.py`) that combines audio recording, transcription, response generation, and text-to-speech conversion — all inside an interactive loop.
2. **Designed a professional graphical interface** instead of relying on the terminal (Cmd), featuring:
   - A chat window with message bubbles — user messages in blue on the right, bot replies in gray on the left
   - A live status indicator (colored dot: 🟠 loading / 🟢 ready / 🔴 error)
   - A single "Hold to talk" button that records audio for 5 seconds
   - Background model loading (on a separate thread) so the interface doesn't freeze while waiting
3. **Connected the Cohere API** to generate responses, while maintaining conversation history (`chat_history`) so the bot remembers context between messages.
4. **Solved several common technical issues** during setup, including:
   - Installing FFmpeg and adding it to the system PATH
   - An OpenMP library conflict (`KMP_DUPLICATE_LIB_OK`)
   - Output audio filename conflicts (each reply is now saved as a uniquely timestamped MP3 file to avoid "Permission denied" errors)
   - Updating the Cohere model name after an older model was deprecated (`command-r-plus` → `command-a-03-2025`)

---

## ⚙️ Setup & Run

### 1. Set up the environment
```bash
conda create -n voicebot python=3.10
conda activate voicebot
```

### 2. Install FFmpeg
Required for Whisper to work. **Restart your computer** after installing it.

### 3. Install the dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure your Cohere API key
1. Sign up for free at [cohere.com](https://cohere.com)
2. Copy your key from [dashboard.cohere.com/api-keys](https://dashboard.cohere.com/api-keys)
3. Open `chatbot_gui.py` and paste your key here:
   ```python
   COHERE_API_KEY = "YOUR_API_KEY_HERE"
   ```

### 5. Run the app
```bash
python chatbot_gui.py
```

Wait until the status dot turns green (Ready), then press the **"🎙️ Hold to talk"** button and speak.

---
## 🎬 Demo Video
[Watch the demo](https://drive.google.com/file/d/1yMHoOv0fRmZab5oqVQYmTDSp5l9I5YyD/view?usp=sharing))

---

## 📁 Project Structure

```
voice_chatbot/
├── chatbot_gui.py       # Main application (GUI + full pipeline logic)
├── requirements.txt     # All required libraries
└── README.md            # This file
```

---

## 📝 Notes

- Default recording length is 5 seconds — adjustable via `RECORD_SECONDS` in the code.
- Default reply language is Arabic (`REPLY_LANG = "ar"`) — change to `"en"` for English.
- Whisper model size (`WHISPER_MODEL_SIZE = "base"`) can be changed to `tiny` for more speed, or `small`/`medium` for higher accuracy.
