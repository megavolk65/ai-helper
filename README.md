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
- 🌐 **Built-in Browser** — open links from AI responses directly inside the overlay. No more **Alt-Tab** switching!
- ⌨️ **Hotkeys** — quick access from anywhere in the system
- 📷 **Visual Support** — AIgator "sees" your screen (when a screenshot is attached), allowing for ultra-short queries
- 🎯 **App context** — AIgator automatically detects which game/program you are using
- 🔒 **Security** — does not trigger anti-cheats
- 🌍 **Two versions** — international and Russian (works without VPN and foreign cards)

## Quick Start
...
## Usage

1. Press the hotkey to call the overlay
2. Enter your question and press Enter
3. Get an answer from the AI

### Efficiency & Smart Context
AIgator is built to save your time and keep you in the flow:
- **No more Alt-Tab**: Get answers and browse web resources without leaving your game or app.
- **Visual Context**: Attach a screenshot, and AIgator will instantly see what's happening. You can ask "What is this item?" or "How to solve this?" instead of typing long descriptions.
- **Model Quality & Hallucinations**: Remember that AI quality depends on the selected model. AI can sometimes "hallucinate" (provide incorrect info).
- **Verify with Links**: You can ask AIgator for helpful links (guides, wikis, maps) and open them in the **built-in browser** to verify information or see more details.

### With Screenshot
...
## Anti-cheat Safety

The application is **safe** to use with any games:

- ✅ Uses standard Windows overlay (like Discord, Steam)
- ✅ Does not inject into game processes
- ✅ Does not read game memory
- ✅ Does not use DirectX/Vulkan hooks
- ✅ Screenshots via standard Windows API

### Important: Display Mode
For the overlay to appear on top of your game, use **Borderless Window** or **Windowed** mode. The overlay will **not** be visible in **Exclusive Fullscreen** mode.


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
