# 🎵 SoundBoard Manager - Lightweight Volume Mixer

**Pure Python** - Ultra-lightweight volume control that replaces heavy Electron apps

![License](https://img.shields.io/badge/license-MIT-green.svg)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Size](https://img.shields.io/badge/size-%3C5MB-brightgreen.svg)

## ✨ Features

- 🎚️ **Per-Application Volume Control** - Control volume for each application independently
- ⌨️ **Media Key Integration** - Use multimedia keys (Volume Up/Down) to control audio
- 🎨 **Modern Overlay UI** - Sleek, transparent overlay with smooth fade animations
- 🖱️ **True Click-Through** - Overlay never interferes with your work
- 🌍 **Multi-Language Support** - 10 languages with automatic download from GitHub
- 📍 **9 Screen Positions** - Place overlay anywhere on screen
- 🔇 **Mute Indicator** - Visual feedback when applications are muted
- 🎯 **App Icon Detection** - Automatically shows icons for each application
- 💾 **Persistent Settings** - Configuration saved locally
- 🪶 **Lightweight** - No Electron, no Node.js, pure Python
- 🖼️ **System Tray** - Minimal background presence with system tray icon

## 📸 Screenshots

(/src/assets/example.png)

## 🚀 Quick Start

### Prerequisites

- Windows 10/11
- Python 3.8 or higher

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/seerrgiioo/SoundBoard-Manager.git
   cd SoundBoard-Manager
   ```

2. **Create virtual environment (recommended)**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python -m src
   ```

## 🔧 Development

### Project Structure

```
SoundBoard-Manager/
├── src/
│   ├── __main__.py         # Application entry point
│   ├── backend.py          # Audio session management (pycaw)
│   ├── media_wheel.py      # Media key interception
│   ├── ui_qt.py            # PySide6 overlay UI
│   ├── i18n.py             # Internationalization system
│   └── assets/
│       ├── icon.png        # Application icon
│       ├── icon.ico        # Windows icon
│       └── noicon.png      # Fallback icon
├── i18n/                   # Language files (upload to GitHub)
│   ├── es.json
│   ├── en.json
│   ├── fr.json
│   └── ...
├── requirements.txt        # Python dependencies
└── README.md
```

### Key Components

- **backend.py**: Audio session control using Windows Core Audio API (pycaw)
- **media_wheel.py**: Global keyboard hook for media keys with suppression
- **ui_qt.py**: Qt-based overlay with click-through capabilities
- **i18n.py**: Automatic language download and caching system

### Building for Production

```bash
# Install PyInstaller
pip install pyinstaller

# Build executable
pyinstaller --onefile --windowed --icon=src/assets/icon.ico --name=SoundBoardManager -m src

# Output will be in dist/
```

## 🎮 Usage

### Media Keys

- **Volume Up/Down** - Adjust volume of currently playing application
- **Overlay Display** - Automatically appears when adjusting volume
- **Auto-Hide** - Overlay fades out after 3 seconds of inactivity

### System Tray

Right-click the tray icon to access:
- **Show/Hide** - Manually toggle overlay visibility
- **Settings** - Open configuration dialog
- **Exit** - Close application

### Configuration

The settings dialog allows you to customize:

#### Screen Position (9 options)
- Top: Left, Center, Right
- Middle: Left, Center, Right  
- Bottom: Left, Center, Right

#### Language Selection
Choose from 10 supported languages:
- 🇪🇸 Español
- 🇬🇧 English
- 🇫🇷 Français
- 🇩🇪 Deutsch
- 🇮🇹 Italiano
- 🇧🇷 Português
- 🇯🇵 日本語
- 🇨🇳 中文
- 🇰🇷 한국어
- 🇷🇺 Русский

## 🌍 Internationalization

The application uses a smart i18n system:
1. **First run**: Downloads language files from GitHub
2. **Local cache**: Stores downloaded languages in `%LOCALAPPDATA%\SoundBoard Manager\i18n\`
3. **Offline mode**: Uses cached files when internet is unavailable
4. **Fallback**: Built-in Spanish and English translations

## 🛠️ Technologies

### Core
- **Python 3.8+** - Main language
- **PySide6** - Qt6 bindings for UI
- **pycaw** - Windows Core Audio wrapper
- **keyboard** - Global keyboard hooks
- **comtypes** - COM interface for Windows APIs

### Additional Libraries
- **psutil** - Process information
- **Pillow** - Image handling for icons
- **pywin32** - Windows API access
- **pystray** - System tray integration

## 🤝 Contributing

Contributions are welcome! Areas for improvement:

### Adding Languages
1. Copy `i18n/es.json` as a template
2. Translate all strings to your language
3. Name the file with ISO 639-1 code (e.g., `it.json`)
4. Submit a Pull Request

### Code Contributions
1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚡ Performance

| Metric | Electron Version | Python Version |
|--------|-----------------|----------------|
| Memory Usage | ~150MB | ~30MB |
| Disk Size | ~200MB | ~5MB |
| Startup Time | ~3s | <1s |
| CPU Idle | ~1% | ~0.1% |

## 🐛 Known Issues

- Threading warnings on first launch (harmless, will be fixed)
- Some UWP apps may not expose volume controls
- Icon extraction may fail for some system processes

## 🔮 Roadmap

- [ ] Custom keyboard shortcuts
- [ ] Volume presets per application
- [ ] Application whitelist/blacklist
- [ ] Custom themes and colors
- [ ] Hotkey recording for shortcuts
- [ ] Multiple monitor support
- [ ] Audio device switching
- [ ] Portable mode (no installation)

## 📧 Support

For questions, issues, or feature requests:
- Open an issue on [GitHub Issues](https://github.com/seerrgiioo/SoundBoard-Manager/issues)
- Check existing issues before creating new ones

## 🙏 Acknowledgments

- [pycaw](https://github.com/AndreCNF/pycaw) - Python Core Audio Windows Library
- [PySide6](https://www.qt.io/qt-for-python) - Qt for Python
- [keyboard](https://github.com/boppreh/keyboard) - Hook and simulate keyboard events
- All contributors and translators

---

**Made by seerrgiioo with ❤️ and Python** 


