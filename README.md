# 🚀 Telegram Download Manager v1.0.0

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python)
![Tkinter](https://img.shields.io/badge/GUI-Tkinter-FF6B35?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)
[![PyPI version](https://badge.fury.io/py/TeleDM.svg)](https://badge.fury.io/py/TeleDM)

**The "No need to keep the tab in focus" way to download files from Telegram!** 🎉

[📥 Download](#-installation) • [📚 Documentation](#-documentation) • [🐛 Report Issues](https://github.com/ADPer0705/telegram-download-manager/issues)

---

</div>

## ✨ Why Choose Telegram Download Manager?

We've all been there -- You want to download a movie, a project file, a course file, or something that's gonna take a while to download, so you just start the download and leave the tab in focus and go to sleep or lunch or whatever. And if you do not, half the times it just stops downloading soon after it looses focus.

### What TeleDM has to offer
⚡ **Lightning Fast Downloads** - Queue management with progress tracking  
🔄 **Resume Interrupted Downloads** - Never lose progress again  
💾 **Smart Database** - Persistent download history and queue state  
🎨 **Beautiful GUI** - User-friendly interface that just works  

## 🌟 Features

<div align="center">

| Feature | Description |
|---------|-------------|
| 🔑 **API Credentials** | Full access to all your files |
| 📊 **Progress Tracking** | Real-time download progress |
| 🔄 **Resume Downloads** | Continue interrupted downloads |
| 📋 **Queue Management** | Handle multiple downloads efficiently |
| 💾 **Database Storage** | Persistent download history |
| 🛡️ **Error Handling** | Robust retry mechanisms |

</div>

## 🚀 Quick Start & Usage

### 1️⃣ Installation
```bash
make install
```
of for development
```bash
make install-dev
```

### 2️⃣ Configuration
Before the first run, you need to set up your Telegram API credentials.
```bash
# Run the interactive configuration wizard
teledm config
```
You will be prompted for your `API ID`, `API Hash`, and `Phone Number`. See [Getting API Credentials](#-getting-api-credentials) for more details.

### 3️⃣ Running the Application
Once configured, you can launch the GUI:
```bash
# Launch the GUI (default action)
teledm

# Or explicitly:
teledm run
```

### 4️⃣ Command-Line Help
Get help and check your configuration right from the terminal.
```bash
# See all available commands
teledm --help

# Show the installed version
teledm --version

# View current configuration and file paths
teledm info
```

---

## 🔐 Getting API Credentials

TeleDM uses Telegram's official API to access your files. Here's how to get your credentials:

1.  **Visit [my.telegram.org](https://my.telegram.org/)** and log in with your phone number.
2.  Navigate to **"API development tools"**.
3.  Create a new application (you can name it "TeleDM").
4.  Note down your `api_id` and `api_hash`.
5.  Run `teledm config` and enter these credentials when prompted.

**Note:** Your credentials are a secret. They are stored locally in your user data directory and are never shared.

---

## 📍 File Locations

TeleDM stores its configuration, logs, and database in your user's data directory. You can find the exact paths by running `teledm info`.

-   **Configuration File**: `teledmcfg.ini`
-   **Log File**: `teledmlog.log`
-   **Database**: `teledmdb.db`
-   **Session File**: `sessions/`

Typical locations are:
-   **Linux**: `~/.local/share/TeleDM/`
-   **Windows**: `C:\\Users\\<YourUser>\\AppData\\Local\\ADPer\\TeleDM`
-   **macOS**: `~/Library/Application Support/TeleDM/`

---

## 📸 Screenshots

<div align="center">

*Coming soon - beautiful screenshots of the GUI in action!*

</div>

---

## 🏗️ Project Structure

```
telegram-download-manager/
├── src/TeleDM/           # Main package
│   ├── main.py            # GUI application entry point
│   ├── cli.py             # Command-line interface
│   ├── configure.py       # Interactive configuration wizard
│   ├── telegramClient.py  # Telegram API client
│   ├── downloadManager.py # Download queue & progress
│   ├── database.py        # SQLite persistence layer
│   ├── utils.py           # Logging, config, and utilities
│   ├── gui.py             # Tkinter GUI implementation
│   └── __main__.py        # Package entry point
├── docs/                  # Detailed documentation
├── pyproject.toml         # Project metadata & dependencies
└── README.md              # This file
```

---

## 🔧 Advanced Configuration

You can manually edit the `teledmcfg.ini` file (see [File Locations](#-file-locations)) for advanced settings.

```ini
[downloads]
download_path = ~/Downloads          # Where to save files (supports ~ for home directory)
max_concurrent_downloads = 3         # Number of parallel downloads
chunk_size = 1048576                 # Download chunk size in bytes (1MB)
retry_attempts = 5                   # How many times to retry failed downloads
retry_delay = 5                      # Seconds to wait between retries

[logging]
log_level = INFO                     # INFO, WARNING, ERROR
```

---

## 💡 Tips & FAQ

### 🔍 How to Find Chat ID and Message ID

To download a file from Telegram, you need the **Chat ID** and **Message ID**. Here's how to get them:

#### Method 1: Using @userinfobot (Recommended)

1. **Search for `@userinfobot`** on Telegram and start a chat with it.

2. **Get the Chat ID:**
   - Forward any message from the channel/group/chat to `@userinfobot`
   - The bot will reply with information including the Chat ID
   - **Example output:**
     ```
     @offenciveSec
     Id: -1001778292767
     Title: Offensive-SEC
     ```
   - The Chat ID is the number: `-1001778292767` (**include the negative sign!**)

3. **Get the Message ID:**
   - Open the channel in your browser or desktop app
   - Right-click on the message containing the file
   - Look at the message link (e.g., `https://t.me/offenciveSec/1274`)
   - The Message ID is the last number: `1274`

#### Method 2: Using Web Telegram

1. Open [web.telegram.org](https://web.telegram.org)
2. Navigate to the channel/chat with the file
3. Click on the message with the file
4. Look at the URL in your browser: `https://web.telegram.org/k/#-1001778292767_1274`
5. The Chat ID is `-1001778292767` and Message ID is `1274`

#### Important Notes:

- **Chat ID Format:**
  - Public channels: Usually negative numbers like `-1001778292767`
  - Private chats: Positive numbers
  - **Always use the numeric ID, NEVER use the @username**
  
- **Message ID Format:**
  - Just the number (e.g., `1274`)
  - No special characters or prefixes

- **File Name:**
  - The file name is automatically detected from the message
  - You don't need to enter it manually

#### Example in TeleDM:

```
Chat ID: -1001778292767
Message ID: 1274
File Name: [Auto-detected]
```

---

### Common Questions

**Q: Can I download files from private channels?**  
A: Yes, as long as you are a member of that channel. TeleDM accesses Telegram as you, so it can see everything you can.

**Q: Does it resume interrupted downloads?**  
A: Yes! If a download is interrupted, it will automatically resume from where it left off the next time you run the app.

**Q: Where is the configuration file stored?**  
A: Run `teledm info` to see the exact path on your system.

**Q: Is it safe to enter my API credentials?**  
A: Yes. Your credentials are stored locally on your machine and are only used to communicate with Telegram's official servers. They are never sent anywhere else.

**Q: Why am I getting "invalid literal for int()" error?**  
A: You're using the channel username (e.g., `@offenciveSec`) instead of the numeric Chat ID. Use `@userinfobot` to get the correct numeric ID (e.g., `-1001778292767`).

---

## 🛠️ Development

### Requirements
- Python 3.8+
- An active internet connection

### Setup
1.  Fork and clone the repository.
2.  Create a virtual environment.
3.  Install in editable mode with development dependencies:
    ```bash
    pip install -e .
    ```
4.  Run the configuration and the app:
    ```bash
    teledm config
    teledm run
    ```

### Contributing
Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change. Please make sure to update tests as appropriate.

---

## 📈 Roadmap

- [ ] 📸 Add screenshots and demo GIFs
- [ ] � Dark mode and theme support
- [ ] � In-app file search functionality
- [ ] 📊 Download analytics and speed graphs
- [ ] 🌍 Multi-language support

---

## 🤝 Support & Community

<div align="center">

**Need help? Found a bug? Have a suggestion?**

🐛 [Report an Issue](https://github.com/ADPer0705/telegram-download-manager/issues)  
💬 [Start a Discussion](https://github.com/ADPer0705/telegram-download-manager/discussions)  

</div>

---

## 📄 License

<div align="center">

**MIT License** - Free to use, modify, and distribute!

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

</div>

---

<div align="center">

**Made with ❤️ for the Telegram community**

⭐ **Star this repo if you found it useful!**

[⬆️ Back to Top](#-telegram-download-manager)

</div>
