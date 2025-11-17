# TeleDM Command-Line Interface

TeleDM provides a simple and intuitive command-line interface for managing your Telegram downloads.

## Installation

Install TeleDM using pip:

```bash
pip install teledm
```

Or install from source:

```bash
git clone https://github.com/ADPer0705/telegram-download-manager.git
cd telegram-download-manager
pip install .
```

## Quick Start

1. **Configure TeleDM** (first-time setup):
   ```bash
   teledm config
   ```
   
   You'll be prompted to enter:
   - Telegram API ID (get from https://my.telegram.org)
   - Telegram API Hash
   - Phone number (with country code)
   - Download settings (optional, defaults provided)

2. **Run TeleDM**:
   ```bash
   teledm
   ```
   
   This launches the GUI application.

## Available Commands

### `teledm` or `teledm run`
Launch the TeleDM GUI application. This is the default action when running `teledm` without any subcommands.

```bash
teledm
# or
teledm run
```

### `teledm config`
Interactive configuration wizard for setting up API credentials and download preferences.

```bash
teledm config
```

**What it configures:**
- **Telegram Settings:**
  - API ID
  - API Hash
  - Phone Number
  
- **Download Settings:**
  - Download path (default: `~/.local/share/TeleDM/downloads`)
  - Max concurrent downloads (default: 3)
  - Chunk size in bytes (default: 1048576 = 1MB)
  - Retry attempts (default: 5)
  - Retry delay in seconds (default: 5)

**Notes:**
- If a configuration file already exists, you'll be shown the current settings
- You'll be prompted to confirm before overwriting existing configuration
- Press Enter to accept default values (shown in brackets)

### `teledm info`
Display installation and configuration information.

```bash
teledm info
```

**Shows:**
- Version number
- Application directory location
- Configuration file location
- Current Telegram settings status
- Current download settings

### `teledm --help`
Display help information about available commands.

```bash
teledm --help
```

### `teledm --version`
Show the installed version of TeleDM.

```bash
teledm --version
```

## Configuration File Location

TeleDM stores its configuration in a platform-specific location:

- **Linux**: `~/.local/share/TeleDM/teledmcfg.ini`
- **macOS**: `~/Library/Application Support/TeleDM/teledmcfg.ini`
- **Windows**: `%LOCALAPPDATA%\ADPer\TeleDM\teledmcfg.ini`

You can find your exact configuration path by running:
```bash
teledm info
```

## Manual Configuration

You can also manually edit the configuration file. It uses the standard INI format:

```ini
[telegram]
api_id = YOUR_API_ID
api_hash = YOUR_API_HASH
phone = +1234567890

[downloads]
download_path = /path/to/downloads
max_concurrent_downloads = 3
chunk_size = 1048576
retry_attempts = 5
retry_delay = 5
```

## Getting Telegram API Credentials

1. Visit https://my.telegram.org
2. Log in with your phone number
3. Go to "API development tools"
4. Create a new application (if you haven't already)
5. Note down your `api_id` and `api_hash`

## Troubleshooting

### Command not found: teledm
If you get a "command not found" error:

1. Ensure TeleDM is installed: `pip list | grep -i teledm`
2. Check if your pip scripts directory is in PATH:
   ```bash
   python -m site --user-base
   ```
   Add `/bin` (Linux/macOS) or `\Scripts` (Windows) to your PATH

3. Alternatively, run using Python module:
   ```bash
   python -m TeleDM
   ```

### Configuration not persisting
- Check file permissions on the config directory
- Ensure you have write access to the application directory
- Run `teledm info` to verify the config file location

### API errors
- Double-check your API credentials in the config file
- Ensure your phone number includes the country code (e.g., `+1` for USA)
- Verify your API credentials at https://my.telegram.org

## Integration with Development Workflow

For developers working on TeleDM:

```bash
# Install in editable mode
pip install -e .[dev]

# The teledm command will now use your local development code
teledm config
teledm info
```

## Examples

**First-time setup:**
```bash
$ teledm config
Empty configuration file created at: /home/user/.local/share/TeleDM/teledmcfg.ini
Please answer the configuration prompts below:
Hit Enter to accept default values shown in [brackets].

--- Telegram Configuration ---
Enter your Telegram API ID: 12345678
Enter your Telegram API Hash: abc123def456...
Enter your Telegram Phone Number: +1234567890

--- Download Configuration ---
Enter download path [/home/user/.local/share/TeleDM/downloads]: 
Enter max concurrent downloads [3]: 5
...
```

**Check current configuration:**
```bash
$ teledm info
============================================================
TeleDM - Telegram Download Manager
============================================================
Version: 0.1.0
Application Directory: /home/user/.local/share/TeleDM
Config File: /home/user/.local/share/TeleDM/teledmcfg.ini
Config Status: ✓ Exists

Telegram Configuration:
  API ID: 12345678
  API Hash: ******** (configured)
  Phone: +1234567890
...
```

**Launch the application:**
```bash
$ teledm
# GUI window opens
```

## See Also

- [Configuration Guide](Configuration.md) - Detailed configuration options
- [Usage Guide](Usage.md) - How to use the GUI
- [FAQ](FAQ.md) - Frequently asked questions
- [Troubleshooting](TroubleShooting.md) - Common issues and solutions
