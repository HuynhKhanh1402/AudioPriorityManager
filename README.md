# Audio Priority Manager

A Windows application that automatically manages audio volume levels by "ducking" (lowering) other applications when priority audio is playing.

![Python](https://img.shields.io/badge/python-v3.8+-blue.svg)
![Platform](https://img.shields.io/badge/platform-windows-lightgrey.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## ✨ Features

- **Smart Audio Ducking**: Automatically lower volume of other applications when priority audio plays
- **Real-time Monitoring**: Live audio level indicators and status updates
- **Modern GUI**: Dark theme with intuitive controls and tooltips
- **System Tray Integration**: Minimize to tray with notifications
- **Keyboard Shortcuts**: Ctrl+S (Start), Ctrl+T (Stop), Ctrl+M (Minimize)
- **Flexible Configuration**: Customizable thresholds and target processes

## 🚀 Quick Start

### Prerequisites
- Windows 10/11
- Python 3.8 or higher

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/HuynhKhanh1402/AudioPriorityManager.git
   cd AudioPriorityManager
   ```

2. **Run setup**:
   ```bash
   python setup.py
   ```
   Or use the quick setup batch file:
   ```bash
   quick_setup.bat
   ```

3. **Run the application**:
   ```bash
   python app.py
   ```

## 📖 Usage

### Basic Setup
1. **Priority Process**: Enter the name of your priority audio application (e.g., `vlc.exe`, `spotify.exe`)
2. **Duck Volume**: Set the volume level to reduce other apps to (default: 25%)
3. **Activity Threshold**: Minimum audio level to consider as "active" (default: 2%)
4. Click **Start Ducking** to begin

### Advanced Configuration
- **Attack/Release Settings**: Fine-tune when ducking starts and stops
- **Timing Controls**: Adjust responsiveness and smoothness
- **Target Processes**: Optionally limit ducking to specific applications

## ⚙️ Technical Details

### Dependencies
- `PyQt6`: Modern GUI framework
- `pycaw`: Windows Core Audio API wrapper
- `comtypes`: COM interface support

### Project Structure
```
AudioPriority/
├── src/
│   ├── audio_engine.py    # Core audio ducking logic
│   └── gui.py             # PyQt6 user interface
├── app.py                 # Main application entry point
├── requirements.txt       # Python dependencies
├── setup.py              # Installation script
└── README.md             # This file
```

## 🎯 Use Cases

- **Gaming**: Duck Discord/music when game audio plays
- **Streaming**: Auto-lower background music during voice commentary
- **Video Calls**: Reduce notification sounds during meetings
- **Media Production**: Manage multiple audio sources automatically

## 🐛 Troubleshooting

### Common Issues
1. **No audio detected**: Ensure the process name matches exactly (e.g., `chrome.exe` not `Chrome`)
2. **Permissions error**: Run as administrator if needed
3. **GUI doesn't appear**: Check if minimized to system tray

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📋 Requirements

- **OS**: Windows 10/11
- **Python**: 3.8+ (nếu chạy từ source)
- **Audio**: WASAPI-compatible applications (hầu hết app hiện đại)

### Python Dependencies

- `pycaw` - Windows audio control
- `comtypes` - COM interface support  
- `PyQt6` - GUI framework
- `pystray` - System tray support
- `Pillow` - Image processing
- `pyinstaller` - EXE building

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)  
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

## 🙏 Acknowledgments

- **pycaw**: Windows audio control library
- **PyQt6**: Modern GUI framework
- **comtypes**: COM interface support
- Inspired by various audio ducking solutions

---

**Made with ❤️ for Windows audio enthusiasts**
