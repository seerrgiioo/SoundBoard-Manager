# 🎵 SoundBoard Manager

A powerful Windows application for per-application volume control with keyboard shortcuts. Control individual application volumes without touching your mouse.

![License](https://img.shields.io/badge/license-Non--Commercial-orange.svg)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Electron](https://img.shields.io/badge/electron-28.0.0-blue.svg)

## ✨ Features

- 🎚️ **Per-Application Volume Control** - Adjust volume for individual applications independently
- ⌨️ **Keyboard Shortcuts** - Use your volume keys to control app volumes
- 🔄 **Navigation Mode** - Switch between applications using volume keys
- 🎨 **Modern UI** - Clean, transparent overlay with smooth animations
- 🌍 **Multi-Language** - Supports 20+ languages
- 🚀 **Auto-Start** - Launches on system startup
- 💾 **Persistent Settings** - Remembers your preferences and window position
- 🎯 **Smart Icon Detection** - Automatically extracts application icons with transparency

## 📸 Screenshots

*Coming soon*

## 🚀 Quick Start

### Prerequisites

- Windows 10/11
- Python 3.8 or higher
- Node.js 16 or higher

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/seerrgiioo/soundboard-manager.git
   cd soundboard-manager
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Node.js dependencies**
   ```bash
   cd src
   npm install
   ```

4. **Run the application**
   ```bash
   npm start
   ```

## 🔧 Development

### Project Structure

```
soundboard-manager/
├── src/
│   ├── backend.py          # Python backend (audio control)
│   ├── main.js             # Electron main process
│   ├── ui/                 # Frontend UI
│   │   ├── index.html
│   │   ├── script.js
│   │   └── styles.css
│   ├── i18n/               # Translations
│   └── assets/             # Icons and resources
├── requirements.txt        # Python dependencies
└── package.json           # Node.js configuration
```

### Building for Production

1. **Build Python backend**
   ```bash
   pyinstaller --onefile --windowed --icon=src/assets/icon.ico src/backend.py
   ```

2. **Build Electron app**
   ```bash
   cd src
   npm run build
   ```

The built application will be in `src/dist/`.

## 🎮 Usage

### Default Keyboard Shortcuts

- **Volume Up/Down** - Adjust volume of the selected application (default mode)
- **Volume Mute** - Toggle navigation mode
- **Volume Up/Down** (in navigation mode) - Switch between applications

### Configuration

Access settings by right-clicking the system tray icon and selecting "Settings".

Available options:
- **Position** - Choose where the overlay appears on screen
- **Opacity** - Adjust window transparency (20-100%)
- **Volume Delta** - Set volume change increment (1-20%)
- **Language** - Select your preferred language

## 🌍 Supported Languages

Arabic (ar), Bengali (bn), German (de), English (en), Spanish (es), French (fr), Hindi (hi), Indonesian (id), Italian (it), Japanese (ja), Korean (ko), Marathi (mr), Portuguese (pt), Russian (ru), Swahili (sw), Telugu (te), Turkish (tr), Urdu (ur), Vietnamese (vi), Chinese (zh)

## 🛠️ Technologies

### Backend
- **Python 3.8+** - Core audio control logic
- **pycaw** - Windows audio session management
- **keyboard** - Global keyboard hook
- **websockets** - Real-time communication
- **psutil** - Process information
- **Pillow & NumPy** - Icon extraction and processing

### Frontend
- **Electron 28** - Cross-platform desktop framework
- **Node.js** - JavaScript runtime
- **WebSockets** - Real-time UI updates
- **HTML5/CSS3** - Modern UI design

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under a **Non-Commercial License**. You are free to use, modify, and distribute this software for non-commercial purposes only. Commercial use is strictly prohibited.

See the [LICENSE](LICENSE) file for full details.

## 🐛 Known Issues

- Master volume override may not work on some Windows configurations
- Some applications may not report accurate volume levels

## 🔮 Future Enhancements

- [ ] Custom keyboard shortcuts
- [ ] Profiles for different scenarios
- [ ] Volume presets
- [ ] Application whitelist/blacklist
- [ ] Hotkey recording
- [ ] macOS and Linux support

## 📧 Contact

For questions or support, please open an issue on GitHub.

## 🙏 Acknowledgments

- [pycaw](https://github.com/AndreCNF/pycaw) - Python Core Audio Windows Library
- [Electron](https://www.electronjs.org/) - Build cross-platform desktop apps
- All contributors who have helped improve this project

---

Made with ❤️ by seerrgiioo

