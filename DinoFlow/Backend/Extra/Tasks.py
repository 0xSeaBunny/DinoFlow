import tkinter as tk
from tkinter import ttk, messagebox
import os


class TaskManager:
    
    def __init__(self, script_dir=None):
        self.script_dir = script_dir
    
    def get_task_names(self):
        return get_task_list(self.script_dir)


class TaskUIBuilder:
    
    def __init__(self, parent_frame, task_manager, bg, bg_light, bg_lighter, fg, font, font_bold, font_title):
        self.parent = parent_frame
        self.task_manager = task_manager
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
    
    def build_new_task_form(self, on_save, on_cancel=None):
        outer_frame, form_frame, canvas = self._create_scrollable_frame()
        self._scrollable_outer = outer_frame
        self._scrollable_canvas = canvas
        
        header_frame = tk.Frame(form_frame, bg=self.colors["bg"])
        header_frame.pack(fill=tk.X, pady=(0, 10))
        tk.Label(header_frame, text="New Task", font=self.fonts["font_title"], 
                bg=self.colors["bg"], fg=self.colors["fg"]).pack(side=tk.LEFT)
        
        btn_frame = tk.Frame(header_frame, bg=self.colors["bg"])
        btn_frame.pack(side=tk.RIGHT)
        
        tk.Button(btn_frame, text="Save", bg=self.colors["bg_lighter"], fg=self.colors["fg"], 
                 font=self.fonts["font_bold"], relief=tk.RAISED, bd=2, 
                 command=on_save).pack(side=tk.LEFT, padx=(0, 5))
        
        if on_cancel:
            tk.Button(btn_frame, text="Cancel", bg="#aa3333", fg=self.colors["fg"], 
                     font=self.fonts["font_bold"], relief=tk.RAISED, bd=2, 
                     command=on_cancel).pack(side=tk.LEFT)
        
        self.vars["name"] = tk.StringVar()
        tk.Label(form_frame, text="Task Name:", font=self.fonts["font_bold"], 
                bg=self.colors["bg"], fg=self.colors["fg"]).pack(anchor=tk.W, pady=(10, 5))
        tk.Entry(form_frame, textvariable=self.vars["name"], width=40,
                font=self.fonts["font"], bg=self.colors["bg_light"], 
                fg=self.colors["fg"]).pack(anchor=tk.W)
        
        self.vars["task_enabled"] = tk.BooleanVar(value=True)
        tk.Checkbutton(form_frame, text="Task Enabled", variable=self.vars["task_enabled"],
                      font=self.fonts["font_bold"], bg=self.colors["bg"], fg=self.colors["fg"],
                      selectcolor=self.colors["bg_light"]).pack(anchor=tk.W, pady=(10, 5))
        
        self.vars["description"] = tk.StringVar()
        tk.Label(form_frame, text="Task Prompt:", font=self.fonts["font_bold"], 
                bg=self.colors["bg"], fg=self.colors["fg"]).pack(anchor=tk.W, pady=(15, 5))
        tk.Entry(form_frame, textvariable=self.vars["description"], width=50,
                font=self.fonts["font"], bg=self.colors["bg_light"], 
                fg=self.colors["fg"]).pack(anchor=tk.W, fill=tk.X)
        
        self.vars["task_mode"] = tk.StringVar(value="Once")
        tk.Label(form_frame, text="Task Mode:", font=self.fonts["font_bold"], 
                bg=self.colors["bg"], fg=self.colors["fg"]).pack(anchor=tk.W, pady=(15, 5))
        ttk.Combobox(form_frame, textvariable=self.vars["task_mode"],
                    values=["Once", "Repeat"], state="readonly", width=20).pack(anchor=tk.W)
        
        self.vars["timer_type"] = tk.StringVar(value="Minutes")
        tk.Label(form_frame, text="Timer Type:", font=self.fonts["font_bold"], 
                bg=self.colors["bg"], fg=self.colors["fg"]).pack(anchor=tk.W, pady=(15, 5))
        ttk.Combobox(form_frame, textvariable=self.vars["timer_type"],
                    values=["Minutes", "specific time"], state="readonly", width=20).pack(anchor=tk.W)
        
        self.timer_details_frame = tk.Frame(form_frame, bg=self.colors["bg"])
        self.timer_details_frame.pack(anchor=tk.W, fill=tk.X, pady=(15, 5))
        
        self.vars["timer_type"].trace_add("write", lambda *args: self._update_timer_details(self.timer_details_frame, "new"))
        
        self._update_timer_details(self.timer_details_frame, "new")
    
    def _update_timer_details(self, container, mode):
        for widget in container.winfo_children():
            widget.destroy()
        
        timer_type = self.vars["timer_type"].get()
        
        if timer_type == "Minutes":
            if "minutes" not in self.vars:
                self.vars["minutes"] = tk.StringVar(value="")
            tk.Label(container, text="Minutes until this task fires after chat has started:", 
                    font=self.fonts["font_bold"], bg=self.colors["bg"], fg=self.colors["fg"]).pack(anchor=tk.W, pady=(0, 5))
            tk.Entry(container, textvariable=self.vars["minutes"], width=20,
                    font=self.fonts["font"], bg=self.colors["bg_light"], 
                    fg=self.colors["fg"]).pack(anchor=tk.W)
        
        elif timer_type == "specific time":
            if "specific_time" not in self.vars:
                self.vars["specific_time"] = tk.StringVar(value="")
            tk.Label(container, text="Time when task will fire:", 
                    font=self.fonts["font_bold"], bg=self.colors["bg"], fg=self.colors["fg"]).pack(anchor=tk.W, pady=(0, 5))
            time_options = [f"{h:02d}:00" for h in range(24)]
            ttk.Combobox(container, textvariable=self.vars["specific_time"],
                        values=time_options, state="readonly", width=20).pack(anchor=tk.W)
    
    def build_edit_task_form(self, task_data, on_save, on_delete, on_cancel=None):
        outer_frame, form_frame, canvas = self._create_scrollable_frame()
        self._scrollable_outer = outer_frame
        self._scrollable_canvas = canvas
        
        header_frame = tk.Frame(form_frame, bg=self.colors["bg"])
        header_frame.pack(fill=tk.X, pady=(0, 10))
        tk.Label(header_frame, text="Edit Task", font=self.fonts["font_title"], 
                bg=self.colors["bg"], fg=self.colors["fg"]).pack(side=tk.LEFT)
        
        btn_frame = tk.Frame(header_frame, bg=self.colors["bg"])
        btn_frame.pack(side=tk.RIGHT)
        
        tk.Button(btn_frame, text="Save", bg=self.colors["bg_lighter"], fg=self.colors["fg"], 
                 font=self.fonts["font_bold"], relief=tk.RAISED, bd=2, 
                 command=on_save).pack(side=tk.LEFT, padx=(0, 5))
        
        tk.Button(btn_frame, text="Delete", bg="#aa3333", fg=self.colors["fg"], 
                 font=self.fonts["font_bold"], relief=tk.RAISED, bd=2, 
                 command=on_delete).pack(side=tk.LEFT, padx=(0, 5))
        
        if on_cancel:
            tk.Button(btn_frame, text="Cancel", bg=self.colors["bg_light"], fg=self.colors["fg"], 
                     font=self.fonts["font_bold"], relief=tk.RAISED, bd=2, 
                     command=on_cancel).pack(side=tk.LEFT)
        
        self.vars["name"] = tk.StringVar(value=task_data.get("name", ""))
        tk.Label(form_frame, text="Task Name:", font=self.fonts["font_bold"], 
                bg=self.colors["bg"], fg=self.colors["fg"]).pack(anchor=tk.W, pady=(10, 5))
        tk.Entry(form_frame, textvariable=self.vars["name"], width=40,
                font=self.fonts["font"], bg=self.colors["bg_light"], 
                fg=self.colors["fg"]).pack(anchor=tk.W)
        
        self.vars["task_enabled"] = tk.BooleanVar(value=task_data.get("task_enabled", True))
        tk.Checkbutton(form_frame, text="Task Enabled", variable=self.vars["task_enabled"],
                      font=self.fonts["font_bold"], bg=self.colors["bg"], fg=self.colors["fg"],
                      selectcolor=self.colors["bg_light"]).pack(anchor=tk.W, pady=(10, 5))
        
        self.vars["description"] = tk.StringVar(value=task_data.get("description", ""))
        tk.Label(form_frame, text="Task Prompt:", font=self.fonts["font_bold"], 
                bg=self.colors["bg"], fg=self.colors["fg"]).pack(anchor=tk.W, pady=(15, 5))
        tk.Entry(form_frame, textvariable=self.vars["description"], width=50,
                font=self.fonts["font"], bg=self.colors["bg_light"], 
                fg=self.colors["fg"]).pack(anchor=tk.W, fill=tk.X)
        
        self.vars["task_mode"] = tk.StringVar(value=task_data.get("task_mode", "Once"))
        tk.Label(form_frame, text="Task Mode:", font=self.fonts["font_bold"], 
                bg=self.colors["bg"], fg=self.colors["fg"]).pack(anchor=tk.W, pady=(15, 5))
        ttk.Combobox(form_frame, textvariable=self.vars["task_mode"],
                    values=["Once", "Repeat"], state="readonly", width=20).pack(anchor=tk.W)
        
        self.vars["timer_type"] = tk.StringVar(value=task_data.get("timer_type", "Minutes"))
        tk.Label(form_frame, text="Timer Type:", font=self.fonts["font_bold"], 
                bg=self.colors["bg"], fg=self.colors["fg"]).pack(anchor=tk.W, pady=(15, 5))
        ttk.Combobox(form_frame, textvariable=self.vars["timer_type"],
                    values=["Minutes", "specific time"], state="readonly", width=20).pack(anchor=tk.W)
        
        self.timer_details_frame_edit = tk.Frame(form_frame, bg=self.colors["bg"])
        self.timer_details_frame_edit.pack(anchor=tk.W, fill=tk.X, pady=(15, 5))
        
        self.vars["timer_type"].trace_add("write", lambda *args: self._update_timer_details(self.timer_details_frame_edit, "edit"))
        
        self.vars["minutes"] = tk.StringVar(value=task_data.get("minutes", ""))
        self.vars["specific_time"] = tk.StringVar(value=task_data.get("specific_time", ""))
        
        self._update_timer_details(self.timer_details_frame_edit, "edit")
    
    def get_var(self, name):
        return self.vars.get(name)
    
    def get_widget(self, name):
        return self.widgets.get(name)


def get_tasks_dir(script_dir=None):
    if script_dir is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        script_dir = os.path.dirname(os.path.dirname(script_dir))
    tasks_dir = os.path.join(script_dir, "Backend", "SavedInfo", "Tasks")
    os.makedirs(tasks_dir, exist_ok=True)
    return tasks_dir


def save_task(name, description, task_mode, timer_type, minutes, specific_time, task_enabled=True, script_dir=None):
    if not name:
        return False, "Task name is required."
    
    tasks_dir = get_tasks_dir(script_dir)
    filename = name.replace(' ', '_') + ".txt"
    filepath = os.path.join(tasks_dir, filename)
    
    if os.path.exists(filepath):
        return False, f"Task '{name}' already exists."
    
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"Name: {name}\n")
            f.write(f"Task Prompt: {description}\n")
            f.write(f"Task Mode: {task_mode}\n")
            f.write(f"Timer Type: {timer_type}\n")
            if timer_type == "Minutes":
                f.write(f"Minutes: {minutes}\n")
            else:
                f.write(f"Specific Time: {specific_time}\n")
            f.write(f"Task Enabled: {task_enabled}\n")
        return True, f"Task '{name}' saved successfully."
    except Exception as e:
        return False, f"Failed to save task: {e}"


def update_task(old_name, name, description, task_mode, timer_type, minutes, specific_time, task_enabled=True, script_dir=None):
    if not name:
        return False, "Task name is required.", None
    
    tasks_dir = get_tasks_dir(script_dir)
    old_filename = old_name.replace(' ', '_') + ".txt"
    old_filepath = os.path.join(tasks_dir, old_filename)
    new_filename = name.replace(' ', '_') + ".txt"
    new_filepath = os.path.join(tasks_dir, new_filename)
    
    try:
        if old_name != name and os.path.exists(old_filepath):
            os.remove(old_filepath)
        
        with open(new_filepath, "w", encoding="utf-8") as f:
            f.write(f"Name: {name}\n")
            f.write(f"Task Prompt: {description}\n")
            f.write(f"Task Mode: {task_mode}\n")
            f.write(f"Timer Type: {timer_type}\n")
            if timer_type == "Minutes":
                f.write(f"Minutes: {minutes}\n")
            else:
                f.write(f"Specific Time: {specific_time}\n")
            f.write(f"Task Enabled: {task_enabled}\n")
        
        return True, f"Task '{name}' updated successfully.", name.replace(' ', '_')
    except Exception as e:
        return False, f"Failed to update task: {e}", None


def delete_task(name, script_dir=None):
    tasks_dir = get_tasks_dir(script_dir)
    filename = name.replace(' ', '_') + ".txt"
    filepath = os.path.join(tasks_dir, filename)
    
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            return True, f"Task '{name}' deleted successfully."
        else:
            return False, f"Task '{name}' not found."
    except Exception as e:
        return False, f"Failed to delete task: {e}"


def load_task(name, script_dir=None):
    tasks_dir = get_tasks_dir(script_dir)
    filename = name.replace(' ', '_') + ".txt"
    filepath = os.path.join(tasks_dir, filename)
    
    task_data = {
        "name": name,
        "description": "",
        "task_mode": "Once",
        "timer_type": "Minutes",
        "minutes": "",
        "specific_time": "",
        "task_enabled": True
    }
    
    if not os.path.exists(filepath):
        return task_data
    
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("Name: "):
                    task_data["name"] = line[6:]
                elif line.startswith("Task Prompt: "):
                    task_data["description"] = line[13:]
                elif line.startswith("Task Mode: "):
                    task_data["task_mode"] = line[11:]
                elif line.startswith("Timer Type: "):
                    task_data["timer_type"] = line[12:]
                elif line.startswith("Minutes: "):
                    task_data["minutes"] = line[9:]
                elif line.startswith("Specific Time: "):
                    task_data["specific_time"] = line[15:]
                elif line.startswith("Task Enabled: "):
                    task_data["task_enabled"] = line[14:].lower() == "true"
        return task_data
    except Exception:
        return task_data


def get_task_list(script_dir=None):
    tasks_dir = get_tasks_dir(script_dir)
    try:
        files = [f for f in os.listdir(tasks_dir) if f.endswith('.txt')]
        files.sort()
        tasks = [f.replace('.txt', '').replace('_', ' ') for f in files]
        return tasks
    except:
        return []
