import sys
import os
import subprocess
import signal
import time
import threading
import datetime
import tkinter as tk
from tkinter import messagebox, ttk, scrolledtext

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "MainScripts"))
from api_chat import chat_with_api, get_model_max_context
from Tools import TOOL_DEFINITIONS as ALL_TOOLS
from Memory import (
    get_episodic_memory, get_skill_lessons,
    get_user_preferences, get_pattern_detector,
    get_memory_context_for_prompt, summarize_conversation,
    set_current_agent, get_current_agent
)


def load_agent_config(agent_name, script_dir=None):
    if script_dir is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        script_dir = os.path.dirname(os.path.dirname(script_dir))
    
    agent_file = os.path.join(script_dir, "Backend", "SavedInfo", "AgentCatalog", agent_name.replace(' ', '_') + ".txt")
    
    config = {
        "name": agent_name,
        "model": "",
        "system_prompt": "",
        "connected_dbs": [],
        "enabled_tools": []
    }
    
    if not os.path.isfile(agent_file):
        return config
    
    try:
        with open(agent_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("Name: "):
                    config["name"] = line[6:]
                elif line.startswith("Model: "):
                    config["model"] = line[7:]
                elif line.startswith("System Prompt: "):
                    config["system_prompt"] = line[15:]
                elif line.startswith("Connected Databases: "):
                    db_list = line.replace("Connected Databases: ", "").strip()
                    if db_list and db_list != "None":
                        config["connected_dbs"] = [db.strip() for db in db_list.split(",") if db.strip()]
                elif line.startswith("Enabled Tools: "):
                    tools_list = line.replace("Enabled Tools: ", "").strip()
                    if tools_list and tools_list != "None":
                        config["enabled_tools"] = [tool.strip() for tool in tools_list.split(",") if tool.strip()]
    except:
        pass
    
    return config


def load_enabled_tasks(script_dir=None):
    if script_dir is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        script_dir = os.path.dirname(os.path.dirname(script_dir))
    
    tasks_dir = os.path.join(script_dir, "Backend", "SavedInfo", "Tasks")
    enabled_tasks = []
    
    if not os.path.isdir(tasks_dir):
        return enabled_tasks
    
    try:
        for filename in os.listdir(tasks_dir):
            if not filename.endswith(".txt"):
                continue
            
            filepath = os.path.join(tasks_dir, filename)
            task_data = {
                "name": filename.replace(".txt", "").replace("_", " "),
                "description": "",
                "task_enabled": False,
                "task_mode": "Once",
                "timer_type": "Minutes",
                "minutes": "",
                "specific_time": ""
            }
            
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
            except:
                pass
            
            if task_data["task_enabled"]:
                enabled_tasks.append(task_data)
    except:
        pass
    
    return enabled_tasks


_active_task_scheduler = None

def set_active_task_scheduler(scheduler):
    global _active_task_scheduler
    _active_task_scheduler = scheduler

def get_active_task_scheduler():
    return _active_task_scheduler

def schedule_task_dynamically(task_data):
    scheduler = get_active_task_scheduler()
    if scheduler and scheduler.is_running:
        scheduler._schedule_task(task_data)
        return True
    return False


class TaskScheduler:
    def __init__(self, chat_session, on_task_fire):
        self.chat_session = chat_session
        self.on_task_fire = on_task_fire
        self.enabled_tasks = []
        self.pending_tasks = []
        self.timers = []
        self.is_running = False
        self.lock = threading.Lock()
    
    def start(self, script_dir=None):
        self.enabled_tasks = load_enabled_tasks(script_dir)
        self.is_running = True
        set_active_task_scheduler(self)
        for task in self.enabled_tasks:
            self._schedule_task(task)
        self.processor_thread = threading.Thread(target=self._process_pending_tasks, daemon=True)
        self.processor_thread.start()
    
    def stop(self):
        self.is_running = False
        set_active_task_scheduler(None)
        for timer in self.timers:
            timer.cancel()
        self.timers.clear()
    
    def _schedule_task(self, task):
        if task["timer_type"] == "Minutes":
            try:
                minutes = int(task.get("minutes", 0))
                if minutes > 0:
                    timer = threading.Timer(minutes * 60, self._on_timer_fire, args=[task])
                    timer.start()
                    self.timers.append(timer)
            except:
                pass
        
        elif task["timer_type"] == "specific time":
            try:
                time_str = task.get("specific_time", "")
                if time_str:
                    now = datetime.datetime.now()
                    hour, minute = map(int, time_str.split(":"))
                    target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    if target_time <= now:
                        target_time += datetime.timedelta(days=1)
                    
                    delay_seconds = (target_time - now).total_seconds()
                    timer = threading.Timer(delay_seconds, self._on_timer_fire, args=[task])
                    timer.start()
                    self.timers.append(timer)
            except:
                pass
    
    def _on_timer_fire(self, task):
        with self.lock:
            self.pending_tasks.append(task)
        if task["task_mode"] == "Repeat":
            self._schedule_task(task)
    
    def _process_pending_tasks(self):
        while self.is_running:
            if self.pending_tasks and not getattr(self.chat_session, "is_processing", False):
                with self.lock:
                    if self.pending_tasks:
                        task = self.pending_tasks.pop(0)
                        if self.on_task_fire:
                            self.on_task_fire(task)
            time.sleep(0.5)


class ChatSession:
    def __init__(self, agent_name, script_dir=None):
        self.agent_name = agent_name
        self.script_dir = script_dir or os.path.dirname(os.path.abspath(__file__))
        self.config = load_agent_config(agent_name, script_dir)
        self.messages = []
        self.is_active = False
        self.is_processing = False
        self.max_context = 2048
        self.task_scheduler = None
        
        self.episodic_memory = get_episodic_memory(agent_name)
        self.skill_lessons = get_skill_lessons(agent_name)
        self.user_prefs = get_user_preferences(agent_name)
        self.pattern_detector = get_pattern_detector(agent_name)
        self.session_actions = []
        system_content = ""
        if self.config["system_prompt"]:
            system_content = self.config["system_prompt"]
        db_content = self._load_connected_databases()
        if db_content:
            if system_content:
                system_content += "\n\n"
            system_content += db_content
        
        if system_content:
            self.messages.append({"role": "system", "content": system_content})
        
        if self.config["model"]:
            self.max_context = get_model_max_context(self.config["model"])
    
    def _load_connected_databases(self):
        connected_db_names = self.config.get("connected_dbs", [])
        if not connected_db_names:
            return ""
        db_paths = self._get_database_paths(connected_db_names)
        if not db_paths:
            return ""
        
        db_sections = []
        for db_name, db_path in db_paths.items():
            if os.path.isfile(db_path):
                db_sections.append(f"- {db_name}: {db_path} (file)")
            elif os.path.isdir(db_path):
                db_sections.append(f"- {db_name}: {db_path} (folder)")
            else:
                db_sections.append(f"- {db_name}: {db_path} (not found)")
        
        if db_sections:
            return "You have access to the following databases. Use the files.py tools (read_file, list_directory, search_files, etc.) to explore them as needed:\n" + "\n".join(db_sections)
        return ""
    
    def _get_database_paths(self, db_names):
        if not db_names:
            return {}
        script_dir = self.script_dir
        if script_dir is None:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            script_dir = os.path.dirname(os.path.dirname(script_dir))
        
        db_file = os.path.join(script_dir, "Backend", "SavedInfo", "Databases.txt")
        db_map = {}
        if os.path.isfile(db_file):
            try:
                with open(db_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("Name: "):
                            parts = line.split("|")
                            if parts:
                                name_part = parts[0].replace("Name: ", "").strip()
                                if name_part and len(parts) > 0:
                                    for part in parts:
                                        if part.strip().startswith("FilePath: "):
                                            path = part.strip().replace("FilePath: ", "").strip()
                                            db_map[name_part] = path
                                            break
            except Exception:
                pass
        result = {}
        for db_name in db_names:
            if db_name in db_map:
                result[db_name] = db_map[db_name]
        return result
    
    def start(self):
        self.is_active = True
    
    def end(self):
        self.is_active = False
        self.messages = []
    
    def get_context_info(self):
        total_tokens = 0
        for msg in self.messages:
            total_tokens += len(msg.get("content", "").split())

        system_tokens = 0
        for msg in self.messages:
            if msg.get("role") == "system":
                system_tokens += len(msg.get("content", "").split())

        prompt_tokens = 0
        for msg in self.messages:
            if msg.get("role") == "user":
                prompt_tokens += len(msg.get("content", "").split())
        memory_context = get_memory_context_for_prompt("", self.agent_name)
        memory_tokens = len(memory_context.split()) if memory_context else 0

        enabled_tools = self.config.get("enabled_tools", [])
        tools_count = len(enabled_tools)
        tools_tokens = 0

        if enabled_tools and ALL_TOOLS:
            for tool in ALL_TOOLS:
                tool_name = tool.get("function", {}).get("name", "")
                if tool_name in enabled_tools:
                    description = tool.get("function", {}).get("description", "")
                    params = str(tool.get("function", {}).get("parameters", {}))
                    tools_tokens += len(description) // 4 + len(params) // 4

        return {
            "max_context": self.max_context,
            "total_tokens": total_tokens,
            "system_tokens": system_tokens,
            "prompt_tokens": prompt_tokens,
            "memory_tokens": memory_tokens,
            "tools_tokens": tools_tokens,
            "tools_count": tools_count
        }
    
    def send_message(self, message, on_response, on_error, on_stream=None, on_tool_call=None):
        if not self.is_active:
            on_error("Chat session not started")
            return
        
        if not self.config["model"]:
            on_error("No model configured for this agent")
            return
        self.is_processing = True
        self.pattern_detector.record_action("user_message", {"content": message[:50]})
        self.session_actions.append({"type": "user_message", "content": message[:50]})
        self.messages.append({"role": "user", "content": message})
        memory_context = get_memory_context_for_prompt(message, self.agent_name)
        messages_with_memory = self.messages.copy()
        if memory_context:
            messages_with_memory.insert(-1, {
                "role": "system",
                "content": f"You have access to past learning and memories:\n{memory_context}"
            })
        
        filtered_tools = self._get_filtered_tools()
        
        def handle_response(content, updated_messages):
            self.is_processing = False
            if memory_context and len(updated_messages) > 1:
                for i, msg in enumerate(updated_messages):
                    if msg.get("role") == "system" and "past learning and memories" in msg.get("content", ""):
                        updated_messages.pop(i)
                        break
            self.messages = updated_messages
            summary = summarize_conversation(self.messages[-4:])
            if summary:
                self.episodic_memory.add_memory(
                    summary=summary,
                    context={"model": self.config["model"], "tools_used": []},
                    importance=1.0
                )
            detected_pattern = self.pattern_detector.detect_patterns()
            if detected_pattern:
                print(f"[Memory] Detected pattern: {detected_pattern['action_type']} ({detected_pattern['occurrences']} occurrences)")
            if len(self.messages) % 6 == 0:
                self._perform_self_reflection()
            self.episodic_memory.auto_consolidate(max_memories=100)
            on_response(content)
        
        def handle_error(error):
            self.is_processing = False
            error_str = str(error)
            if "tool" in error_str.lower() or any(tool in error_str.lower() for tool in ["file", "web", "search", "browser", "read", "write"]):
                self.skill_lessons.add_lesson(
                    skill_name="general",
                    error=error_str[:200],
                    lesson=f"Tool execution failed: {error_str[:100]}",
                    solution="Check tool parameters and try again"
                )
            on_error(error)
        
        def handle_tool_call(name, args):
            set_current_agent(self.agent_name)
            self.pattern_detector.record_action("tool_call", {"tool": name, "args": list(args.keys())})
            self.session_actions.append({"type": "tool_call", "tool": name})
            if on_tool_call:
                on_tool_call(name, args)
        
        chat_with_api(
            model_name=self.config["model"],
            messages=messages_with_memory,
            on_response=handle_response,
            on_error=handle_error,
            on_stream=on_stream,
            on_tool_call=handle_tool_call,
            filtered_tools=filtered_tools,
            agent_config=self.config
        )
    
    def _get_filtered_tools(self):
        enabled_tools = self.config.get("enabled_tools", [])
        if not enabled_tools:
            return []
        return [t for t in ALL_TOOLS if t["function"]["name"] in enabled_tools]
    
    def _perform_self_reflection(self):
        recent = self.messages[-6:] if len(self.messages) >= 6 else self.messages
        if not recent:
            return
        tool_failures = []
        for msg in recent:
            content = msg.get("content", "")
            if "Error:" in content or "failed" in content.lower():
                tool_failures.append(content[:100])
        
        if tool_failures:
            lesson = f"Recent tool failures: {', '.join(tool_failures[:2])}"
            self.skill_lessons.add_lesson(
                skill_name="general",
                error=tool_failures[0],
                lesson=lesson,
                solution="Review tool usage and parameters"
            )
            print(f"[Memory] Self-reflection recorded: {lesson}")
    
    def clear_history(self):
        self.messages = []
        system_content = ""
        if self.config["system_prompt"]:
            system_content = self.config["system_prompt"]
        
        db_content = self._load_connected_databases()
        if db_content:
            if system_content:
                system_content += "\n\n"
            system_content += db_content
        
        if system_content:
            self.messages.append({"role": "system", "content": system_content})


class ChatManager:
    def __init__(self, script_dir=None):
        self.script_dir = script_dir
        self.current_session = None
        self.ollama_process = None
        self.on_task_fire = None
    
    def start_ollama(self):
        try:
            import psutil
            for proc in psutil.process_iter(['name']):
                try:
                    if proc.info['name'] and 'ollama' in proc.info['name'].lower():
                        return True, "Ollama already running"
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        except:
            pass
        
        try:
            if sys.platform == "win32":
                self.ollama_process = subprocess.Popen(
                    ["ollama", "serve"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                )
            else:
                self.ollama_process = subprocess.Popen(
                    ["ollama", "serve"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True
                )
            time.sleep(2)
            return True, "Ollama started"
        except Exception as e:
            return False, f"Failed to start Ollama: {e}"
    
    def stop_ollama(self):
        if self.ollama_process:
            try:
                self.ollama_process.terminate()
                self.ollama_process.wait(timeout=5)
                self.ollama_process = None
                return True, "Ollama stopped"
            except subprocess.TimeoutExpired:
                try:
                    self.ollama_process.kill()
                    self.ollama_process.wait(timeout=2)
                    self.ollama_process = None
                    return True, "Ollama force killed"
                except Exception as e:
                    return False, f"Error killing Ollama: {e}"
            except Exception as e:
                return False, f"Error stopping Ollama: {e}"
        
        try:
            import psutil
            killed = False
            for proc in psutil.process_iter(['name']):
                try:
                    if proc.info['name'] and 'ollama' in proc.info['name'].lower():
                        proc.terminate()
                        killed = True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            if killed:
                return True, "Ollama processes killed"
            return True, "No Ollama process to stop"
        except:
            return True, "No Ollama process to stop"
    
    def start_chat(self, agent_name, tasks_enabled=False, on_task_fire=None):
        success, msg = self.start_ollama()
        if not success:
            return None, msg
        
        self.current_session = ChatSession(agent_name, self.script_dir)
        self.current_session.start()
        if tasks_enabled and on_task_fire:
            self.on_task_fire = on_task_fire
            self.current_session.task_scheduler = TaskScheduler(self.current_session, on_task_fire)
            self.current_session.task_scheduler.start(self.script_dir)
        
        return self.current_session, msg
    
    def end_chat(self):
        if self.current_session:
            if self.current_session.task_scheduler:
                self.current_session.task_scheduler.stop()
                self.current_session.task_scheduler = None
            self.current_session.end()
            self.current_session = None
        self.stop_ollama()
    
    def get_session(self):
        return self.current_session
    
    def is_chat_active(self):
        return self.current_session is not None and self.current_session.is_active


class ConvoManager:
    def __init__(self, script_dir=None):
        self.script_dir = script_dir or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.convos_dir = os.path.join(self.script_dir, "Backend", "SavedInfo", "Convos")
    
    def _ensure_dir(self):
        os.makedirs(self.convos_dir, exist_ok=True)
    
    def _name_to_filename(self, name):
        filename = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        return filename.replace(' ', '_') + ".txt"
    
    def _filename_to_name(self, filename):
        return filename.replace('.txt', '').replace('_', ' ')
    
    def save_convo(self, name, content):
        self._ensure_dir()
        filename = self._name_to_filename(name)
        filepath = os.path.join(self.convos_dir, filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return True, filename
    
    def update_convo(self, name, content):
        filename = self._name_to_filename(name)
        filepath = os.path.join(self.convos_dir, filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    
    def load_convo(self, filename):
        filepath = os.path.join(self.convos_dir, filename)
        
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        
        display_name = self._filename_to_name(filename)
        return content, display_name
    
    def delete_convo(self, filename):
        filepath = os.path.join(self.convos_dir, filename)
        os.remove(filepath)
        return True
    
    def list_convos(self):
        try:
            files = [f for f in os.listdir(self.convos_dir) if f.endswith('.txt')]
            return sorted(files)
        except:
            return []


class ChatUIBuilder:

    def __init__(self, parent_notebook, colors, fonts, callbacks):
        self.notebook = parent_notebook
        self.colors = colors
        self.fonts = fonts
        self.callbacks = callbacks
        self.widgets = {}
        self.vars = {}
    
    def build_chat_tab(self):
        frame = tk.Frame(self.notebook, bg=self.colors["bg"])
        self.notebook.add(frame, text="Chat")
        
        container = tk.Frame(frame, bg=self.colors["bg"])
        container.pack(fill=tk.BOTH, expand=True)
        left_sidebar = tk.Frame(container, bg=self.colors["bg_light"], width=150)
        left_sidebar.pack(side=tk.LEFT, fill=tk.Y)
        left_sidebar.pack_propagate(False)
        
        tk.Label(left_sidebar, text="Conversations", font=self.fonts["font_bold"], bg=self.colors["bg_light"], fg=self.colors["fg"]).pack(anchor=tk.W, padx=10, pady=(10, 5))
        
        tk.Button(left_sidebar, text="Save Convo", bg=self.colors["bg_lighter"], fg=self.colors["fg"],
                  font=self.fonts["font_bold"], relief=tk.FLAT, bd=0,
                  command=self.callbacks["save_convo"]).pack(fill=tk.X, padx=5, pady=2)
        
        tk.Button(left_sidebar, text="Delete Convo", bg=self.colors["bg_lighter"], fg=self.colors["fg"],
                  font=self.fonts["font_bold"], relief=tk.FLAT, bd=0,
                  command=self.callbacks["delete_convo"]).pack(fill=tk.X, padx=5, pady=2)
        tk.Frame(left_sidebar, bg=self.colors["fg"], height=1).pack(fill=tk.X, padx=5, pady=5)
        self.widgets["saved_convos_frame"] = tk.Frame(left_sidebar, bg=self.colors["bg_light"])
        self.widgets["saved_convos_frame"].pack(fill=tk.X, expand=True, anchor=tk.N)
        
        content_frame = tk.Frame(container, bg=self.colors["bg"])
        content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(content_frame, text="Chat", font=self.fonts["font_title"], bg=self.colors["bg"], fg=self.colors["fg"]).pack(pady=(0, 10))
        
        top_bar = tk.Frame(content_frame, bg=self.colors["bg"])
        top_bar.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(top_bar, text="Agent:", font=self.fonts["font_bold"], bg=self.colors["bg"], fg=self.colors["fg"]).pack(side=tk.LEFT)
        
        self.vars["agent"] = tk.StringVar(value="No agents")
        self.widgets["agent_combo"] = ttk.Combobox(top_bar, textvariable=self.vars["agent"],
                                        values=[], state="readonly", width=30)
        self.widgets["agent_combo"].pack(side=tk.LEFT, padx=(8, 0))
        
        tk.Button(top_bar, text="Refresh", bg=self.colors["bg_lighter"], fg=self.colors["fg"],
                  font=self.fonts["font_bold"], relief=tk.RAISED, bd=2,
                  command=self.callbacks["refresh_agents"]).pack(side=tk.LEFT, padx=(8, 0))
        
        btn_frame = tk.Frame(top_bar, bg=self.colors["bg"])
        btn_frame.pack(side=tk.LEFT, padx=(20, 0), fill=tk.X, expand=True)
        
        self.widgets["convo_name_label"] = tk.Label(top_bar, text="Convo Name: Not Saved", font=self.fonts["font_bold"], bg=self.colors["bg"], fg=self.colors["fg"])
        self.widgets["convo_name_label"].pack(side=tk.RIGHT)
        
        mode_bar = tk.Frame(content_frame, bg=self.colors["bg"])
        mode_bar.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(mode_bar, text="Chat Mode:", font=self.fonts["font_bold"], bg=self.colors["bg"], fg=self.colors["fg"]).pack(side=tk.LEFT)
        
        self.vars["chat_mode"] = tk.StringVar(value="Normal")
        self.widgets["chat_mode_combo"] = ttk.Combobox(mode_bar, textvariable=self.vars["chat_mode"],
                                            values=["Normal", "Tasks Enabled"], state="readonly", width=15)
        self.widgets["chat_mode_combo"].pack(side=tk.LEFT, padx=(8, 0))
        
        self.widgets["start_chat_btn"] = tk.Button(btn_frame, text="Start Chat", bg=self.colors["bg_lighter"], fg=self.colors["fg"],
                  font=self.fonts["font_bold"], relief=tk.RAISED, bd=2,
                  command=self.callbacks["start_chat"])
        self.widgets["start_chat_btn"].pack(side=tk.LEFT, padx=(0, 5))
        
        self.widgets["end_chat_btn"] = tk.Button(btn_frame, text="End Chat", bg="#aa3333", fg=self.colors["fg"],
                  font=self.fonts["font_bold"], relief=tk.RAISED, bd=2,
                  command=self.callbacks["end_chat"], state="disabled")
        self.widgets["end_chat_btn"].pack(side=tk.LEFT, padx=(0, 5))
        
        tk.Button(btn_frame, text="Clear Chat", bg=self.colors["bg_lighter"], fg=self.colors["fg"],
                  font=self.fonts["font_bold"], relief=tk.RAISED, bd=2,
                  command=self.callbacks["clear_chat"]).pack(side=tk.LEFT)
        
        self.widgets["thinking_label"] = tk.Label(content_frame, text="", font=self.fonts["font_bold"], bg=self.colors["bg"], fg="#ffff00")
        self.widgets["thinking_label"].pack(anchor=tk.W)
        
        tk.Label(content_frame, text="Chat History:", font=self.fonts["font_bold"], bg=self.colors["bg"], fg=self.colors["fg"]).pack(anchor=tk.W)
        
        self.widgets["chat_history"] = scrolledtext.ScrolledText(
            content_frame, bg=self.colors["bg_light"], fg=self.colors["fg"], font=self.fonts["font_mono"],
            wrap=tk.WORD, state="disabled"
        )
        self.widgets["chat_history"].pack(fill=tk.BOTH, expand=True, pady=(5, 10))
        self.widgets["chat_history"].tag_configure("user", foreground=self.colors["fg"])
        self.widgets["chat_history"].tag_configure("model", foreground=self.colors["green"])
        
        input_frame = tk.Frame(content_frame, bg=self.colors["bg"])
        input_frame.pack(fill=tk.X)
        
        top_context_frame = tk.Frame(input_frame, bg=self.colors["bg"])
        top_context_frame.pack(anchor=tk.W, pady=(0, 5))
        
        self.widgets["max_context_label"] = tk.Label(top_context_frame, text="Model's Max Context: Unknown", font=self.fonts["font_bold"], bg=self.colors["bg"], fg=self.colors["blue"])
        self.widgets["max_context_label"].pack(side=tk.LEFT, padx=(0, 20))
        
        self.widgets["total_context_label"] = tk.Label(top_context_frame, text="Context Total: 0 tokens", font=self.fonts["font_bold"], bg=self.colors["bg"], fg=self.colors["green"])
        self.widgets["total_context_label"].pack(side=tk.LEFT)
        
        context_frame = tk.Frame(input_frame, bg=self.colors["bg"])
        context_frame.pack(anchor=tk.W, pady=(0, 5))
        
        self.widgets["memory_context_label"] = tk.Label(context_frame, text="Memory Context: 0 tokens", font=self.fonts["font"], bg=self.colors["bg"], fg=self.colors["fg"])
        self.widgets["memory_context_label"].pack(side=tk.LEFT, padx=(0, 15))
        
        self.widgets["tools_context_label"] = tk.Label(context_frame, text="Tools Context: 0 tokens", font=self.fonts["font"], bg=self.colors["bg"], fg=self.colors["fg"])
        self.widgets["tools_context_label"].pack(side=tk.LEFT, padx=(0, 15))
        
        self.widgets["system_prompt_label"] = tk.Label(context_frame, text="System Prompt: 0 tokens", font=self.fonts["font"], bg=self.colors["bg"], fg=self.colors["fg"])
        self.widgets["system_prompt_label"].pack(side=tk.LEFT, padx=(0, 15))
        
        self.widgets["context_label"] = tk.Label(context_frame, text="Prompt Context: 0 tokens", font=self.fonts["font"], bg=self.colors["bg"], fg=self.colors["fg"])
        self.widgets["context_label"].pack(side=tk.LEFT)
        
        inner_frame = tk.Frame(input_frame, bg=self.colors["bg"])
        inner_frame.pack(fill=tk.X)
        
        self.widgets["attach_btn"] = tk.Button(inner_frame, text="📎", bg=self.colors["bg_lighter"], fg=self.colors["fg"],
                  font=self.fonts["font_bold"], relief=tk.RAISED, bd=2,
                  command=self.callbacks["attach_file"], state="disabled")
        self.widgets["attach_btn"].pack(side=tk.LEFT, padx=(0, 5))
        
        self.widgets["attached_label"] = tk.Label(inner_frame, text="", font=self.fonts["font"], bg=self.colors["bg"], fg=self.colors["fg"])
        self.widgets["attached_label"].pack(side=tk.LEFT, padx=(0, 5))
        
        self.widgets["chat_input"] = tk.Entry(inner_frame, font=self.fonts["font"], bg=self.colors["bg_light"], fg=self.colors["fg"],
                                   insertbackground=self.colors["fg"], state="disabled")
        self.widgets["chat_input"].pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.widgets["chat_input"].bind("<Return>", lambda e: self.callbacks["send_message"]())
        
        self.widgets["send_btn"] = tk.Button(inner_frame, text="Send", bg=self.colors["bg_lighter"], fg=self.colors["fg"],
                  font=self.fonts["font_bold"], relief=tk.RAISED, bd=2,
                  command=self.callbacks["send_message"], state="disabled")
        self.widgets["send_btn"].pack(side=tk.LEFT, padx=(0, 5))
        
        self.widgets["context_check_btn"] = tk.Button(inner_frame, text="Context Check", bg=self.colors["bg_lighter"], fg=self.colors["fg"],
                  font=self.fonts["font_bold"], relief=tk.RAISED, bd=2,
                  command=self.callbacks["check_context"], state="disabled")
        self.widgets["context_check_btn"].pack(side=tk.LEFT)
        
        return frame
    
    def get_widget(self, name):
        return self.widgets.get(name)
    
    def get_var(self, name):
        return self.vars.get(name)
