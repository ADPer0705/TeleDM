"""
gui.py — Tkinter GUI for TeleDM (Telegram Download Manager)

Features:
- Modern async/await integration with Tkinter
- Clean UI for managing Telegram downloads
- Real-time progress tracking and speed monitoring
- Supports chat_id + message_id based downloads (Telethon)
"""

from __future__ import annotations

import atexit
import asyncio
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from typing import Optional

from .utils import LogManager, ConfigManager
from .telegramClient import TelegramClient
from .downloadManager import DownloadManager

class TeleDMGUI:
    """Main GUI application for Telegram Download Manager."""

    def __init__(self, config_manager: ConfigManager, telegram_client: TelegramClient, download_manager: DownloadManager):
        self.logger = LogManager.get("GUI")

        # Core components (all initialized in main.py)
        self.config_manager = config_manager
        self.telegram_client = telegram_client
        self.download_manager = download_manager

        # Async event loop (runs in background thread)
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.loop_thread: Optional[threading.Thread] = None

        # Create main window
        self.root = tk.Tk()
        self.root.title("TeleDM - Telegram Download Manager")
        self.root.geometry("900x700")
        self.root.minsize(700, 500)

        # Style
        self.style = ttk.Style()
        self.style.theme_use("clam")

        # Variables
        self.status_var = tk.StringVar(value="Not connected")
        self.download_path_var = tk.StringVar()

        # Tree item → file_id mapping
        self.tree_file_id_map = {}

        # Auto-refresh job
        self.refresh_job = None

        # Build UI
        self._create_ui()
        self._load_config()

    # -------------------------------------------------------------------------
    # UI CONSTRUCTION
    # -------------------------------------------------------------------------

    def _create_ui(self):
        """Build the entire GUI."""
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.grid(row=0, column=0, sticky="nsew")

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(4, weight=1)

        # --- Status Frame ---
        status_frame = ttk.LabelFrame(main_frame, text="Status", padding=10)
        status_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        ttk.Label(status_frame, text="Connection:").pack(side="left")
        ttk.Label(status_frame, textvariable=self.status_var).pack(side="left", padx=10)

        self.connect_btn = ttk.Button(status_frame, text="Connect", command=self._on_connect)
        self.connect_btn.pack(side="left", padx=10)

        # --- Download Path ---
        path_frame = ttk.LabelFrame(main_frame, text="Download Path", padding=10)
        path_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        path_frame.columnconfigure(1, weight=1)

        ttk.Label(path_frame, text="Path:").grid(row=0, column=0, sticky="w")
        ttk.Entry(path_frame, textvariable=self.download_path_var).grid(
            row=0, column=1, sticky="ew", padx=10
        )
        ttk.Button(path_frame, text="Browse", command=self._browse_path).grid(row=0, column=2)

        # --- Add Download ---
        add_frame = ttk.LabelFrame(main_frame, text="Add Download", padding=10)
        add_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        add_frame.columnconfigure(1, weight=1)

        ttk.Label(add_frame, text="Chat ID:").grid(row=0, column=0, sticky="w", pady=2)
        self.chat_id_entry = ttk.Entry(add_frame)
        self.chat_id_entry.grid(row=0, column=1, sticky="ew", padx=(10, 10), pady=2)

        ttk.Label(add_frame, text="Message ID:").grid(row=1, column=0, sticky="w", pady=2)
        self.msg_id_entry = ttk.Entry(add_frame)
        self.msg_id_entry.grid(row=1, column=1, sticky="ew", padx=(10, 10), pady=2)

        ttk.Label(add_frame, text="File Name:").grid(row=2, column=0, sticky="w", pady=2)
        self.file_name_entry = ttk.Entry(add_frame)
        self.file_name_entry.grid(row=2, column=1, sticky="ew", padx=(10, 10), pady=2)

        ttk.Button(add_frame, text="Add Download", command=self._add_download).grid(
            row=0, column=2, rowspan=3, padx=(5, 0), sticky="ns"
        )

        # --- Controls ---
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=3, column=0, sticky="ew", pady=(0, 10))

        ttk.Button(control_frame, text="Refresh", command=self._refresh_downloads).pack(
            side="left", padx=5
        )
        ttk.Button(control_frame, text="Clear Completed", command=self._clear_completed).pack(
            side="left", padx=5
        )

        # --- Downloads List ---
        list_frame = ttk.LabelFrame(main_frame, text="Downloads", padding=10)
        list_frame.grid(row=4, column=0, sticky="nsew", pady=(0, 10))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        columns = ("file_name", "status", "progress", "speed")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="tree headings", height=10)

        self.tree.heading("#0", text="ID")
        self.tree.column("#0", width=80, minwidth=80)

        self.tree.heading("file_name", text="File Name")
        self.tree.column("file_name", width=300, minwidth=150)

        self.tree.heading("status", text="Status")
        self.tree.column("status", width=100, minwidth=80)

        self.tree.heading("progress", text="Progress")
        self.tree.column("progress", width=100, minwidth=80)

        self.tree.heading("speed", text="Speed")
        self.tree.column("speed", width=100, minwidth=80)

        v_scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        h_scroll = ttk.Scrollbar(list_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")

        # Context menu
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Cancel", command=self._cancel_selected)
        self.context_menu.add_command(label="Retry", command=self._retry_selected)
        self.context_menu.add_command(label="Remove", command=self._remove_selected)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Open Folder", command=self._open_folder)

        self.tree.bind("<Button-3>", self._show_context_menu)

        # --- Log ---
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding=10)
        log_frame.grid(row=5, column=0, sticky="ew")
        log_frame.columnconfigure(0, weight=1)

        self.log_text = scrolledtext.ScrolledText(log_frame, height=6, state="disabled")
        self.log_text.grid(row=0, column=0, sticky="ew")

    def _load_config(self):
        """Load config and populate UI."""
        try:
            dconf = self.config_manager.get_download_config()
            self.download_path_var.set(dconf.download_path)
            self._log("Configuration loaded successfully.")
        except Exception as e:
            self._log(f"Error loading configuration: {e}")

    # -------------------------------------------------------------------------
    # ASYNC LOOP MANAGEMENT
    # -------------------------------------------------------------------------

    def _start_loop(self):
        """Start background asyncio event loop."""
        if self.loop and self.loop.is_running():
            return

        def run_loop():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_forever()

        self.loop_thread = threading.Thread(target=run_loop, daemon=True)
        self.loop_thread.start()
        self.logger.info("Async event loop started in background thread")

    def _stop_loop(self):
        """Stop background event loop."""
        if self.loop and self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)
            self.loop_thread.join(timeout=2)
            self.loop = None
            self.logger.info("Async event loop stopped")

    def _run_async(self, coro):
        """Schedule a coroutine in the background loop."""
        if not self.loop or not self.loop.is_running():
            raise RuntimeError("Event loop not running")
        return asyncio.run_coroutine_threadsafe(coro, self.loop)

    # -------------------------------------------------------------------------
    # TELEGRAM CONNECTION
    # -------------------------------------------------------------------------

    def _on_connect(self):
        """Handle connect/disconnect button."""
        if self.telegram_client and self.telegram_client.initialized:
            self._disconnect()
        else:
            self._connect()

    def _connect(self):
        """Connect to Telegram and start download manager."""
        def connect_thread():
            error_message = None
            try:
                self.root.after(0, lambda: self.status_var.set("Connecting..."))
                self.root.after(0, lambda: self.connect_btn.configure(state="disabled"))

                # Verify credentials are configured
                tconf = self.config_manager.get_telegram_config()
                if not tconf.api_id or not tconf.api_hash or not tconf.phone:
                    raise ValueError(
                        "Telegram credentials not configured. "
                        "Please run 'teledm config' to set up your credentials."
                    )

                # Start async loop
                self._start_loop()
                
                # Wait for event loop to be fully ready
                import time
                time.sleep(0.5)

                # Initialize telegram client
                future = self._run_async(self.telegram_client.initialize())
                success = future.result(timeout=60)

                if not success:
                    raise Exception("Telegram client initialization failed")

                # Register callbacks and start download manager
                self.download_manager.status_callbacks.append(self._on_download_event)

                future = self._run_async(self.download_manager.start())
                future.result(timeout=10)

                self.root.after(0, lambda: self.status_var.set("Connected"))
                self.root.after(0, lambda: self.connect_btn.configure(text="Disconnect", state="normal"))
                self.root.after(0, lambda: self._log("Connected to Telegram successfully"))
                self.root.after(0, self._refresh_downloads)
                self.root.after(0, self._start_auto_refresh)

            except Exception as e:
                self.logger.exception("Connection error")
                error_message = str(e)
                self.root.after(0, lambda msg=error_message: self.status_var.set("Connection failed"))
                self.root.after(0, lambda: self.connect_btn.configure(state="normal"))
                self.root.after(0, lambda msg=error_message: self._log(f"Connection error: {msg}"))
                self.root.after(
                    0, lambda msg=error_message: messagebox.showerror("Connection Error", f"Failed to connect:\n{msg}")
                )

        threading.Thread(target=connect_thread, daemon=True).start()

    def _disconnect(self):
        """Disconnect from Telegram."""
        def disconnect_thread():
            try:
                self._stop_auto_refresh()

                if self.download_manager:
                    future = self._run_async(self.download_manager.stop())
                    future.result(timeout=5)

                if self.telegram_client:
                    future = self._run_async(self.telegram_client.close())
                    future.result(timeout=5)

                self._stop_loop()

                self.root.after(0, lambda: self.status_var.set("Disconnected"))
                self.root.after(0, lambda: self.connect_btn.configure(text="Connect"))
                self.root.after(0, lambda: self._log("Disconnected from Telegram"))

            except Exception as e:
                self.logger.exception("Disconnect error")
                self.root.after(0, lambda: self._log(f"Error disconnecting: {e}"))

        threading.Thread(target=disconnect_thread, daemon=True).start()

    # -------------------------------------------------------------------------
    # DOWNLOAD OPERATIONS
    # -------------------------------------------------------------------------

    def _add_download(self):
        """Add a new download."""
        if not self.download_manager:
            messagebox.showwarning("Not Connected", "Please connect to Telegram first")
            return

        chat_id = self.chat_id_entry.get().strip()
        msg_id = self.msg_id_entry.get().strip()
        file_name = self.file_name_entry.get().strip()

        if not chat_id or not msg_id:
            messagebox.showwarning("Missing Info", "Please enter both Chat ID and Message ID")
            return

        if not file_name:
            file_name = f"file_{chat_id}_{msg_id}"

        try:
            # Use unique file_id format
            file_id = f"{chat_id}_{msg_id}"

            def add_task():
                future = self._run_async(
                    self.download_manager.add_download(
                        file_id=file_id,
                        file_name=file_name,
                        chat_id=chat_id,
                        message_id=int(msg_id),
                    )
                )
                future.result(timeout=5)

                self.root.after(0, lambda: self.chat_id_entry.delete(0, tk.END))
                self.root.after(0, lambda: self.msg_id_entry.delete(0, tk.END))
                self.root.after(0, lambda: self.file_name_entry.delete(0, tk.END))
                self.root.after(0, lambda: self._log(f"Added download: {file_name}"))
                self.root.after(0, self._refresh_downloads)

            threading.Thread(target=add_task, daemon=True).start()

        except Exception as e:
            self.logger.exception("Error adding download")
            messagebox.showerror("Error", f"Failed to add download:\n{e}")
            self._log(f"Error adding download: {e}")

    def _cancel_selected(self):
        """Cancel the selected download."""
        file_id = self._get_selected_file_id()
        if not file_id:
            messagebox.showwarning("No Selection", "Please select a download to cancel")
            return

        if not self.download_manager:
            return

        def cancel_task():
            try:
                future = self._run_async(self.download_manager.cancel_download(file_id))
                future.result(timeout=5)
                self.root.after(0, lambda: self._log(f"Cancelled download: {file_id}"))
                self.root.after(0, self._refresh_downloads)
            except Exception as e:
                self.logger.exception("Error cancelling download")
                self.root.after(0, lambda: self._log(f"Error cancelling: {e}"))

        threading.Thread(target=cancel_task, daemon=True).start()

    def _retry_selected(self):
        """Retry the selected download."""
        file_id = self._get_selected_file_id()
        if not file_id:
            messagebox.showwarning("No Selection", "Please select a download to retry")
            return

        if not self.download_manager:
            return

        def retry_task():
            try:
                future = self._run_async(self.download_manager.retry_download(file_id))
                future.result(timeout=5)
                self.root.after(0, lambda: self._log(f"Retrying download: {file_id}"))
                self.root.after(0, self._refresh_downloads)
            except Exception as e:
                self.logger.exception("Error retrying download")
                self.root.after(0, lambda: self._log(f"Error retrying: {e}"))

        threading.Thread(target=retry_task, daemon=True).start()

    def _remove_selected(self):
        """Remove the selected download from the database."""
        file_id = self._get_selected_file_id()
        if not file_id:
            messagebox.showwarning("No Selection", "Please select a download to remove")
            return

        if not self.download_manager:
            return

        result = messagebox.askyesno(
            "Confirm Remove", f"Remove download {file_id} from database?"
        )
        if not result:
            return

        def remove_task():
            try:
                # Cancel first if active
                future = self._run_async(self.download_manager.cancel_download(file_id))
                future.result(timeout=5)

                # Delete from DB
                future = self._run_async(self.download_manager.db.delete_download(file_id))
                future.result(timeout=5)

                self.root.after(0, lambda: self._log(f"Removed download: {file_id}"))
                self.root.after(0, self._refresh_downloads)
            except Exception as e:
                self.logger.exception("Error removing download")
                self.root.after(0, lambda: self._log(f"Error removing: {e}"))

        threading.Thread(target=remove_task, daemon=True).start()

    def _clear_completed(self):
        """Clear all completed/cancelled downloads."""
        if not self.download_manager:
            messagebox.showwarning("Not Connected", "Please connect first")
            return

        result = messagebox.askyesno(
            "Clear Completed",
            "Remove all completed and cancelled downloads from the list?",
        )
        if not result:
            return

        def clear_task():
            try:
                future = self._run_async(self.download_manager.clear_completed())
                count = future.result(timeout=5)
                self.root.after(0, lambda: self._log(f"Cleared {count} completed downloads"))
                self.root.after(0, self._refresh_downloads)
            except Exception as e:
                self.logger.exception("Error clearing completed")
                self.root.after(0, lambda: self._log(f"Error clearing: {e}"))

        threading.Thread(target=clear_task, daemon=True).start()

    # -------------------------------------------------------------------------
    # UI UPDATES
    # -------------------------------------------------------------------------

    def _refresh_downloads(self):
        """Refresh the downloads tree view."""
        if not self.download_manager:
            return

        def refresh_task():
            try:
                future = self._run_async(self.download_manager.db.get_all_downloads())
                downloads = future.result(timeout=5)

                def update_tree():
                    # Clear tree
                    for item in self.tree.get_children():
                        self.tree.delete(item)
                    self.tree_file_id_map.clear()

                    # Populate
                    for dl in downloads:
                        progress_text = f"{dl.progress:.1f}%"
                        speed_text = ""

                        if dl.status == "downloading":
                            speed = self.download_manager.speed.get(dl.file_id, 0)
                            speed_text = self._format_speed(speed) if speed > 0 else ""

                        item_id = self.tree.insert(
                            "",
                            "end",
                            text=str(dl.id),
                            values=(dl.file_name, dl.status, progress_text, speed_text),
                        )
                        self.tree_file_id_map[item_id] = dl.file_id

                self.root.after(0, update_tree)

            except Exception as e:
                self.logger.exception("Error refreshing downloads")

        threading.Thread(target=refresh_task, daemon=True).start()

    def _start_auto_refresh(self):
        """Start auto-refresh timer."""
        if self.refresh_job is None:
            self._schedule_refresh()

    def _stop_auto_refresh(self):
        """Stop auto-refresh timer."""
        if self.refresh_job is not None:
            self.root.after_cancel(self.refresh_job)
            self.refresh_job = None

    def _schedule_refresh(self):
        """Schedule next refresh."""
        if self.download_manager:
            self._refresh_downloads()
        self.refresh_job = self.root.after(2000, self._schedule_refresh)

    def _on_download_event(self, event_type, item):
        """Handle download events from DownloadManager."""
        file_name = item.get("file_name", "Unknown")
        self.root.after(0, lambda: self._log(f"Download {event_type}: {file_name}"))

    # -------------------------------------------------------------------------
    # HELPERS
    # -------------------------------------------------------------------------

    def _browse_path(self):
        """Browse for download directory."""
        path = filedialog.askdirectory(initialdir=self.download_path_var.get())
        if path:
            self.download_path_var.set(path)

    def _open_folder(self):
        """Open the download folder in file manager."""
        import subprocess
        import sys

        path = self.download_path_var.get()
        try:
            if sys.platform == "win32":
                subprocess.run(["explorer", path])
            elif sys.platform == "darwin":
                subprocess.run(["open", path])
            else:
                subprocess.run(["xdg-open", path])
        except Exception as e:
            self._log(f"Error opening folder: {e}")

    def _get_selected_file_id(self) -> Optional[str]:
        """Get file_id of selected tree item."""
        selected = self.tree.selection()
        if selected:
            return self.tree_file_id_map.get(selected[0])
        return None

    def _show_context_menu(self, event):
        """Show context menu on right-click."""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def _log(self, message: str):
        """Add message to log."""
        self.log_text.configure(state="normal")
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.configure(state="disabled")
        self.log_text.see(tk.END)

    @staticmethod
    def _format_speed(speed_bytes_per_sec: float) -> str:
        """Format speed in human-readable form."""
        if speed_bytes_per_sec < 1024:
            return f"{speed_bytes_per_sec:.1f} B/s"
        elif speed_bytes_per_sec < 1024 * 1024:
            return f"{speed_bytes_per_sec / 1024:.1f} KB/s"
        elif speed_bytes_per_sec < 1024 * 1024 * 1024:
            return f"{speed_bytes_per_sec / (1024 * 1024):.1f} MB/s"
        else:
            return f"{speed_bytes_per_sec / (1024 * 1024 * 1024):.1f} GB/s"

    # -------------------------------------------------------------------------
    # LIFECYCLE
    # -------------------------------------------------------------------------

    def _on_closing(self):
        """Handle window close - synchronous version."""
        try:
            self._stop_auto_refresh()

            if self.download_manager:
                try:
                    future = self._run_async(self.download_manager.stop())
                    future.result(timeout=5)
                except Exception as e:
                    self.logger.error(f"Error stopping download manager: {e}")

            if self.telegram_client:
                try:
                    future = self._run_async(self.telegram_client.close())
                    future.result(timeout=5)
                except Exception as e:
                    self.logger.error(f"Error closing telegram client: {e}")

            self._stop_loop()

        except Exception as e:
            self.logger.exception("Error during cleanup")

        self.root.destroy()

    def run(self):
        """Run the application."""
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        self.root.mainloop()
