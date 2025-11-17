"""
main.py -- entry point for the application
- initializes all components and launches the GUI
"""

from .utils import LogManager, ConfigManager, get_config_path, get_app_dir
from .telegramClient import TelegramClient
from .downloadManager import DownloadManager

# -----------------------------------------------------------------------------
# Entry Point
# -----------------------------------------------------------------------------

def main():
    """Entry point for the TeleDM GUI."""
    # Setup logging first
    LogManager.setup()
    logger = LogManager.get("Main")
    
    logger.info("Starting TeleDM...")
    logger.info("Application directory: " + get_app_dir())
    logger.info("Config file: " + get_config_path())
    
    # Load configuration
    config_manager = ConfigManager()
    
    # Get telegram configuration
    telegram_config = config_manager.get_telegram_config()
    
    # Check if API credentials are configured
    if not telegram_config.api_id or not telegram_config.api_hash or not telegram_config.phone:
        logger.error("API credentials not configured")
        print("\n" + "="*60)
        print("ERROR: Telegram credentials not configured!")
        print("="*60)
        print("\nPlease run 'teledm config' to set up your credentials.")
        print(f"You can also manually edit: {get_config_path()}")
        print("="*60 + "\n")
        return  # Exit instead of launching GUI
    
    # Initialize Telegram client with validated credentials
    telegram_client = TelegramClient(
        api_id=telegram_config.api_id,
        api_hash=telegram_config.api_hash,
        phone=telegram_config.phone,
    )
    
    # Get download configuration
    download_config = config_manager.get_download_config()
    
    # Initialize Download Manager
    config_dict = {
        "download_path": download_config.download_path,
        "max_concurrent_downloads": download_config.max_concurrent_downloads,
        "retry_attempts": download_config.retry_attempts,
        "retry_delay": download_config.retry_delay,
    }
    download_manager = DownloadManager(config_dict, telegram_client)
    
    # Import GUI after logging is set up
    from .gui import TeleDMGUI
    
    # Create and run GUI with initialized components
    try:
        app = TeleDMGUI(config_manager, telegram_client, download_manager)
        logger.info("Launching TeleDM GUI...")
        app.run()
    except Exception as e:
        logger.exception("Error launching the GUI")
        logger.critical("Exiting the application: Unable to launch GUI")
        raise
    
    logger.info("TeleDM GUI closed")


if __name__ == "__main__":
    main()
