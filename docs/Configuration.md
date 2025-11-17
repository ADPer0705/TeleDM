# Configuration
We are using a config.ini file for storing the User's
- preferences
- credentials
The location of the file depends on the OS (it is in the user's data directory which is platform agnostic) so it is recommended to either use the UI for editing the configs

>[!NOTE]
> For this version, we're yet to implement the UI for managing configs, so unfortunately you'll have to write directly to the file

You can see the logs when you launch the application, there will be a line

```log
Config loaded from: /home/user/.local/share/TeleDM/teledmcfg.ini
```

```python
# since this a python tool, it is assumed python is installed
# you can find the application directory with the following command

python -c "import platformdirs; print(platformdirs.user_data_dir('TeleDM', 'ADPer'))"
```

## Basic Configuration

**API Credentials**
```ini
[telegram]
api_id = YOUR_API_ID
api_hash = YOUR_API_HASH
phone = YOUR_PHONE_NUMBER
```

**Downloads Preferences**
```ini
[downloads]
download_path = downloads/
max_concurrent_downloads = 3
chunk_size = 1048576
retry_attempts = 5
retry_delay = 5
```

> It should be noted that the values used above are also the default configuration values.



### Configuration Options

| Section | Option | Description | Default | Type |
|---------|--------|-------------|---------|------|
| telegram | api_id | Your Telegram API ID | Required | int |
| telegram | api_hash | Your Telegram API Hash | Required | string |  
| telegram | phone | Phone number with country code | Required | string |
| downloads | download_path | Directory to save downloads | ./downloads | string |
| downloads | max_concurrent_downloads | Maximum simultaneous downloads | 3 | int |
| downloads | chunk_size | Download chunk size in bytes | 1048576 | int |
| downloads | retry_attempts | Number of retry attempts | 5 | int |
| downloads | retry_delay | Delay between retries in seconds | 5 | int |
| logging | log_level | Logging level | INFO | string |
| logging | log_file | Log file path | logs/telegram_downloader.log | string |

NOTE
- setting `retry_attempts` or `max_concurrent_downloads` to `0` will lead to the software assuming 

    "There are no upper bounds for `retry_attempts` and `max_concurrent_download` from the user's end.

### Advanced Configuration

- **Chunk Size**: Larger chunks (e.g., 2MB) may improve speed but use more memory
- **Concurrent Downloads**: More concurrent downloads may saturate bandwidth
- **Retry Settings**: Adjust based on your network stability

