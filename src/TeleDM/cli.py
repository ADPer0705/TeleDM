"""
cli.py -- Command-line interface for TeleDM
Handles CLI arguments and subcommands (run, config, etc.)
"""

import sys
import argparse
from pathlib import Path

from .utils import LogManager, ConfigManager, get_app_dir, get_config_path
from .configure import main as configure_main


def main():
    """Main CLI entry point for teledm command."""
    parser = argparse.ArgumentParser(
        prog="teledm",
        description="TeleDM - Telegram Download Manager",
        epilog="Run 'teledm config' to configure the application before first use."
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="TeleDM 1.0.0"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Config subcommand
    config_parser = subparsers.add_parser(
        "config",
        help="Configure TeleDM (API credentials, download settings)"
    )
    
    # Run subcommand (optional, same as running with no args)
    run_parser = subparsers.add_parser(
        "run",
        help="Launch the TeleDM GUI (default action)"
    )
    
    # Info subcommand
    info_parser = subparsers.add_parser(
        "info",
        help="Show TeleDM installation and configuration information"
    )
    
    args = parser.parse_args()
    
    # Handle subcommands
    if args.command == "config":
        configure_main()
    elif args.command == "info":
        show_info()
    elif args.command == "run":
        # Run the main application
        from .main import main as app_main
        app_main()
    else:
        parser.print_help()
        sys.exit(1)


def show_info():
    """Display installation and configuration information."""
    print("=" * 60)
    print("TeleDM - Telegram Download Manager")
    print("=" * 60)
    print(f"Version: 1.0.0")
    print(f"Application Directory: {get_app_dir()}")
    print(f"Config File: {get_config_path()}")
    
    config_path = Path(get_config_path())
    if config_path.exists():
        print(f"Config Status: ✓ Exists")
        
        # Try to load config and show basic info
        try:
            cm = ConfigManager()
            tconf = cm.get_telegram_config()
            dconf = cm.get_download_config()
            
            print("\nTelegram Configuration:")
            if tconf and tconf.api_id and tconf.api_hash:
                print(f"  API ID: {tconf.api_id}")
                print(f"  API Hash: {'*' * 8} (configured)")
                print(f"  Phone: {tconf.phone if tconf.phone else 'Not set'}")
            else:
                print("  Status: ⚠ Not configured (run 'teledm config')")
            
            print("\nDownload Configuration:")
            print(f"  Download Path: {dconf.download_path}")
            print(f"  Max Concurrent: {dconf.max_concurrent_downloads}")
            print(f"  Chunk Size: {dconf.chunk_size} bytes")
            print(f"  Retry Attempts: {dconf.retry_attempts}")
            print(f"  Retry Delay: {dconf.retry_delay}s")
        except Exception as e:
            print(f"  Error reading config: {e}")
    else:
        print(f"Config Status: ✗ Not found (run 'teledm config' to create)")
    
    print("=" * 60)
    print("\nUsage:")
    print("  teledm run     - Launch the GUI application")
    print("  teledm config  - Configure API credentials and settings")
    print("  teledm info    - Show this information")
    print("=" * 60)


if __name__ == "__main__":
    main()
