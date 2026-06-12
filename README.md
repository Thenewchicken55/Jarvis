# Jarvis - Voice-Controlled AI Assistant

A privacy-first, locally-hosted AI assistant inspired by Iron Man's Jarvis. Supports voice interaction, keyboard automation, and chat — powered by Ollama, OpenAI, Anthropic, or local GGUF models.

## Features

- **Voice Assistant Mode** - Push-to-talk voice control, just like Jarvis
- **Speech-to-Text** - Speak naturally, get transcribed (Google STT or Whisper)
- **Text-to-Speech** - Hear responses spoken back to you
- **Keyboard Automation** - Ask Jarvis to type on your keyboard
- **Multi-Provider LLM** - Choose from Ollama (local), OpenAI, Anthropic, or local GGUF models
- **Streamlit Chat UI** - Classic web chat interface also included
- **Conversation Memory** - Remembers context across turns
- **Fully Offline Options** - Use local models + offline TTS/STT for complete privacy

## Quick Start

### Prerequisites

- Python 3.10+
- For Ollama mode: [Ollama](https://ollama.com) installed and running with a model pulled (e.g., `ollama pull llama3.2`)
- For voice mode: A working microphone

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/Jarvis
cd Jarvis

# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# (Optional) For local Whisper STT:
pip install faster-whisper

# (Optional) For edge-tts (better voice quality):
pip install edge-tts
```

### Run the Voice Assistant (Jarvis Mode)

```bash
python jarvis.py
```

Push-to-talk: Hold the **Spacebar**, speak your command, release. Jarvis will process and respond.

### Run the Web Chat UI

```bash
streamlit run app.py
```

### Keyboard Control

Jarvis can type on your keyboard or press key combos. Just ask:

| Say this | What happens |
|---|---|
| "Type hello world" | Jarvis types "hello world" wherever your cursor is |
| "Press ctrl+c" | Jarvis presses Ctrl+C |
| "Type an email saying I'm running late, meeting at 3" | Jarvis types the full message |
| "Open notepad and write a shopping list" | Jarvis switches to Notepad and types the list |
| "Press enter" | Jarvis presses the Enter key |

Jarvis uses `[TYPE]` and `[KEY]` markers in its responses to trigger keyboard actions — the marker text is stripped before speaking, so you only hear the natural response while the typing happens silently.

## Configuration

Edit `config.yaml` to customize:

### LLM Provider

```yaml
llm:
  provider: "ollama"  # Choose: ollama, openai, anthropic, local

  # Ollama (local, default) — requires `ollama` running
  ollama:
    model: "llama3.2"
    base_url: "http://localhost:11434"
    temperature: 0.7
    max_tokens: 2048

  # OpenAI — requires API key
  openai:
    model: "gpt-4o"
    api_key: "sk-..."       # Set via OPENAI_API_KEY env var or here
    temperature: 0.7
    max_tokens: 2048

  # Anthropic — requires API key
  anthropic:
    model: "claude-sonnet-4-20250514"
    api_key: "sk-ant-..."   # Set via ANTHROPIC_API_KEY env var or here
    temperature: 0.7
    max_tokens: 2048

  # Local GGUF — requires a .gguf model file
  local:
    model_path: "models/mistral-7b-instruct.Q5_K_M.gguf"
    model_type: "mistral"
    gpu_layers: 0
    temperature: 0.7
    max_tokens: 2048
```

### Voice Settings

```yaml
voice:
  stt_engine: "speech_recognition"  # speech_recognition (Google free), whisper
  tts_engine: "pyttsx3"            # pyttsx3 (offline), edge_tts (online, better)
  language: "en-US"
  push_to_talk_key: "space"        # Hotkey to hold while speaking
```

### Keyboard Automation

```yaml
keyboard:
  enabled: true
  typing_speed: 0.05  # Seconds between keystrokes (lower = faster)
```

## Usage Examples

### Voice Assistant

| Say this | Action |
|---|---|
| "What's the weather today?" | Jarvis responds verbally |
| "Type a message saying I'll be late" | Jarvis types on your keyboard |
| "Open notepad and write a todo list" | Jarvis types the todo list |
| "Tell me a joke" | Jarvis tells a joke with voice |

### Chat UI

Open `http://localhost:8501` after running `streamlit run app.py` to get the text-based interface.

## Project Structure

```
Jarvis/
├── jarvis.py            # Voice assistant main loop (push-to-talk)
├── app.py               # Streamlit web chat UI
├── llm_chains.py        # Multi-provider LLM abstraction
├── prompt_templates.py  # Prompt templates
├── audio_utils.py       # Speech-to-text & text-to-speech
├── keyboard_agent.py    # Keyboard automation
├── config.yaml          # Configuration
├── requirements.txt     # Dependencies
└── README.md            # This file
```

## Troubleshooting

### "No module named 'pyttsx3'"
```bash
pip install pyttsx3
```

### "Microphone not working"
- On Windows: Check privacy settings (Settings > Privacy > Microphone)
- On Linux: `sudo apt install portaudio19-dev python3-pyaudio`
- On Mac: `brew install portaudio`

### "Ollama connection refused"
- Ensure Ollama is running: `ollama serve`
- Check the base_url in config.yaml (default: http://localhost:11434)

### "push_to_talk_key not working"
- Some terminals capture the space key. Try a different key like "ctrl" or "shift" in config
- Run `python jarvis.py` directly (not inside another program)

## License

MIT
