#!/usr/bin/env python3
"""DinoFlow Setup Script - Checks and installs required dependencies."""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess
import sys
import importlib.util
import threading

# Package definitions with their import names and pip names
PACKAGES = {
    "requests": {
        "pip_name": "requests",
        "import_name": "requests",
        "description": "HTTP library for Ollama API calls",
        "required": True
    },
    "selenium": {
        "pip_name": "selenium",
        "import_name": "selenium",
        "description": "Browser automation for web tools",
        "required": True
    },
    "webdriver-manager": {
        "pip_name": "webdriver-manager",
        "import_name": "webdriver_manager",
        "description": "ChromeDriver auto-management",
        "required": True
    },
    "pyautogui": {
        "pip_name": "pyautogui",
        "import_name": "pyautogui",
        "description": "Keyboard/mouse input control (optional)",
        "required": False
    },
    "discord.py": {
        "pip_name": "discord.py",
        "import_name": "discord",
        "description": "Discord bot integration (optional)",
        "required": False
    },
    "python-telegram-bot": {
        "pip_name": "python-telegram-bot",
        "import_name": "telegram",
        "description": "Telegram bot integration (optional)",
        "required": False
    }
}


class DinoFlowSetup:
    def __init__(self, root):
        self.root = root
        self.root.title("DinoFlow Setup")
        self.root.geometry("600x500")
        self.root.configure(bg="#2b2b2b")
        
        self.check_vars = {}
        self.status_labels = {}
        self.missing_packages = []
        
        self._build_ui()
        self._check_installed()
    
    def _build_ui(self):
        # Title
        title = tk.Label(
            self.root,
            text="DinoFlow Dependency Setup",
            font=("Arial", 16, "bold"),
            bg="#2b2b2b",
            fg="white"
        )
        title.pack(pady=(20, 10))
        
        # Description
        desc = tk.Label(
            self.root,
            text="Check which packages you want to install.",
            font=("Arial", 10),
            bg="#2b2b2b",
            fg="#aaaaaa"
        )
        desc.pack(pady=(0, 20))
        
        # Package list frame
        list_frame = tk.Frame(self.root, bg="#3c3c3c", bd=2, relief=tk.SUNKEN)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Headers
        header_frame = tk.Frame(list_frame, bg="#3c3c3c")
        header_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(header_frame, text="Install", bg="#3c3c3c", fg="white", 
                font=("Arial", 10, "bold"), width=8).pack(side=tk.LEFT)
        tk.Label(header_frame, text="Package", bg="#3c3c3c", fg="white",
                font=("Arial", 10, "bold"), width=20).pack(side=tk.LEFT, padx=(10, 0))
        tk.Label(header_frame, text="Status", bg="#3c3c3c", fg="white",
                font=("Arial", 10, "bold"), width=15).pack(side=tk.LEFT, padx=(10, 0))
        
        # Separator
        tk.Frame(list_frame, bg="#555555", height=1).pack(fill=tk.X, padx=5)
        
        # Package rows
        for pkg_id, pkg_info in PACKAGES.items():
            row = tk.Frame(list_frame, bg="#3c3c3c")
            row.pack(fill=tk.X, padx=10, pady=3)
            
            # Checkbox
            var = tk.BooleanVar(value=False)
            self.check_vars[pkg_id] = var
            
            cb = tk.Checkbutton(
                row,
                variable=var,
                bg="#3c3c3c",
                fg="white",
                selectcolor="#2b2b2b",
                activebackground="#3c3c3c",
                activeforeground="white"
            )
            cb.pack(side=tk.LEFT)
            
            # Package name and description
            name_frame = tk.Frame(row, bg="#3c3c3c")
            name_frame.pack(side=tk.LEFT, padx=(10, 0), fill=tk.X, expand=True)
            
            tk.Label(
                name_frame,
                text=pkg_info["pip_name"],
                bg="#3c3c3c",
                fg="white",
                font=("Arial", 10, "bold"),
                anchor=tk.W
            ).pack(fill=tk.X)
            
            tk.Label(
                name_frame,
                text=pkg_info["description"],
                bg="#3c3c3c",
                fg="#aaaaaa",
                font=("Arial", 8),
                anchor=tk.W
            ).pack(fill=tk.X)
            
            # Status label
            status_label = tk.Label(
                row,
                text="Checking...",
                bg="#3c3c3c",
                fg="#aaaaaa",
                font=("Arial", 9),
                width=15,
                anchor=tk.W
            )
            status_label.pack(side=tk.LEFT, padx=(10, 0))
            self.status_labels[pkg_id] = status_label
        
        # Progress frame
        progress_frame = tk.Frame(self.root, bg="#2b2b2b")
        progress_frame.pack(fill=tk.X, padx=20, pady=(10, 5))
        
        self.progress_label = tk.Label(
            progress_frame,
            text="Ready to install",
            bg="#2b2b2b",
            fg="#aaaaaa",
            font=("Arial", 9),
            anchor=tk.W
        )
        self.progress_label.pack(fill=tk.X)
        
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            mode='determinate',
            length=100
        )
        self.progress_bar.pack(fill=tk.X, pady=(5, 0))
        
        # Button frame
        btn_frame = tk.Frame(self.root, bg="#2b2b2b")
        btn_frame.pack(fill=tk.X, padx=20, pady=(10, 20))
        
        self.install_btn = tk.Button(
            btn_frame,
            text="Install Selected",
            command=self._start_installation,
            bg="#00aaff",
            fg="white",
            font=("Arial", 10, "bold"),
            relief=tk.FLAT,
            padx=20,
            pady=8
        )
        self.install_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.select_missing_btn = tk.Button(
            btn_frame,
            text="Select Missing Only",
            command=self._select_missing,
            bg="#4a4a4a",
            fg="white",
            font=("Arial", 10),
            relief=tk.FLAT,
            padx=15,
            pady=8
        )
        self.select_missing_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.exit_btn = tk.Button(
            btn_frame,
            text="Exit",
            command=self.root.quit,
            bg="#4a4a4a",
            fg="white",
            font=("Arial", 10),
            relief=tk.FLAT,
            padx=20,
            pady=8
        )
        self.exit_btn.pack(side=tk.RIGHT)
    
    def _check_installed(self):
        """Check which packages are already installed."""
        for pkg_id, pkg_info in PACKAGES.items():
            if self._is_installed(pkg_info["import_name"]):
                self.status_labels[pkg_id].config(
                    text="Installed",
                    fg="#00ff00"
                )
            else:
                self.status_labels[pkg_id].config(
                    text="Not installed",
                    fg="#ff6666"
                )
                self.missing_packages.append(pkg_id)
                
                # Auto-check required packages
                if pkg_info["required"]:
                    self.check_vars[pkg_id].set(True)
    
    def _is_installed(self, import_name):
        """Check if a package is installed by trying to import it."""
        try:
            spec = importlib.util.find_spec(import_name)
            return spec is not None
        except ModuleNotFoundError:
            return False
    
    def _select_missing(self):
        """Select only packages that are not installed."""
        for pkg_id, pkg_info in PACKAGES.items():
            if not self._is_installed(pkg_info["import_name"]):
                self.check_vars[pkg_id].set(True)
            else:
                self.check_vars[pkg_id].set(False)
    
    def _start_installation(self):
        """Start installing selected packages one by one."""
        selected = [
            pkg_id for pkg_id, var in self.check_vars.items()
            if var.get()
        ]
        
        if not selected:
            messagebox.showwarning("No Selection", "Please select at least one package to install.")
            return
        
        self.install_btn.config(state="disabled")
        self.select_missing_btn.config(state="disabled")
        
        # Run installation in background thread
        thread = threading.Thread(target=self._install_packages, args=(selected,), daemon=True)
        thread.start()
    
    def _install_packages(self, package_ids):
        """Install packages one by one with confirmation."""
        total = len(package_ids)
        
        for i, pkg_id in enumerate(package_ids):
            pkg_info = PACKAGES[pkg_id]
            
            # Update progress
            progress = (i / total) * 100
            self.root.after(0, lambda p=progress, name=pkg_info["pip_name"]: self._update_progress(
                p, f"Installing {name}... ({i+1}/{total})"
            ))
            
            # Install the package
            success = self._install_package(pkg_info["pip_name"])
            
            if success:
                self.root.after(0, lambda pid=pkg_id: self._mark_installed(pid))
            else:
                self.root.after(0, lambda pid=pkg_id, name=pkg_info["pip_name"]: self._mark_failed(pid, name))
            
            # Small delay between installations
            import time
            time.sleep(0.5)
        
        # Done
        self.root.after(0, lambda: self._installation_complete())
    
    def _install_package(self, pip_name):
        """Install a single package using pip."""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", pip_name],
                capture_output=True,
                text=True,
                timeout=120
            )
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            return False
        except Exception:
            return False
    
    def _update_progress(self, value, text):
        """Update the progress bar and label."""
        self.progress_bar['value'] = value
        self.progress_label.config(text=text)
    
    def _mark_installed(self, pkg_id):
        """Mark a package as installed."""
        self.status_labels[pkg_id].config(
            text="Installed",
            fg="#00ff00"
        )
        self.check_vars[pkg_id].set(False)
    
    def _mark_failed(self, pkg_id, name):
        """Mark a package as failed to install."""
        self.status_labels[pkg_id].config(
            text="Failed",
            fg="#ff0000"
        )
        messagebox.showerror(
            "Installation Failed",
            f"Failed to install {name}.\n\nTry running:\npip install {name}"
        )
    
    def _installation_complete(self):
        """Called when all installations are done."""
        self.progress_bar['value'] = 100
        self.progress_label.config(text="Installation complete!")
        self.install_btn.config(state="normal")
        self.select_missing_btn.config(state="normal")
        
        # Recheck all packages
        self.missing_packages = []
        for pkg_id, pkg_info in PACKAGES.items():
            if self._is_installed(pkg_info["import_name"]):
                self.status_labels[pkg_id].config(text="Installed", fg="#00ff00")
            else:
                self.status_labels[pkg_id].config(text="Not installed", fg="#ff6666")
                self.missing_packages.append(pkg_id)
        
        if not self.missing_packages:
            messagebox.showinfo(
                "Setup Complete",
                "All packages are installed!\n\nYou can now run DinoFlow."
            )
        else:
            messagebox.showinfo(
                "Setup Partial",
                f"Some packages are still missing:\n" +
                "\n".join([PACKAGES[p]["pip_name"] for p in self.missing_packages]) +
                "\n\nYou can run DinoFlow, but some features may not work."
            )


def main():
    root = tk.Tk()
    app = DinoFlowSetup(root)
    root.mainloop()


if __name__ == "__main__":
    main()
