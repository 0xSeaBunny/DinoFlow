import os
import tkinter as tk
from tkinter import messagebox, ttk


class DatabaseManager:
    
    def __init__(self, script_dir=None):
        self.script_dir = script_dir
    
    def get_database_names(self):
        return _get_database_list(self.script_dir)
    
    def get_db_file_path(self):
        return _get_databases_file_path(self.script_dir)


class DatabaseUIBuilder:
    
    def __init__(self, parent_frame, db_manager, bg, bg_light, bg_lighter, fg, font, font_bold, font_title):
        self.parent = parent_frame
        self.db_manager = db_manager
        self.colors = {"bg": bg, "bg_light": bg_light, "bg_lighter": bg_lighter, "fg": fg}
        self.fonts = {"font": font, "font_bold": font_bold, "font_title": font_title}
        self.vars = {}
    
    def get_var(self, name):
        return self.vars.get(name)
    
    def build_new_db_form(self, on_save):
        for widget in self.parent.winfo_children():
            widget.destroy()
        
        header_frame = tk.Frame(self.parent, bg=self.colors["bg"])
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(header_frame, text="New Database", font=self.fonts["font_title"], 
                bg=self.colors["bg"], fg=self.colors["fg"]).pack(side=tk.LEFT)
        
        tk.Button(header_frame, text="Save", bg=self.colors["bg_lighter"], fg=self.colors["fg"], 
                 font=self.fonts["font_bold"], relief=tk.RAISED, bd=2, 
                 command=on_save).pack(side=tk.RIGHT)
        
        tk.Label(self.parent, text="Name:", font=self.fonts["font_bold"], 
                bg=self.colors["bg"], fg=self.colors["fg"]).pack(anchor=tk.W, pady=(10, 5))
        
        self.vars["name"] = tk.StringVar()
        tk.Entry(self.parent, textvariable=self.vars["name"], width=40,
                font=self.fonts["font"], bg=self.colors["bg_light"], 
                fg=self.colors["fg"]).pack(anchor=tk.W)
        
        tk.Label(self.parent, text="File or Folder Path:", font=self.fonts["font_bold"], 
                bg=self.colors["bg"], fg=self.colors["fg"]).pack(anchor=tk.W, pady=(15, 5))
        
        path_frame = tk.Frame(self.parent, bg=self.colors["bg"])
        path_frame.pack(anchor=tk.W)
        
        self.vars["path"] = tk.StringVar()
        tk.Entry(path_frame, textvariable=self.vars["path"], width=50,
                font=self.fonts["font"], bg=self.colors["bg_light"], 
                fg=self.colors["fg"]).pack(side=tk.LEFT)
    
    def build_edit_db_form(self, db_name, file_path, on_save, on_delete):
        for widget in self.parent.winfo_children():
            widget.destroy()
        
        header_frame = tk.Frame(self.parent, bg=self.colors["bg"])
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(header_frame, text="Edit Database", font=self.fonts["font_title"], 
                bg=self.colors["bg"], fg=self.colors["fg"]).pack(side=tk.LEFT)
        
        btn_frame = tk.Frame(header_frame, bg=self.colors["bg"])
        btn_frame.pack(side=tk.RIGHT)
        
        tk.Button(btn_frame, text="Save", bg=self.colors["bg_lighter"], fg=self.colors["fg"], 
                 font=self.fonts["font_bold"], relief=tk.RAISED, bd=2, 
                 command=on_save).pack(side=tk.LEFT, padx=(0, 5))
        
        tk.Button(btn_frame, text="Delete", bg="#aa3333", fg=self.colors["fg"], 
                 font=self.fonts["font_bold"], relief=tk.RAISED, bd=2, 
                 command=on_delete).pack(side=tk.LEFT)
        
        tk.Label(self.parent, text="Name:", font=self.fonts["font_bold"], 
                bg=self.colors["bg"], fg=self.colors["fg"]).pack(anchor=tk.W, pady=(10, 5))
        
        self.vars["name"] = tk.StringVar(value=db_name)
        tk.Entry(self.parent, textvariable=self.vars["name"], width=40,
                font=self.fonts["font"], bg=self.colors["bg_light"], 
                fg=self.colors["fg"]).pack(anchor=tk.W)
        
        tk.Label(self.parent, text="File or Folder Path:", font=self.fonts["font_bold"], 
                bg=self.colors["bg"], fg=self.colors["fg"]).pack(anchor=tk.W, pady=(15, 5))
        
        path_frame = tk.Frame(self.parent, bg=self.colors["bg"])
        path_frame.pack(anchor=tk.W)
        
        self.vars["path"] = tk.StringVar(value=file_path)
        tk.Entry(path_frame, textvariable=self.vars["path"], width=50,
                font=self.fonts["font"], bg=self.colors["bg_light"], 
                fg=self.colors["fg"]).pack(side=tk.LEFT)


def _get_databases_file_path(script_dir=None):
    if script_dir is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        script_dir = os.path.dirname(os.path.dirname(script_dir))
    return os.path.join(script_dir, "Backend", "SavedInfo", "Databases.txt")


def _get_database_list(script_dir=None):
    db_path = _get_databases_file_path(script_dir)
    
    databases = []
    if os.path.isfile(db_path):
        try:
            with open(db_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and line.startswith("Name: "):
                        parts = line.split("|")
                        if parts:
                            name_part = parts[0].replace("Name: ", "").strip()
                            if name_part:
                                databases.append(name_part)
        except Exception:
            pass
    
    return databases if databases else ["No databases available"]


def get_database_names(script_dir=None):
    return _get_database_list(script_dir)


def get_database_info(db_name, script_dir=None):
    db_path = _get_databases_file_path(script_dir)
    file_path = ""
    
    try:
        if os.path.isfile(db_path):
            with open(db_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("Name: "):
                        parts = line.split("|")
                        if parts:
                            name_part = parts[0].replace("Name: ", "").strip()
                            if name_part == db_name and len(parts) > 0:
                                if "FilePath: " in parts[-1]:
                                    file_path = parts[-1].replace("FilePath: ", "").strip()
                                    break
    except:
        pass
    
    return file_path


def save_database(name, file_path, script_dir=None):
    if not name:
        return False, "Database name is required."
    if not file_path:
        return False, "File path is required."
    
    save_path = _get_databases_file_path(script_dir)
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    
    try:
        databases = []
        if os.path.isfile(save_path):
            with open(save_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        databases.append(line)
        
        for db in databases:
            if db.startswith(f"Name: {name}|"):
                return False, f"Database '{name}' already exists."
        
        db_entry = f"Name: {name}|FilePath: {file_path}"
        databases.append(db_entry)
        
        with open(save_path, "w", encoding="utf-8") as f:
            f.write("# Databases Configuration File\n")
            f.write("# Format: Name: <name>|FilePath: <path>\n")
            f.write("# One database per line\n\n")
            for db in databases:
                f.write(db + "\n")
        
        return True, f"Database '{name}' saved successfully."
    except Exception as e:
        return False, f"Failed to save database: {e}"


def update_database(old_name, new_name, new_path, script_dir=None):
    if not new_name:
        return False, "Database name is required.", None
    if not new_path:
        return False, "File path is required.", None
    
    save_path = _get_databases_file_path(script_dir)
    
    try:
        databases = []
        if os.path.isfile(save_path):
            with open(save_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        databases.append(line)
        
        new_databases = []
        found = False
        for db in databases:
            if db.startswith(f"Name: {old_name}|"):
                new_databases.append(f"Name: {new_name}|FilePath: {new_path}")
                found = True
            else:
                new_databases.append(db)
        
        if not found:
            return False, f"Database '{old_name}' not found.", None
        
        if old_name != new_name:
            for db in new_databases:
                if db.startswith(f"Name: {new_name}|") and not db.startswith(f"Name: {old_name}|"):
                    return False, f"Database name '{new_name}' already exists.", None
        
        with open(save_path, "w", encoding="utf-8") as f:
            f.write("# Databases Configuration File\n")
            f.write("# Format: Name: <name>|FilePath: <path>\n")
            f.write("# One database per line\n\n")
            for db in new_databases:
                f.write(db + "\n")
        
        return True, f"Database '{new_name}' updated successfully.", new_name
    except Exception as e:
        return False, f"Failed to update database: {e}", None


def delete_database(db_name, script_dir=None):
    save_path = _get_databases_file_path(script_dir)
    
    try:
        databases = []
        if os.path.isfile(save_path):
            with open(save_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        databases.append(line)
        
        new_databases = [db for db in databases if not db.startswith(f"Name: {db_name}|")]
        
        with open(save_path, "w", encoding="utf-8") as f:
            f.write("# Databases Configuration File\n")
            f.write("# Format: Name: <name>|FilePath: <path>\n")
            f.write("# One database per line\n\n")
            for db in new_databases:
                f.write(db + "\n")
        
        return True, f"Database '{db_name}' deleted successfully."
    except Exception as e:
        return False, f"Failed to delete database: {e}"
