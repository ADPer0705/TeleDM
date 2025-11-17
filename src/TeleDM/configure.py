import platformdirs
from pathlib import Path
import configparser

# --------------------------
# Constants / Defaults
# --------------------------
APP_NAME = "TeleDM"
APP_AUTHOR = "ADPer"
CONFIG_FILE_NAME = "teledmcfg.ini"
DOWNLOAD_DIR_NAME = "downloads"

DEFAULT_MAX_LOG_BYTES = 5 * 1024 * 1024  # 5 MB
DEFAULT_LOG_BACKUP_COUNT = 5

def main():                 #TODO: integrate into main application flow
    """Function to configure user settings."""

    p = Path(platformdirs.user_data_dir(APP_NAME, APP_AUTHOR)) / CONFIG_FILE_NAME
    p.parent.mkdir(parents=True, exist_ok=True)
    
    if not p.exists() or p.stat().st_size == 0:

        template = configparser.ConfigParser()
        template["telegram"] = {
                "api_id": None,
                "api_hash": None,
                "phone": None
        }
        template["downloads"] = {
            "download_path": str(Path.home() / DOWNLOAD_DIR_NAME),
            "max_concurrent_downloads": "3",
            "chunk_size": str(1 * 1024 * 1024),
            "retry_attempts": "5",
            "retry_delay": "5",
        }
        with open(p, "w", encoding="utf-8") as fh:
            template.write(fh)

        print(f"Empty configuration file created at: {str(p)}")
    else:
        print(f"Configuration file already exists at: {str(p)}")
        print("Here are the current settings:\n")
        config = configparser.ConfigParser()
        config.read(p, encoding="utf-8")
        for section in config.sections():
            print(f"[{section}]")
            for key, value in config[section].items():
                print(f"{key} = {value}")
            print()
        overwrite = input("Do you want to overwrite the existing configuration? (y/N): ")
        if overwrite.lower() != 'y':
            print("Exiting without changes.")
            return
        
    print("Please answer the configuration prompts below:")
    print("Hit Enter to accept default values shown in [brackets].\n")
    config = configparser.ConfigParser()
    config.read(p, encoding="utf-8")
    
    # Telegram Config
    print("\n--- Telegram Configuration ---")
    api_id = input("Enter your Telegram API ID (get it from https://my.telegram.org): ")
    api_hash = input("Enter your Telegram API Hash: ")
    phone = input("Enter your Telegram Phone Number (with country code, e.g., +1234567890): ")
    config["telegram"]["api_id"] = api_id
    config["telegram"]["api_hash"] = api_hash
    config["telegram"]["phone"] = phone

    # Download Config
    print("\n--- Download Configuration ---")
    download_path = input(f"Enter download path [{str(Path.home() / DOWNLOAD_DIR_NAME)}]: ") or str(Path.home() / DOWNLOAD_DIR_NAME)
    max_concurrent_downloads = input("Enter max concurrent downloads [3]: ") or "3"
    chunk_size = input("Enter chunk size in bytes [1048576]: ") or str(1 * 1024 * 1024)
    retry_attempts = input("Enter number of retry attempts [5]: ") or "5"
    retry_delay = input("Enter delay between retries in seconds [5]: ") or "5"
    config["downloads"]["download_path"] = download_path
    config["downloads"]["max_concurrent_downloads"] = max_concurrent_downloads
    config["downloads"]["chunk_size"] = chunk_size
    config["downloads"]["retry_attempts"] = retry_attempts
    config["downloads"]["retry_delay"] = retry_delay

    with open(p, "w", encoding="utf-8") as fh:
        config.write(fh)
    print(f"\nConfiguration saved to: {str(p)}")

if __name__ == "__main__":
    main()