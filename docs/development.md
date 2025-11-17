## Development

### Code Structure

```
main.py                 # GUI application entry point
├── TelegramDownloadManagerGUI class
    ├── GUI setup and event handling
    ├── Telegram client integration
    └── Download manager coordination

telegram_client.py      # Telegram API wrapper
├── TelegramClient class
    ├── Authentication handling
    ├── File download methods
    └── Error handling

download_manager.py     # Download queue management
├── DownloadManager class
    ├── Queue processing
    ├── Progress tracking
    └── Retry logic

database.py            # Data persistence
├── Database class
    ├── SQLite operations
    ├── Download history
    └── Queue state

config_manager.py      # Configuration handling
├── ConfigManager class
    ├── Config file parsing
    ├── Default values
    └── Validation

logger.py              # Logging setup
├── Logger class
    ├── File logging
    ├── Console output
    └── Log rotation
```

### Adding Features

1. **New Download Sources**: Extend TelegramClient
2. **UI Improvements**: Modify TelegramDownloadManagerGUI
3. **Database Changes**: Update Database class and migrations
4. **Configuration**: Add options to ConfigManager

### Testing

Run basic import test:
```bash
python -c "import main; print('✓ Success')"
```

### Debugging

Enable debug logging in config.ini:
```ini
[logging]
log_level = DEBUG
```

Check logs for detailed information:
```bash
tail -f logs/telegram_downloader.log
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes following the existing code style
4. Test thoroughly
5. Submit a pull request