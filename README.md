[🇬🇧 English](README.md) | [🇷🇺 Русский](README_RU.md)

# <img src="assets/icon_256.png" alt="" width="32"> AIgator

<p align="center">
  <img src="assets/logo.png" alt="AIgator" width="400">
</p>

<p align="center">
  <strong>Universal AI Assistant with Overlay</strong><br>
  Can be called in any application with a hotkey
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue" alt="Python">
  <img src="https://img.shields.io/badge/License-MIT-green" alt="License">
  <img src="https://img.shields.io/badge/Platform-Windows-lightgrey" alt="Platform">
</p>

## Features

- 🎮 **Universal helper** — works in any application (games, browser, IDE)
- 🧠 **Any models** — works with any LLMs compatible with OpenAI API (GPT, Claude, Gemini, Qwen, etc.)
- ⌨️ **Hotkeys** — quick access from anywhere in the system
- 📷 **Screenshot analysis** — AI sees what's on your screen (Vision models)
- 🎯 **App context** — AI knows which game/program you are asking about
- 🔒 **Security** — does not trigger anti-cheats
- 🌍 **Two versions** — international and Russian (works without VPN and foreign cards)

## Quick Start

1. Download and run the application
2. Open settings (⚙️) and select an API provider
3. Enter your API key
4. Add models
5. Done!

## API Providers

### OpenRouter (International)

- 🌐 **Website:** [openrouter.ai](https://openrouter.ai)
- 🔑 **Get key:** [openrouter.ai/keys](https://openrouter.ai/keys)
- 💳 **Payment:** International cards
- ✅ **Free models:** Yes! Models with the `:free` suffix work without payment

### AITunnel (For Russia)

- 🌐 **Website:** [aitunnel.ru](https://aitunnel.ru)
- 🔑 **Get key:** In the personal account after registration
- 💳 **Payment:** Russian cards, rubles
- ⚠️ **No free models**

## Hotkeys

Configurable in settings. Default:

- `PageUp` — Show/hide overlay
- `PageDown` — Take screenshot
- `Escape` — Close overlay

## Usage

1. Press the hotkey to call the overlay
2. Enter your question and press Enter
3. Get an answer from the AI

### With Screenshot

1. Press the screenshot hotkey or the 📷 button in the overlay
2. The screenshot will be attached to the message
3. Enter your question — AI will see what is on the screen

## Anti-cheat Safety

The application is **safe** to use with any games:

- ✅ Uses standard Windows overlay (like Discord, Steam)
- ✅ Does not inject into game processes
- ✅ Does not read game memory
- ✅ Does not use DirectX/Vulkan hooks
- ✅ Screenshots via standard Windows API

## Installation

### Ready-made Installer

Download `AIgator_Setup_x.x.x.exe` from [Releases](https://github.com/megavolk65/AIgator/releases)

### Build from Source

```bash
git clone https://github.com/megavolk65/AIgator.git
cd AIgator
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

### Create EXE and Installer

```bash
pip install pyinstaller
pyinstaller build.spec
# Then compile installer/setup.iss via Inno Setup
```

## License

MIT License

## Author

megavolk65 — [GitHub](https://github.com/megavolk65) • [Telegram](https://t.me/megavolk)
