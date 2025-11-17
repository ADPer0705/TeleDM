## Troubleshooting

### Installation Issues

**Problem**: "Module not found" errors
**Solution**: 
```bash
pip install -r requirements.txt
```

**Problem**: Python version errors
**Solution**: Ensure you're using Python 3.8 or higher:
```bash
python --version
```

### Authentication Issues

**Problem**: Authentication failed
**Solutions**:
- Double-check api_id and api_hash in config.ini
- Ensure phone number includes country code (+1234567890)
- Verify credentials are valid at my.telegram.org

**Problem**: "Invalid phone number"
**Solution**: Use international format: +[country code][number]

### Download Issues

**Problem**: Downloads failing
**Solutions**:
- Check internet connection
- Verify file ID is correct
- Check logs in logs/telegram_downloader.log
- Increase retry_attempts in config

**Problem**: "File not found"
**Solutions**:
- Verify you have access to the file in Telegram
- Check if file was deleted by sender
- Ensure file ID format is correct

**Problem**: Slow download speeds
**Solutions**:
- Increase chunk_size in config
- Check network connection
- Try downloading at different times

### Permission Issues

**Problem**: Permission denied errors
**Solutions**:
- Ensure download directory is writable
- Check file system permissions
- Try running as administrator (Windows) or with sudo (Linux/Mac)

**Problem**: "Cannot create directory"
**Solution**: Create the download directory manually or check parent directory permissions

### Database Issues

**Problem**: Database errors
**Solutions**:
- Delete downloads.db and restart (loses history)
- Check file permissions on database file
- Ensure SQLite is properly installed