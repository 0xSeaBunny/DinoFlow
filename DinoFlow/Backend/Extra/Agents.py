import os
import sys
import tkinter as tk
from tkinter import messagebox, ttk

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "MainScripts"))
from Tools import TOOL_DEFINITIONS as _TOOL_DEFINITIONS


def _generate_ui_tools():
    _tool_categories = {
        "AVAILABLE_TOOLS": [
            "get_system_info", "get_current_time", "list_processes", "kill_process",
            "start_process", "run_shell_command", "run_python_code"
        ],
        "GENERAL_TOOLS": [
            "take_screenshot", "save_to_memory", "toggle_task", "create_task"
        ],
        "BROWSER_TOOLS": [
            "launch_browser", "navigate_to", "get_page_text", "click_element",
            "find_elements", "scroll_page", "close_browser"
        ],
        "FILES_TOOLS": [
            "read_file", "write_file", "delete_file", "list_directory",
            "search_files", "create_folder", "move_file", "copy_file"
        ],
        "INPUTS_TOOLS": [
            "type_text", "press_key", "get_mouse_position", "move_mouse",
            "click_mouse", "scroll_mouse"
        ],
        "APIs": [
            "search_reddit", "get_reddit_thread",
            "tavily_search", "tavily_search_advanced", "tavily_extract"
        ]
    }
    
    ui_tools = {}
    all_tool_map = {t["function"]["name"]: t["function"]["description"] for t in _TOOL_DEFINITIONS}
    
    for category, tool_names in _tool_categories.items():
        ui_tools[category] = []
        for name in tool_names:
            if name in all_tool_map:
                desc = all_tool_map[name]
                display_name = name.replace("_", " ").title()
                ui_tools[category].append((name, display_name))
    
    return ui_tools


_UI_TOOLS = _generate_ui_tools()
AVAILABLE_TOOLS = _UI_TOOLS.get("AVAILABLE_TOOLS", [])
GENERAL_TOOLS = _UI_TOOLS.get("GENERAL_TOOLS", [])
BROWSER_TOOLS = _UI_TOOLS.get("BROWSER_TOOLS", [])
FILES_TOOLS = _UI_TOOLS.get("FILES_TOOLS", [])
INPUTS_TOOLS = _UI_TOOLS.get("INPUTS_TOOLS", [])
API_TOOLS = _UI_TOOLS.get("APIs", [])


def get_agent_catalog_path(script_dir=None):

    if script_dir is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        script_dir = os.path.dirname(os.path.dirname(script_dir))
    catalog_dir = os.path.join(script_dir, "Backend", "SavedInfo", "AgentCatalog")
    os.makedirs(catalog_dir, exist_ok=True)
    return catalog_dir


def get_database_names(script_dir=None):

    if script_dir is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        script_dir = os.path.dirname(os.path.dirname(script_dir))
    db_path = os.path.join(script_dir, "Backend", "SavedInfo", "Databases.txt")
    
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


def save_agent(name, model, system_prompt, connected_dbs, enabled_tools=None, script_dir=None):

    if not name:
        return False, "Agent name is required."
    if not model or model == "No models available":
        return False, "Please select a model."

    filename = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).rstrip()
    filename = filename.replace(' ', '_') + ".txt"
    
    catalog_dir = get_agent_catalog_path(script_dir)
    filepath = os.path.join(catalog_dir, filename)
    

    connected_dbs_str = ", ".join(connected_dbs) if connected_dbs else "None"
    enabled_tools_str = ", ".join(enabled_tools) if enabled_tools else "None"
    agent_data = f"Name: {name}\nModel: {model}\nSystem Prompt: {system_prompt}\nConnected Databases: {connected_dbs_str}\nEnabled Tools: {enabled_tools_str}\n"
    
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(agent_data)
        return True, f"Agent '{name}' saved successfully."
    except Exception as e:
        return False, f"Failed to save agent: {e}"


def update_agent(old_filename, name, model, system_prompt, connected_dbs, enabled_tools=None, script_dir=None):

    if not name:
        return False, "Agent name is required.", old_filename
    if not model or model == "No models available":
        return False, "Please select a model.", old_filename
    
    catalog_dir = get_agent_catalog_path(script_dir)
    old_filepath = os.path.join(catalog_dir, old_filename)
    
    new_filename = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).rstrip()
    new_filename = new_filename.replace(' ', '_') + ".txt"
    new_filepath = os.path.join(catalog_dir, new_filename)
    
    connected_dbs_str = ", ".join(connected_dbs) if connected_dbs else "None"
    enabled_tools_str = ", ".join(enabled_tools) if enabled_tools else "None"
    agent_data = f"Name: {name}\nModel: {model}\nSystem Prompt: {system_prompt}\nConnected Databases: {connected_dbs_str}\nEnabled Tools: {enabled_tools_str}\n"
    
    try:
        if new_filename != old_filename and os.path.exists(old_filepath):
            os.remove(old_filepath)
        
        with open(new_filepath, "w", encoding="utf-8") as f:
            f.write(agent_data)
        
        return True, f"Agent '{name}' updated successfully.", new_filename
    except Exception as e:
        return False, f"Failed to update agent: {e}", old_filename


def delete_agent(filename, script_dir=None):

    catalog_dir = get_agent_catalog_path(script_dir)
    filepath = os.path.join(catalog_dir, filename)
    
    try:
        agent_name = ""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("Name: "):
                        agent_name = line[6:]
                        break
        except:
            pass
        
        os.remove(filepath)
        
        if agent_name and script_dir:
            memory_folder = os.path.join(script_dir, "Backend", "SavedInfo", "AgentFolders", agent_name.replace(' ', '_'))
            if os.path.exists(memory_folder):
                import shutil
                shutil.rmtree(memory_folder)
        
        return True, "Agent and associated memory deleted."
    except Exception as e:
        return False, f"Failed to delete agent: {e}"


def delete_agent_memory(filename, script_dir=None):

    catalog_dir = get_agent_catalog_path(script_dir)
    filepath = os.path.join(catalog_dir, filename)
    
    try:
        agent_name = ""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("Name: "):
                        agent_name = line[6:]
                        break
        except:
            pass
        
        if agent_name and script_dir:
            memory_folder = os.path.join(script_dir, "Backend", "SavedInfo", "AgentFolders", agent_name.replace(' ', '_'))
            if os.path.exists(memory_folder):
                import shutil
                shutil.rmtree(memory_folder)
                return True, f"Memory for agent '{agent_name}' deleted."
            else:
                return True, f"No memory found for agent '{agent_name}'."
        else:
            return False, "Could not determine agent name."
    except Exception as e:
        return False, f"Failed to delete memory: {e}"


def load_agent(filename, script_dir=None):

    catalog_dir = get_agent_catalog_path(script_dir)
    filepath = os.path.join(catalog_dir, filename)
    
    agent_data = {
        "name": "",
        "model": "",
        "system_prompt": "",
        "connected_dbs": [],
        "enabled_tools": []
    }
    
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("Name: "):
                    agent_data["name"] = line[6:]
                elif line.startswith("Model: "):
                    agent_data["model"] = line[7:]
                elif line.startswith("System Prompt: "):
                    agent_data["system_prompt"] = line[15:]
                elif line.startswith("Connected Databases: "):
                    db_list = line.replace("Connected Databases: ", "").strip()
                    if db_list and db_list != "None":
                        agent_data["connected_dbs"] = [db.strip() for db in db_list.split(",") if db.strip()]
                elif line.startswith("Enabled Tools: "):
                    tools_list = line.replace("Enabled Tools: ", "").strip()
                    if tools_list and tools_list != "None":
                        agent_data["enabled_tools"] = [tool.strip() for tool in tools_list.split(",") if tool.strip()]
    except:
        return None
    
    return agent_data


def load_agent_connected_dbs(filename, script_dir=None):

    catalog_dir = get_agent_catalog_path(script_dir)
    filepath = os.path.join(catalog_dir, filename)
    
    connected_dbs = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("Connected Databases: "):
                    db_list = line.replace("Connected Databases: ", "").strip()
                    if db_list and db_list != "None":
                        connected_dbs = [db.strip() for db in db_list.split(",") if db.strip()]
                    break
    except Exception:
        pass
    
    return connected_dbs


def load_agent_enabled_tools(filename, script_dir=None):

    catalog_dir = get_agent_catalog_path(script_dir)
    filepath = os.path.join(catalog_dir, filename)
    
    enabled_tools = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("Enabled Tools: "):
                    tools_list = line.replace("Enabled Tools: ", "").strip()
                    if tools_list and tools_list != "None":
                        enabled_tools = [tool.strip() for tool in tools_list.split(",") if tool.strip()]
                    break
    except Exception:
        pass
    
    return enabled_tools


def get_agent_list(script_dir=None):

    catalog_dir = get_agent_catalog_path(script_dir)
    try:
        files = [f for f in os.listdir(catalog_dir) if f.endswith('.txt')]
        files.sort()
        agents = [(f.replace('.txt', '').replace('_', ' '), f) for f in files]
        return agents
    except:
        return []


class AgentManager:
 
    def __init__(self, script_dir=None):
        self.script_dir = script_dir
        self.new_agent_connected_dbs = []
        self.edit_agent_connected_dbs = []
        self.new_agent_enabled_tools = []
        self.edit_agent_enabled_tools = []
    
    def get_agent_names(self):
        agents = get_agent_list(self.script_dir)
        return [name for name, _ in agents] if agents else ["No agents available"]
    
    def add_db_to_new_agent(self, db_name):
        if not db_name or db_name == "No databases available":
            return
        
        if db_name not in self.new_agent_connected_dbs:
            self.new_agent_connected_dbs.append(db_name)
    
    def remove_db_from_new_agent(self, db_name):
        if db_name and db_name in self.new_agent_connected_dbs:
            self.new_agent_connected_dbs.remove(db_name)
    
    def get_new_agent_db_display_text(self):
        if self.new_agent_connected_dbs:
            return ", ".join(self.new_agent_connected_dbs)
        else:
            return "No databases connected"
    
    def add_db_to_edit_agent(self, db_name):
        if not db_name or db_name == "No databases available":
            return
        
        if db_name not in self.edit_agent_connected_dbs:
            self.edit_agent_connected_dbs.append(db_name)
    
    def remove_db_from_edit_agent(self, db_name):
        if db_name and db_name in self.edit_agent_connected_dbs:
            self.edit_agent_connected_dbs.remove(db_name)
    
    def get_edit_agent_db_display_text(self):
        if self.edit_agent_connected_dbs:
            return ", ".join(self.edit_agent_connected_dbs)
        else:
            return "No databases connected"
    
    def load_edit_agent_dbs(self, filename):
        self.edit_agent_connected_dbs = load_agent_connected_dbs(filename, self.script_dir)
        self.load_edit_agent_tools(filename)
    
    def clear_new_agent_dbs(self):
        self.new_agent_connected_dbs = []
        self.new_agent_enabled_tools = []

    def toggle_new_agent_tool(self, tool_name, enabled):
        if enabled:
            if tool_name not in self.new_agent_enabled_tools:
                self.new_agent_enabled_tools.append(tool_name)
        else:
            if tool_name in self.new_agent_enabled_tools:
                self.new_agent_enabled_tools.remove(tool_name)
    
    def is_new_agent_tool_enabled(self, tool_name):
        return tool_name in self.new_agent_enabled_tools
    
    def toggle_edit_agent_tool(self, tool_name, enabled):
        if enabled:
            if tool_name not in self.edit_agent_enabled_tools:
                self.edit_agent_enabled_tools.append(tool_name)
        else:
            if tool_name in self.edit_agent_enabled_tools:
                self.edit_agent_enabled_tools.remove(tool_name)
    
    def is_edit_agent_tool_enabled(self, tool_name):
        return tool_name in self.edit_agent_enabled_tools
    
    def load_edit_agent_tools(self, filename):
        agent_data = load_agent(filename, self.script_dir)
        if agent_data:
            self.edit_agent_enabled_tools = agent_data.get("enabled_tools", [])


class AgentUIBuilder:

    def __init__(self, parent_frame, agent_manager, model_names, db_names, bg, bg_light, bg_lighter, fg, font, font_bold, font_title):
        self.parent = parent_frame
        self.agent_manager = agent_manager
        self.model_names = model_names
        self.db_names = db_names
        self.colors = {"bg": bg, "bg_light": bg_light, "bg_lighter": bg_lighter, "fg": fg}
        self.fonts = {"font": font, "font_bold": font_bold, "font_title": font_title}
        self.vars = {}
        self.widgets = {}
    
    def _create_scrollable_frame(self):
        outer_frame = tk.Frame(self.parent, bg=self.colors["bg"])
        outer_frame.pack(fill=tk.BOTH, expand=True)
        
        canvas = tk.Canvas(outer_frame, bg=self.colors["bg"], highlightthickness=0)
        scrollbar = tk.Scrollbar(outer_frame, orient="vertical", command=canvas.yview)
        
        canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        inner_frame = tk.Frame(canvas, bg=self.colors["bg"])
        canvas_window = canvas.create_window((0, 0), window=inner_frame, anchor="nw")
        
        def on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)
        
        canvas.bind("<Configure>", on_canvas_configure)
        
        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        inner_frame.bind("<Configure>", on_frame_configure)
        
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind_all("<MouseWheel>", on_mousewheel)
        
        return outer_frame, inner_frame, canvas
    
    def build_new_agent_form(self, on_save, on_add_db, on_remove_db):
        self.agent_manager.clear_new_agent_dbs()
        
        outer_frame, form_frame, canvas = self._create_scrollable_frame()
        self._scrollable_outer = outer_frame
        self._scrollable_canvas = canvas
        
        header_frame = tk.Frame(form_frame, bg=self.colors["bg"])
        header_frame.pack(fill=tk.X, pady=(0, 10))
        tk.Label(header_frame, text="New Agent", font=self.fonts["font_title"], bg=self.colors["bg"], fg=self.colors["fg"]).pack(side=tk.LEFT)
        tk.Button(header_frame, text="Save", bg=self.colors["bg_lighter"], fg=self.colors["fg"], font=self.fonts["font_bold"],
                 relief=tk.RAISED, bd=2, command=on_save).pack(side=tk.RIGHT)
        
        self.vars["name"] = tk.StringVar()
        tk.Label(form_frame, text="Name:", font=self.fonts["font_bold"], bg=self.colors["bg"], fg=self.colors["fg"]).pack(anchor=tk.W, pady=(10, 5))
        tk.Entry(form_frame, textvariable=self.vars["name"], width=40,
                font=self.fonts["font"], bg=self.colors["bg_light"], fg=self.colors["fg"]).pack(anchor=tk.W)
        
        self.vars["model"] = tk.StringVar()
        tk.Label(form_frame, text="Agent Model:", font=self.fonts["font_bold"], bg=self.colors["bg"], fg=self.colors["fg"]).pack(anchor=tk.W, pady=(15, 5))
        ttk.Combobox(form_frame, textvariable=self.vars["model"],
                    values=self.model_names, state="readonly", width=40).pack(anchor=tk.W)
        
        self.vars["prompt"] = tk.StringVar()
        tk.Label(form_frame, text="System Prompt:", font=self.fonts["font_bold"], bg=self.colors["bg"], fg=self.colors["fg"]).pack(anchor=tk.W, pady=(15, 5))
        tk.Entry(form_frame, textvariable=self.vars["prompt"], width=50,
                font=self.fonts["font"], bg=self.colors["bg_light"], fg=self.colors["fg"]).pack(anchor=tk.W, fill=tk.X)
        
        tk.Label(form_frame, text="Connected Databases:", font=self.fonts["font_bold"], bg=self.colors["bg"], fg=self.colors["fg"]).pack(anchor=tk.W, pady=(15, 5))
        
        db_list_frame = tk.Frame(form_frame, bg=self.colors["bg_light"], bd=1, relief=tk.SUNKEN)
        db_list_frame.pack(anchor=tk.W, fill=tk.X, pady=(0, 5))
        self.widgets["db_list_label"] = tk.Label(db_list_frame, text="No databases connected", 
                                           font=self.fonts["font"], bg=self.colors["bg_light"], fg=self.colors["fg"], anchor=tk.W)
        self.widgets["db_list_label"].pack(anchor=tk.W, padx=5, pady=5)
        
        db_select_frame = tk.Frame(form_frame, bg=self.colors["bg"])
        db_select_frame.pack(anchor=tk.W)
        
        self.vars["db"] = tk.StringVar()
        self.widgets["db_combo"] = ttk.Combobox(db_select_frame, textvariable=self.vars["db"],
                      values=self.db_names, state="readonly", width=30)
        self.widgets["db_combo"].pack(side=tk.LEFT)
        
        tk.Button(db_select_frame, text="Add", bg=self.colors["bg_lighter"], fg=self.colors["fg"], font=self.fonts["font_bold"],
                 relief=tk.RAISED, bd=2, command=on_add_db).pack(side=tk.LEFT, padx=(5, 2))
        tk.Button(db_select_frame, text="Remove", bg=self.colors["bg_lighter"], fg=self.colors["fg"], font=self.fonts["font_bold"],
                 relief=tk.RAISED, bd=2, command=on_remove_db).pack(side=tk.LEFT, padx=(2, 0))
        
        tk.Label(form_frame, text="Enabled Tools:", font=self.fonts["font_bold"], bg=self.colors["bg"], fg=self.colors["fg"]).pack(anchor=tk.W, pady=(15, 5))
        
        system_tools_frame = tk.Frame(form_frame, bg=self.colors["bg_light"], bd=1, relief=tk.SUNKEN)
        system_tools_frame.pack(anchor=tk.W, fill=tk.X, pady=(0, 5))
        
        tk.Label(system_tools_frame, text="System Tools:", font=self.fonts["font_bold"], bg=self.colors["bg_light"], fg=self.colors["fg"]).pack(anchor=tk.W, padx=5, pady=(5, 0))
        
        for tool_name, tool_desc in AVAILABLE_TOOLS:
            var = tk.BooleanVar(value=self.agent_manager.is_new_agent_tool_enabled(tool_name))
            self.vars[f"tool_{tool_name}"] = var
            tk.Checkbutton(system_tools_frame, text=tool_desc,
                          variable=var,
                          bg=self.colors["bg_light"], fg=self.colors["fg"],
                          selectcolor=self.colors["bg"],
                          command=lambda tn=tool_name, v=var: self.agent_manager.toggle_new_agent_tool(tn, v.get())).pack(anchor=tk.W, padx=5)
        
        general_tools_frame = tk.Frame(form_frame, bg=self.colors["bg_light"], bd=1, relief=tk.SUNKEN)
        general_tools_frame.pack(anchor=tk.W, fill=tk.X, pady=(0, 5))
        
        tk.Label(general_tools_frame, text="General Tools:", font=self.fonts["font_bold"], bg=self.colors["bg_light"], fg=self.colors["fg"]).pack(anchor=tk.W, padx=5, pady=(5, 0))
        
        for tool_name, tool_desc in GENERAL_TOOLS:
            var = tk.BooleanVar(value=self.agent_manager.is_new_agent_tool_enabled(tool_name))
            self.vars[f"tool_{tool_name}"] = var
            tk.Checkbutton(general_tools_frame, text=tool_desc,
                          variable=var,
                          bg=self.colors["bg_light"], fg=self.colors["fg"],
                          selectcolor=self.colors["bg"],
                          command=lambda tn=tool_name, v=var: self.agent_manager.toggle_new_agent_tool(tn, v.get())).pack(anchor=tk.W, padx=5)
        
        browser_tools_frame = tk.Frame(form_frame, bg=self.colors["bg_light"], bd=1, relief=tk.SUNKEN)
        browser_tools_frame.pack(anchor=tk.W, fill=tk.X, pady=(0, 5))
        
        tk.Label(browser_tools_frame, text="Browser Tools:", font=self.fonts["font_bold"], bg=self.colors["bg_light"], fg=self.colors["fg"]).pack(anchor=tk.W, padx=5, pady=(5, 0))
        
        for tool_name, tool_desc in BROWSER_TOOLS:
            var = tk.BooleanVar(value=self.agent_manager.is_new_agent_tool_enabled(tool_name))
            self.vars[f"tool_{tool_name}"] = var
            tk.Checkbutton(browser_tools_frame, text=tool_desc,
                          variable=var,
                          bg=self.colors["bg_light"], fg=self.colors["fg"],
                          selectcolor=self.colors["bg"],
                          command=lambda tn=tool_name, v=var: self.agent_manager.toggle_new_agent_tool(tn, v.get())).pack(anchor=tk.W, padx=5)
        
        files_tools_frame = tk.Frame(form_frame, bg=self.colors["bg_light"], bd=1, relief=tk.SUNKEN)
        files_tools_frame.pack(anchor=tk.W, fill=tk.X, pady=(0, 5))
        
        tk.Label(files_tools_frame, text="Files Tools:", font=self.fonts["font_bold"], bg=self.colors["bg_light"], fg=self.colors["fg"]).pack(anchor=tk.W, padx=5, pady=(5, 0))
        
        for tool_name, tool_desc in FILES_TOOLS:
            var = tk.BooleanVar(value=self.agent_manager.is_new_agent_tool_enabled(tool_name))
            self.vars[f"tool_{tool_name}"] = var
            tk.Checkbutton(files_tools_frame, text=tool_desc,
                          variable=var,
                          bg=self.colors["bg_light"], fg=self.colors["fg"],
                          selectcolor=self.colors["bg"],
                          command=lambda tn=tool_name, v=var: self.agent_manager.toggle_new_agent_tool(tn, v.get())).pack(anchor=tk.W, padx=5)
        
        inputs_tools_frame = tk.Frame(form_frame, bg=self.colors["bg_light"], bd=1, relief=tk.SUNKEN)
        inputs_tools_frame.pack(anchor=tk.W, fill=tk.X, pady=(0, 5))

        tk.Label(inputs_tools_frame, text="Inputs Tools:", font=self.fonts["font_bold"], bg=self.colors["bg_light"], fg=self.colors["fg"]).pack(anchor=tk.W, padx=5, pady=(5, 0))

        for tool_name, tool_desc in INPUTS_TOOLS:
            var = tk.BooleanVar(value=self.agent_manager.is_new_agent_tool_enabled(tool_name))
            self.vars[f"tool_{tool_name}"] = var
            tk.Checkbutton(inputs_tools_frame, text=tool_desc,
                          variable=var,
                          bg=self.colors["bg_light"], fg=self.colors["fg"],
                          selectcolor=self.colors["bg"],
                          command=lambda tn=tool_name, v=var: self.agent_manager.toggle_new_agent_tool(tn, v.get())).pack(anchor=tk.W, padx=5)

        api_tools_frame = tk.Frame(form_frame, bg=self.colors["bg_light"], bd=1, relief=tk.SUNKEN)
        api_tools_frame.pack(anchor=tk.W, fill=tk.X, pady=(0, 5))

        tk.Label(api_tools_frame, text="APIs:", font=self.fonts["font_bold"], bg=self.colors["bg_light"], fg=self.colors["fg"]).pack(anchor=tk.W, padx=5, pady=(5, 0))

        for tool_name, tool_desc in API_TOOLS:
            var = tk.BooleanVar(value=self.agent_manager.is_new_agent_tool_enabled(tool_name))
            self.vars[f"tool_{tool_name}"] = var
            tk.Checkbutton(api_tools_frame, text=tool_desc,
                          variable=var,
                          bg=self.colors["bg_light"], fg=self.colors["fg"],
                          selectcolor=self.colors["bg"],
                          command=lambda tn=tool_name, v=var: self.agent_manager.toggle_new_agent_tool(tn, v.get())).pack(anchor=tk.W, padx=5)


    def update_db_list_label(self):
        self.widgets["db_list_label"].config(text=self.agent_manager.get_new_agent_db_display_text())
    
    def build_edit_agent_form(self, agent_data, filename, on_save, on_delete, on_add_db, on_remove_db, on_delete_memory=None):
        self.agent_manager.load_edit_agent_dbs(filename)
        
        outer_frame, form_frame, canvas = self._create_scrollable_frame()
        self._scrollable_outer = outer_frame
        self._scrollable_canvas = canvas
        
        header_frame = tk.Frame(form_frame, bg=self.colors["bg"])
        header_frame.pack(fill=tk.X, pady=(0, 10))
        tk.Label(header_frame, text="Edit Agent", font=self.fonts["font_title"], bg=self.colors["bg"], fg=self.colors["fg"]).pack(side=tk.LEFT)
        
        btn_frame = tk.Frame(header_frame, bg=self.colors["bg"])
        btn_frame.pack(side=tk.RIGHT)
        tk.Button(btn_frame, text="Save", bg=self.colors["bg_lighter"], fg=self.colors["fg"], font=self.fonts["font_bold"],
                 relief=tk.RAISED, bd=2, command=on_save).pack(side=tk.LEFT, padx=(0, 5))
        
        if on_delete_memory:
            tk.Button(btn_frame, text="Delete Memory", bg="#aa6633", fg=self.colors["fg"], font=self.fonts["font_bold"],
                     relief=tk.RAISED, bd=2, command=on_delete_memory).pack(side=tk.LEFT, padx=(0, 5))
        
        tk.Button(btn_frame, text="Delete", bg="#aa3333", fg=self.colors["fg"], font=self.fonts["font_bold"],
                 relief=tk.RAISED, bd=2, command=lambda: on_delete(filename)).pack(side=tk.LEFT)
        
        self.vars["name"] = tk.StringVar(value=agent_data.get("name", ""))
        tk.Label(form_frame, text="Name:", font=self.fonts["font_bold"], bg=self.colors["bg"], fg=self.colors["fg"]).pack(anchor=tk.W, pady=(10, 5))
        tk.Entry(form_frame, textvariable=self.vars["name"], width=40,
                font=self.fonts["font"], bg=self.colors["bg_light"], fg=self.colors["fg"]).pack(anchor=tk.W)
        
        self.vars["model"] = tk.StringVar(value=agent_data.get("model", ""))
        tk.Label(form_frame, text="Agent Model:", font=self.fonts["font_bold"], bg=self.colors["bg"], fg=self.colors["fg"]).pack(anchor=tk.W, pady=(15, 5))
        ttk.Combobox(form_frame, textvariable=self.vars["model"],
                    values=self.model_names, state="readonly", width=40).pack(anchor=tk.W)
        
        self.vars["prompt"] = tk.StringVar(value=agent_data.get("system_prompt", ""))
        tk.Label(form_frame, text="System Prompt:", font=self.fonts["font_bold"], bg=self.colors["bg"], fg=self.colors["fg"]).pack(anchor=tk.W, pady=(15, 5))
        tk.Entry(form_frame, textvariable=self.vars["prompt"], width=50,
                font=self.fonts["font"], bg=self.colors["bg_light"], fg=self.colors["fg"]).pack(anchor=tk.W, fill=tk.X)
        
        tk.Label(form_frame, text="Connected Databases:", font=self.fonts["font_bold"], bg=self.colors["bg"], fg=self.colors["fg"]).pack(anchor=tk.W, pady=(15, 5))
        
        db_list_frame = tk.Frame(form_frame, bg=self.colors["bg_light"], bd=1, relief=tk.SUNKEN)
        db_list_frame.pack(anchor=tk.W, fill=tk.X, pady=(0, 5))
        self.widgets["db_list_label"] = tk.Label(db_list_frame, 
                                           text=self.agent_manager.get_edit_agent_db_display_text(), 
                                           font=self.fonts["font"], bg=self.colors["bg_light"], fg=self.colors["fg"], anchor=tk.W)
        self.widgets["db_list_label"].pack(anchor=tk.W, padx=5, pady=5)
        
        db_select_frame = tk.Frame(form_frame, bg=self.colors["bg"])
        db_select_frame.pack(anchor=tk.W)
        
        self.vars["db"] = tk.StringVar()
        self.widgets["db_combo"] = ttk.Combobox(db_select_frame, textvariable=self.vars["db"],
                                          values=self.db_names, state="readonly", width=30)
        self.widgets["db_combo"].pack(side=tk.LEFT)
        
        tk.Button(db_select_frame, text="Add", bg=self.colors["bg_lighter"], fg=self.colors["fg"], font=self.fonts["font_bold"],
                 relief=tk.RAISED, bd=2, command=on_add_db).pack(side=tk.LEFT, padx=(5, 2))
        tk.Button(db_select_frame, text="Remove", bg=self.colors["bg_lighter"], fg=self.colors["fg"], font=self.fonts["font_bold"],
                 relief=tk.RAISED, bd=2, command=on_remove_db).pack(side=tk.LEFT, padx=(2, 0))
        
        tk.Label(form_frame, text="Enabled Tools:", font=self.fonts["font_bold"], bg=self.colors["bg"], fg=self.colors["fg"]).pack(anchor=tk.W, pady=(15, 5))
        
        system_tools_frame = tk.Frame(form_frame, bg=self.colors["bg_light"], bd=1, relief=tk.SUNKEN)
        system_tools_frame.pack(anchor=tk.W, fill=tk.X, pady=(0, 5))
        
        tk.Label(system_tools_frame, text="System Tools:", font=self.fonts["font_bold"], bg=self.colors["bg_light"], fg=self.colors["fg"]).pack(anchor=tk.W, padx=5, pady=(5, 0))
        
        for tool_name, tool_desc in AVAILABLE_TOOLS:
            var = tk.BooleanVar(value=self.agent_manager.is_edit_agent_tool_enabled(tool_name))
            self.vars[f"tool_{tool_name}"] = var
            tk.Checkbutton(system_tools_frame, text=tool_desc,
                          variable=var,
                          bg=self.colors["bg_light"], fg=self.colors["fg"],
                          selectcolor=self.colors["bg"],
                          command=lambda tn=tool_name, v=var: self.agent_manager.toggle_edit_agent_tool(tn, v.get())).pack(anchor=tk.W, padx=5)
        
        general_tools_frame = tk.Frame(form_frame, bg=self.colors["bg_light"], bd=1, relief=tk.SUNKEN)
        general_tools_frame.pack(anchor=tk.W, fill=tk.X, pady=(0, 5))
        
        tk.Label(general_tools_frame, text="General Tools:", font=self.fonts["font_bold"], bg=self.colors["bg_light"], fg=self.colors["fg"]).pack(anchor=tk.W, padx=5, pady=(5, 0))
        
        for tool_name, tool_desc in GENERAL_TOOLS:
            var = tk.BooleanVar(value=self.agent_manager.is_edit_agent_tool_enabled(tool_name))
            self.vars[f"tool_{tool_name}"] = var
            tk.Checkbutton(general_tools_frame, text=tool_desc,
                          variable=var,
                          bg=self.colors["bg_light"], fg=self.colors["fg"],
                          selectcolor=self.colors["bg"],
                          command=lambda tn=tool_name, v=var: self.agent_manager.toggle_edit_agent_tool(tn, v.get())).pack(anchor=tk.W, padx=5)
        
        browser_tools_frame = tk.Frame(form_frame, bg=self.colors["bg_light"], bd=1, relief=tk.SUNKEN)
        browser_tools_frame.pack(anchor=tk.W, fill=tk.X, pady=(0, 5))
        
        tk.Label(browser_tools_frame, text="Browser Tools:", font=self.fonts["font_bold"], bg=self.colors["bg_light"], fg=self.colors["fg"]).pack(anchor=tk.W, padx=5, pady=(5, 0))
        
        for tool_name, tool_desc in BROWSER_TOOLS:
            var = tk.BooleanVar(value=self.agent_manager.is_edit_agent_tool_enabled(tool_name))
            self.vars[f"tool_{tool_name}"] = var
            tk.Checkbutton(browser_tools_frame, text=tool_desc,
                          variable=var,
                          bg=self.colors["bg_light"], fg=self.colors["fg"],
                          selectcolor=self.colors["bg"],
                          command=lambda tn=tool_name, v=var: self.agent_manager.toggle_edit_agent_tool(tn, v.get())).pack(anchor=tk.W, padx=5)
        
        files_tools_frame = tk.Frame(form_frame, bg=self.colors["bg_light"], bd=1, relief=tk.SUNKEN)
        files_tools_frame.pack(anchor=tk.W, fill=tk.X, pady=(0, 5))
        
        tk.Label(files_tools_frame, text="Files Tools:", font=self.fonts["font_bold"], bg=self.colors["bg_light"], fg=self.colors["fg"]).pack(anchor=tk.W, padx=5, pady=(5, 0))
        
        for tool_name, tool_desc in FILES_TOOLS:
            var = tk.BooleanVar(value=self.agent_manager.is_edit_agent_tool_enabled(tool_name))
            self.vars[f"tool_{tool_name}"] = var
            tk.Checkbutton(files_tools_frame, text=tool_desc,
                          variable=var,
                          bg=self.colors["bg_light"], fg=self.colors["fg"],
                          selectcolor=self.colors["bg"],
                          command=lambda tn=tool_name, v=var: self.agent_manager.toggle_edit_agent_tool(tn, v.get())).pack(anchor=tk.W, padx=5)
        
        inputs_tools_frame = tk.Frame(form_frame, bg=self.colors["bg_light"], bd=1, relief=tk.SUNKEN)
        inputs_tools_frame.pack(anchor=tk.W, fill=tk.X, pady=(0, 5))

        tk.Label(inputs_tools_frame, text="Inputs Tools:", font=self.fonts["font_bold"], bg=self.colors["bg_light"], fg=self.colors["fg"]).pack(anchor=tk.W, padx=5, pady=(5, 0))

        for tool_name, tool_desc in INPUTS_TOOLS:
            var = tk.BooleanVar(value=self.agent_manager.is_edit_agent_tool_enabled(tool_name))
            self.vars[f"tool_{tool_name}"] = var
            tk.Checkbutton(inputs_tools_frame, text=tool_desc,
                          variable=var,
                          bg=self.colors["bg_light"], fg=self.colors["fg"],
                          selectcolor=self.colors["bg"],
                          command=lambda tn=tool_name, v=var: self.agent_manager.toggle_edit_agent_tool(tn, v.get())).pack(anchor=tk.W, padx=5)

        api_tools_frame = tk.Frame(form_frame, bg=self.colors["bg_light"], bd=1, relief=tk.SUNKEN)
        api_tools_frame.pack(anchor=tk.W, fill=tk.X, pady=(0, 5))

        tk.Label(api_tools_frame, text="APIs:", font=self.fonts["font_bold"], bg=self.colors["bg_light"], fg=self.colors["fg"]).pack(anchor=tk.W, padx=5, pady=(5, 0))

        for tool_name, tool_desc in API_TOOLS:
            var = tk.BooleanVar(value=self.agent_manager.is_edit_agent_tool_enabled(tool_name))
            self.vars[f"tool_{tool_name}"] = var
            tk.Checkbutton(api_tools_frame, text=tool_desc,
                          variable=var,
                          bg=self.colors["bg_light"], fg=self.colors["fg"],
                          selectcolor=self.colors["bg"],
                          command=lambda tn=tool_name, v=var: self.agent_manager.toggle_edit_agent_tool(tn, v.get())).pack(anchor=tk.W, padx=5)


    def update_edit_db_list_label(self):
        self.widgets["db_list_label"].config(text=self.agent_manager.get_edit_agent_db_display_text())
    
    def get_var(self, name):
        return self.vars.get(name)
    
    def get_db_var(self):
        return self.vars.get("db")
