## Frequently Asked Questions

### Authentication Methods

**Q: What are the different ways to authenticate?**

A: As of now any user can only authenticate using API Credentials, but in the future Bot Token Authentication may also be introduced

- **API Credentials** (Full access):
   - Get from https://my.telegram.org/
   - Requires phone verification  
   - Access to all files you can see
   - Best for personal downloads

### Getting API Credentials

**Q: How do I get Telegram API credentials?**

A: Follow these steps:
1. Go to https://my.telegram.org/
2. Login with your phone number
3. Go to "API development tools"
4. Create a new application:
   - App title: Any name (e.g., "My Download Manager")
   - Short name: Any short identifier
   - Platform: Desktop
   - Other fields: Optional
5. Copy the api_id and api_hash to your config.ini

**Q: Are API credentials safe to use?**

A: Yes, but treat them like passwords:
- Never share them publicly
- Don't commit config.ini to version control
- Use them only in trusted applications

### Application Usage

**Q: Can I download multiple files at once?**

A: Yes, the application supports concurrent downloads. Set `max_concurrent_downloads` in config.ini.

**Q: Can I resume interrupted downloads?**

A: Yes, the application automatically resumes interrupted downloads from where they left off.

**Q: Where are files saved?**

A: Files are saved to the directory specified in `download_path` in config.ini (default: ./downloads).

**Q: Can I change the filename?**

A: Yes, enter a custom filename when adding the download, or it will use the original filename.

### Authentication

**Q: Why do I need to enter a verification code?**

A: Telegram requires phone verification for security. This is a one-time setup per device.

**Q: How often do I need to authenticate?**

A: Usually just once. The application saves session data for future use.

**Q: Can I use a bot token instead?**

A: This version uses user authentication. Bot tokens have limited file access compared to user accounts.