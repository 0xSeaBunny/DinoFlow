import os
import tkinter as tk
from tkinter import messagebox, ttk


class SettingsManager:
    
    def __init__(self, script_dir=None):
        self.script_dir = script_dir
    
    def get_settings_path(self):
        if self.script_dir is None:
            self.script_dir = os.path.dirname(os.path.abspath(__file__))
            self.script_dir = os.path.dirname(os.path.dirname(self.script_dir))
        save_dir = os.path.join(self.script_dir, "Backend", "SavedInfo")
        os.makedirs(save_dir, exist_ok=True)
        return os.path.join(save_dir, "settings.txt")
    
    def load_settings(self):
        settings = {}
        settings_path = self.get_settings_path()
        if os.path.isfile(settings_path):
            try:
                with open(settings_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and ":" in line:
                            key, value = line.split(":", 1)
                            settings[key.strip()] = value.strip()
            except Exception:
                pass
        return settings
    
    def save_settings(self, settings_dict):
        settings_path = self.get_settings_path()
        try:
            with open(settings_path, "w", encoding="utf-8") as f:
                f.write("# DinoFlow Settings\n")
                for key, value in settings_dict.items():
                    f.write(f"{key}: {value}\n")
            return True, "Settings saved successfully."
        except Exception as e:
            return False, f"Failed to save settings: {e}"
    
    def get_reddit_credentials(self):
        return self.load_reddit_credentials()
    
    def get_reddit_info_path(self):
        if self.script_dir is None:
            self.script_dir = os.path.dirname(os.path.abspath(__file__))
            self.script_dir = os.path.dirname(os.path.dirname(self.script_dir))
        save_dir = os.path.join(self.script_dir, "Backend", "SavedInfo")
        os.makedirs(save_dir, exist_ok=True)
        return os.path.join(save_dir, "RedditInfo.txt")
    
    def load_reddit_credentials(self):
        creds = {
            "reddit_client_id": "",
            "reddit_client_secret": ""
        }
        reddit_path = self.get_reddit_info_path()
        if os.path.isfile(reddit_path):
            try:
                with open(reddit_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and ":" in line:
                            key, value = line.split(":", 1)
                            key = key.strip()
                            value = value.strip()
                            if key == "client_id":
                                creds["reddit_client_id"] = value
                            elif key == "client_secret":
                                creds["reddit_client_secret"] = value
            except Exception:
                pass
        return creds
    
    def save_reddit_credentials(self, client_id, client_secret):
        reddit_path = self.get_reddit_info_path()
        try:
            with open(reddit_path, "w", encoding="utf-8") as f:
                f.write("# Reddit API Credentials\n")
                f.write(f"client_id: {client_id}\n")
                f.write(f"client_secret: {client_secret}\n")
            return True, "Reddit credentials saved successfully."
        except Exception as e:
            return False, f"Failed to save Reddit credentials: {e}"

    def get_tavily_info_path(self):
        if self.script_dir is None:
            self.script_dir = os.path.dirname(os.path.abspath(__file__))
            self.script_dir = os.path.dirname(os.path.dirname(self.script_dir))
        save_dir = os.path.join(self.script_dir, "Backend", "SavedInfo")
        os.makedirs(save_dir, exist_ok=True)
        return os.path.join(save_dir, "Tavily.txt")

    def load_tavily_credentials(self):
        creds = {"tavily_api_key": ""}
        tavily_path = self.get_tavily_info_path()
        if os.path.isfile(tavily_path):
            try:
                with open(tavily_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and ":" in line:
                            key, value = line.split(":", 1)
                            key = key.strip()
                            value = value.strip()
                            if key == "api_key":
                                creds["tavily_api_key"] = value
            except Exception:
                pass
        return creds

    def save_tavily_credentials(self, api_key):
        tavily_path = self.get_tavily_info_path()
        try:
            with open(tavily_path, "w", encoding="utf-8") as f:
                f.write("# Tavily API Credentials\n")
                f.write(f"api_key: {api_key}\n")
            return True, "Tavily API key saved successfully."
        except Exception as e:
            return False, f"Failed to save Tavily API key: {e}"


class SettingsUIBuilder:
    
    def __init__(self, parent_frame, settings_manager, colors, fonts):
        self.parent = parent_frame
        self.settings_manager = settings_manager
        self.colors = colors
        self.fonts = fonts
        self.vars = {}
        self.widgets = {}
    
    def get_var(self, name):
        return self.vars.get(name)
    
    def get_widget(self, name):
        return self.widgets.get(name)
    
    def get_all_values(self):
        return {name: var.get() for name, var in self.vars.items()}
    
    def build_settings_tab(self, on_save_callback, on_open_reddit_callback=None, on_open_tavily_callback=None, section_type="reddit"):
        for widget in self.parent.winfo_children():
            widget.destroy()

        header_frame = tk.Frame(self.parent, bg=self.colors["bg"])
        header_frame.pack(fill=tk.X, pady=(0, 10))

        title_text = "Reddit API Settings" if section_type == "reddit" else "Tavily API Settings"
        tk.Label(header_frame, text=title_text, font=self.fonts["font_title"],
                bg=self.colors["bg"], fg=self.colors["fg"]).pack(side=tk.LEFT)

        btn_frame = tk.Frame(header_frame, bg=self.colors["bg"])
        btn_frame.pack(side=tk.RIGHT)

        tk.Button(btn_frame, text="Save", bg=self.colors["bg_lighter"], fg=self.colors["fg"],
                 font=self.fonts["font_bold"], relief=tk.RAISED, bd=2,
                 command=on_save_callback).pack(side=tk.LEFT, padx=(0, 5))

        if on_open_reddit_callback and section_type == "reddit":
            tk.Button(btn_frame, text="Open Reddit's API Site", bg="#0077cc", fg=self.colors["fg"],
                     font=self.fonts["font_bold"], relief=tk.RAISED, bd=2,
                     command=on_open_reddit_callback).pack(side=tk.LEFT)

        if on_open_tavily_callback and section_type == "tavily":
            tk.Button(btn_frame, text="Open Tavily Site", bg="#0077cc", fg=self.colors["fg"],
                     font=self.fonts["font_bold"], relief=tk.RAISED, bd=2,
                     command=on_open_tavily_callback).pack(side=tk.LEFT)

        if section_type == "reddit":
            self._build_reddit_section(self.parent)
        else:
            self._build_tavily_section(self.parent)
    
    def _build_reddit_section(self, parent):
        reddit_frame = tk.LabelFrame(parent, text="Reddit API", font=self.fonts["font_bold"],
                                     bg=self.colors["bg"], fg=self.colors["fg"],
                                     relief=tk.RIDGE, bd=2)
        reddit_frame.pack(fill=tk.X, pady=(10, 20), padx=5)
        reddit_frame.configure(bg=self.colors["bg"])
        
        self.vars["reddit_client_id"] = tk.StringVar()
        tk.Label(reddit_frame, text="Client ID:", font=self.fonts["font_bold"], 
                bg=self.colors["bg"], fg=self.colors["fg"]).pack(anchor=tk.W, pady=(5, 2), padx=10)
        tk.Entry(reddit_frame, textvariable=self.vars["reddit_client_id"], width=50,
                font=self.fonts["font"], bg=self.colors["bg_light"], 
                fg=self.colors["fg"]).pack(anchor=tk.W, padx=10)
        
        self.vars["reddit_client_secret"] = tk.StringVar()
        tk.Label(reddit_frame, text="Client Secret:", font=self.fonts["font_bold"],
                bg=self.colors["bg"], fg=self.colors["fg"]).pack(anchor=tk.W, pady=(10, 2), padx=10)
        tk.Entry(reddit_frame, textvariable=self.vars["reddit_client_secret"], width=50,
                font=self.fonts["font"], bg=self.colors["bg_light"],
                fg=self.colors["fg"], show="*").pack(anchor=tk.W, padx=10, pady=(0, 10))

    def _build_tavily_section(self, parent):
        tavily_frame = tk.LabelFrame(parent, text="Tavily API", font=self.fonts["font_bold"],
                                     bg=self.colors["bg"], fg=self.colors["fg"],
                                     relief=tk.RIDGE, bd=2)
        tavily_frame.pack(fill=tk.X, pady=(10, 20), padx=5)
        tavily_frame.configure(bg=self.colors["bg"])

        self.vars["tavily_api_key"] = tk.StringVar()
        tk.Label(tavily_frame, text="API Key:", font=self.fonts["font_bold"],
                bg=self.colors["bg"], fg=self.colors["fg"]).pack(anchor=tk.W, pady=(5, 2), padx=10)
        tk.Entry(tavily_frame, textvariable=self.vars["tavily_api_key"], width=50,
                font=self.fonts["font"], bg=self.colors["bg_light"],
                fg=self.colors["fg"], show="*").pack(anchor=tk.W, padx=10, pady=(0, 10))

    def load_values(self, section_type="reddit"):
        if section_type == "reddit":
            creds = self.settings_manager.load_reddit_credentials()
        else:
            creds = self.settings_manager.load_tavily_credentials()
        for key, value in creds.items():
            if key in self.vars:
                self.vars[key].set(value)


def save_settings(settings_dict, script_dir=None):
    manager = SettingsManager(script_dir)
    return manager.save_settings(settings_dict)


def load_settings(script_dir=None):
    manager = SettingsManager(script_dir)
    return manager.load_settings()
