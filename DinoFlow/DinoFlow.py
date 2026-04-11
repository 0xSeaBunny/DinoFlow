import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import sys
import os
import webbrowser

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "Backend", "Extra"))
from Agents import AgentManager, AgentUIBuilder, save_agent, update_agent, delete_agent, delete_agent_memory, load_agent, get_database_names
from Chat import ChatManager, ChatSession, ConvoManager, ChatUIBuilder
from Tasks import TaskManager, TaskUIBuilder, save_task, update_task, delete_task, load_task
from Databases import DatabaseManager, DatabaseUIBuilder, save_database, update_database, delete_database
from Settings import SettingsManager, SettingsUIBuilder, save_settings, load_settings

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "Backend", "MainScripts"))
from ollama_manager import get_installed_models, uninstall_model, download_model, get_model_folder
from api_chat import get_model_max_context

try:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "Backend", "MainScripts", "RemoteChats"))
    from TelegramBot import telegram_bot_manager, TelegramUIBuilder, save_telegram_token, load_telegram_token
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    telegram_bot_manager = None
    TelegramUIBuilder = None

try:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "Backend", "MainScripts", "RemoteChats"))
    from Discord import bot_manager as discord_bot_manager
    from Discord.discord_bot import DiscordUIBuilder, save_discord_token, load_discord_token, save_discord_channel, load_discord_channel
    DISCORD_AVAILABLE = True
except ImportError:
    DISCORD_AVAILABLE = False
    discord_bot_manager = None
    DiscordUIBuilder = None


BG = "#2b2b2b"
BG_LIGHT = "#3c3c3c"
BG_LIGHTER = "#4a4a4a"
FG = "white"
GREEN = "#00ff00"
BLUE = "#00aaff"
FONT = ("Arial", 10)
FONT_BOLD = ("Arial", 10, "bold")
FONT_TITLE = ("Arial", 16, "bold")
FONT_MONO = ("Consolas", 10)


class DinoFlow:
    def __init__(self, root):
        self.root = root
        self.root.title("DinoFlow")
        self.root.geometry("1200x800")
        self.root.configure(bg=BG)
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.agent_manager = AgentManager(script_dir)
        
        self.task_manager = TaskManager(script_dir)
        
        self.chat_manager = ChatManager(script_dir)
        
        self.db_manager = DatabaseManager(script_dir)
        self.settings_manager = SettingsManager(script_dir)
        self.convo_manager = ConvoManager(script_dir)
        self.chat_session = None
        
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook", background=BG)
        style.configure("TNotebook.Tab", background=BG_LIGHT, foreground=FG, padding=[12, 5])
        style.map("TNotebook.Tab", background=[("selected", BG_LIGHTER)])
        style.configure("TFrame", background=BG)
        
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self._models_cache = None
        
        self._init_chat_tab()
        self._init_agents_tab()
        self._init_tasks_tab()
        self._init_databases_tab()
        self._init_manage_models_tab()
        self._init_remote_chats_tab()
        self._init_settings_tab()
        
        self._refresh_chat_agents()
    
    def _refresh_chat_agents(self):
        agents = self.agent_manager.get_agent_names()
        self.agent_combo.config(values=agents)
        if agents and agents[0] != "No agents available":
            self.agent_var.set(agents[0])
        else:
            self.agent_var.set("No agents")
    
    def _init_chat_tab(self):
        colors = {"bg": BG, "bg_light": BG_LIGHT, "bg_lighter": BG_LIGHTER, "fg": FG, "green": GREEN, "blue": BLUE}
        fonts = {"font": FONT, "font_bold": FONT_BOLD, "font_title": FONT_TITLE, "font_mono": FONT_MONO}
        callbacks = {
            "save_convo": self._save_convo,
            "delete_convo": self._delete_convo,
            "refresh_agents": self._refresh_chat_agents,
            "start_chat": self._start_chat,
            "end_chat": self._end_chat,
            "clear_chat": self._clear_chat,
            "attach_file": self._attach_file,
            "send_message": self._send_message,
            "check_context": self._check_context
        }
        
        self.chat_ui = ChatUIBuilder(self.notebook, colors, fonts, callbacks)
        self.chat_ui.build_chat_tab()
        self.saved_convos_frame = self.chat_ui.get_widget("saved_convos_frame")
        self.agent_combo = self.chat_ui.get_widget("agent_combo")
        self.agent_var = self.chat_ui.get_var("agent")
        self.convo_name_label = self.chat_ui.get_widget("convo_name_label")
        self.start_chat_btn = self.chat_ui.get_widget("start_chat_btn")
        self.end_chat_btn = self.chat_ui.get_widget("end_chat_btn")
        self.send_btn = self.chat_ui.get_widget("send_btn")
        self.chat_input = self.chat_ui.get_widget("chat_input")
        self.attach_btn = self.chat_ui.get_widget("attach_btn")
        self.context_check_btn = self.chat_ui.get_widget("context_check_btn")
        self.thinking_label = self.chat_ui.get_widget("thinking_label")
        self.chat_history = self.chat_ui.get_widget("chat_history")
        self.max_context_label = self.chat_ui.get_widget("max_context_label")
        self.total_context_label = self.chat_ui.get_widget("total_context_label")
        self.system_prompt_label = self.chat_ui.get_widget("system_prompt_label")
        self.context_label = self.chat_ui.get_widget("context_label")
        self.memory_context_label = self.chat_ui.get_widget("memory_context_label")
        self.tools_context_label = self.chat_ui.get_widget("tools_context_label")
        self.attached_label = self.chat_ui.get_widget("attached_label")
        self._refresh_saved_convos()
    
    def _save_convo(self):
        if not self.chat_session or not self.chat_session.is_active:
            messagebox.showwarning("No Active Chat", "Please start a chat first.")
            return
        
        content = self.chat_history.get(1.0, tk.END).strip()
        
        if hasattr(self, '_current_convo_name') and self._current_convo_name:
            try:
                self.convo_manager.update_convo(self._current_convo_name, content)
                messagebox.showinfo("Success", f"Conversation '{self._current_convo_name}' updated.")
                self._refresh_saved_convos()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save: {e}")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Save Conversation")
        dialog.geometry("300x120")
        dialog.configure(bg=BG)
        dialog.transient(self.root)
        dialog.grab_set()
        
        tk.Label(dialog, text="Convo Name:", font=FONT_BOLD, bg=BG, fg=FG).pack(pady=(10, 5))
        
        name_var = tk.StringVar()
        entry = tk.Entry(dialog, textvariable=name_var, font=FONT, bg=BG_LIGHT, fg=FG, width=30)
        entry.pack(pady=5)
        entry.focus()
        
        def do_save():
            name = name_var.get().strip()
            if not name:
                messagebox.showwarning("No Name", "Please enter a conversation name.")
                return
            
            try:
                self.convo_manager.save_convo(name, content)
                messagebox.showinfo("Success", f"Conversation saved as '{name}'")
                self._current_convo_name = name
                self._update_convo_name_label(name)
                dialog.destroy()
                self._refresh_saved_convos()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save: {e}")
        
        tk.Button(dialog, text="Save", bg=BG_LIGHTER, fg=FG, font=FONT_BOLD,
                 relief=tk.RAISED, bd=2, command=do_save).pack(pady=10)
    
    def _refresh_saved_convos(self):
        for widget in self.saved_convos_frame.winfo_children():
            widget.destroy()
        
        files = self.convo_manager.list_convos()
        
        if not files:
            tk.Label(self.saved_convos_frame, text="No saved convos", 
                    font=FONT, bg=BG_LIGHT, fg=FG).pack(anchor=tk.N, pady=10)
            return
        
        for filename in files:
            display_name = self.convo_manager._filename_to_name(filename)
            btn = tk.Button(self.saved_convos_frame, text=display_name, bg=BG_LIGHTER, fg=FG,
                           font=FONT, relief=tk.FLAT, bd=0,
                           command=lambda f=filename: self._load_convo(f))
            btn.pack(fill=tk.X, padx=5, pady=1, anchor=tk.N)
    
    def _load_convo(self, filename):
        try:
            content, display_name = self.convo_manager.load_convo(filename)
            
            self.chat_history.config(state="normal")
            self.chat_history.delete(1.0, tk.END)
            self.chat_history.insert(tk.END, content)
            self.chat_history.config(state="disabled")
            self.chat_history.see(tk.END)
            self._current_convo_name = display_name
            self._update_convo_name_label(display_name)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load conversation: {e}")
    
    def _delete_convo(self):
        files = self.convo_manager.list_convos()
        
        if not files:
            messagebox.showinfo("No Convos", "No saved conversations to delete.")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Delete Conversation")
        dialog.geometry("300x300")
        dialog.configure(bg=BG)
        dialog.transient(self.root)
        dialog.grab_set()
        
        tk.Label(dialog, text="Select conversation to delete:", font=FONT_BOLD, bg=BG, fg=FG).pack(pady=10)
        
        list_frame = tk.Frame(dialog, bg=BG)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        for filename in files:
            display_name = self.convo_manager._filename_to_name(filename)
            btn = tk.Button(list_frame, text=display_name, bg="#aa3333", fg=FG,
                           font=FONT, relief=tk.FLAT, bd=0,
                           command=lambda f=filename: do_delete(f))
            btn.pack(fill=tk.X, pady=2)
        
        def do_delete(filename):
            try:
                self.convo_manager.delete_convo(filename)
                messagebox.showinfo("Success", "Conversation deleted.")
                dialog.destroy()
                self._refresh_saved_convos()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete: {e}")
    
    def _update_convo_name_label(self, name):
        if name:
            self.convo_name_label.config(text=f"Convo Name: {name}")
        else:
            self.convo_name_label.config(text="Convo Name: Not Saved")
    
    def _get_model_names(self):
        models, error = get_installed_models()
        if models:
            return [m["name"] for m in models]
        return ["No models available"]
    
    def _refresh_agents_list(self):
        for widget in self.agents_list_frame.winfo_children():
            widget.destroy()
        
        agents = self.agent_manager.get_agent_names()
        
        if not agents or agents == ["No agents available"]:
            tk.Label(self.agents_list_frame, text="No agents yet", 
                    font=FONT, bg=BG_LIGHT, fg=FG).pack(anchor=tk.N, pady=10)
            return
        
        for agent_name in agents:
            if agent_name != "No agents available":
                btn = tk.Button(self.agents_list_frame, text=agent_name, bg=BG_LIGHTER, fg=FG,
                               font=FONT, relief=tk.FLAT, bd=0,
                               command=lambda n=agent_name: self._view_agent(n))
                btn.pack(fill=tk.X, padx=5, pady=1, anchor=tk.N)
    
    def _start_chat(self):
        agent_name = self.agent_var.get()
        if not agent_name or agent_name == "No agents":
            messagebox.showwarning("No Agent", "Please select an agent first.")
            return
        chat_mode = self.chat_ui.get_var("chat_mode").get()
        tasks_enabled = chat_mode == "Tasks Enabled"
        def on_task_fire(task):
            self.root.after(0, lambda: self._handle_task_fire(task))
        
        result = self.chat_manager.start_chat(agent_name, tasks_enabled=tasks_enabled, on_task_fire=on_task_fire)
        if isinstance(result, tuple):
            self.chat_session, msg = result
        else:
            self.chat_session = result
            msg = "Chat started"
        
        if not self.chat_session:
            messagebox.showerror("Error", f"Failed to start chat session: {msg}")
            return
        
        self._update_context_labels()
        
        self.start_chat_btn.config(state="disabled")
        self.end_chat_btn.config(state="normal")
        self.send_btn.config(state="normal")
        self.chat_input.config(state="normal")
        self.attach_btn.config(state="normal")
        self.context_check_btn.config(state="normal")
        
        self._update_convo_name_label(None)
        
        self._append_chat(f"Started chat with agent: {agent_name}", "model")
        if TELEGRAM_AVAILABLE and telegram_bot_manager.is_running():
            telegram_bot_manager.unpause()
        if DISCORD_AVAILABLE and discord_bot_manager.is_running():
            discord_bot_manager.unpause()
    
    def _handle_task_fire(self, task):
        task_name = task.get("name", "Unknown Task")
        task_prompt = task.get("description", "")
        self._append_chat(f"\n[Task Fired: {task_name}]", "model")
        if task_prompt:
            self._append_chat(f"Task Prompt: {task_prompt}\n", "model")
        self._send_to_discord(f"[Task Fired: {task_name}]")
        if task_prompt and self.chat_session:
            self.thinking_label.config(text="Processing task...")
            self._update_context_labels()

            def on_response(content):
                self.thinking_label.config(text="")
                self._append_chat(f"{content}\n", "model")
                self._update_context_labels()
                self._send_to_discord(f"Agent (Task: {task_name}): {content}")

            def on_error(error):
                self.thinking_label.config(text="")
                self._append_chat(f"[Task Error: {error}]\n", "model")
                self._send_to_discord(f"[Task Error: {error}]")

            self.chat_session.send_message(
                task_prompt,
                on_response=on_response,
                on_error=on_error
            )
    
    def _end_chat(self):
        self.chat_manager.end_chat()
        self.chat_session = None
        self._update_convo_name_label(None)
        if TELEGRAM_AVAILABLE and telegram_bot_manager.is_running():
            telegram_bot_manager.pause()
        if DISCORD_AVAILABLE and discord_bot_manager.is_running():
            discord_bot_manager.pause()
        
        self.start_chat_btn.config(state="normal")
        self.end_chat_btn.config(state="disabled")
        self.send_btn.config(state="disabled")
        self.chat_input.config(state="disabled")
        self.attach_btn.config(state="disabled")
        self.context_check_btn.config(state="disabled")
        self.thinking_label.config(text="")
        if hasattr(self, '_attached_path'):
            self._attached_path = None
        if hasattr(self, 'attached_label'):
            self.attached_label.config(text="")
    
    def _clear_chat(self):
        self.chat_history.config(state="normal")
        self.chat_history.delete(1.0, tk.END)
        self.chat_history.config(state="disabled")
        
        if self.chat_session:
            self.chat_session.clear_history()
            self._update_context_labels()
    
    def _attach_file(self):
        from tkinter import filedialog
        if hasattr(self, '_attached_path') and self._attached_path:
            self._attached_path = None
            self.attached_label.config(text="")
            return
        path = filedialog.askopenfilename(title="Select a file")
        if not path:
            path = filedialog.askdirectory(title="Select a folder")
        
        if path:
            self._attached_path = path
            self.attached_label.config(text=f"📎 {os.path.basename(path)}")
    
    def _send_message(self):
        if not self.chat_session or not self.chat_session.is_active:
            return
        
        message = self.chat_input.get().strip()
        if not message:
            return
        if hasattr(self, '_attached_path') and self._attached_path:
            message = f"{message}\n\n[Attached: {self._attached_path}]"
            self._attached_path = None
            self.attached_label.config(text="")
        
        self.chat_input.delete(0, tk.END)
        self._append_chat(f"You: {message}\n", "user")
        self._send_to_discord(f"You: {message}")
        if TELEGRAM_AVAILABLE:
            from RemoteChats.TelegramBot import set_thinking as set_telegram_thinking
            set_telegram_thinking(True)
        if DISCORD_AVAILABLE:
            from RemoteChats.Discord.discord_bot import set_thinking as set_discord_thinking
            set_discord_thinking(True)
        
        self.send_btn.config(state="disabled")
        self.thinking_label.config(text="Thinking...")
        self.root.update()
        
        def on_response(response):
            def update_ui():
                self.thinking_label.config(text="")
                self._append_chat(f"Agent: {response}\n\n", "model")
                self.send_btn.config(state="normal")
                self._update_context_labels()
                self._send_to_discord(f"Agent: {response}")
                if TELEGRAM_AVAILABLE:
                    from RemoteChats.TelegramBot import set_thinking as set_telegram_thinking
                    set_telegram_thinking(False)
                if DISCORD_AVAILABLE:
                    from RemoteChats.Discord.discord_bot import set_thinking as set_discord_thinking
                    set_discord_thinking(False)
            self.root.after(0, update_ui)
        
        def on_error(error_msg):
            def update_ui():
                self.thinking_label.config(text="")
                self._append_chat(f"Error: {error_msg}\n\n", "model")
                self.send_btn.config(state="normal")
                self._send_to_discord(f"Error: {error_msg}")
                if TELEGRAM_AVAILABLE:
                    from RemoteChats.TelegramBot import set_thinking as set_telegram_thinking
                    set_telegram_thinking(False)
                if DISCORD_AVAILABLE:
                    from RemoteChats.Discord.discord_bot import set_thinking as set_discord_thinking
                    set_discord_thinking(False)
            self.root.after(0, update_ui)
        
        def on_tool_call(name, args):
            def update_ui():
                self.thinking_label.config(text=f"Using tool: {name}...")
                self._append_chat(f"[Tool: {name}]\n", "model")
                self._send_to_discord(f"[Tool: {name}]")
            self.root.after(0, update_ui)
        
        self.chat_session.send_message(message, on_response, on_error, on_tool_call=on_tool_call)
    
    def _send_to_telegram(self, message):
        if not TELEGRAM_AVAILABLE:
            return
        if not telegram_bot_manager or not telegram_bot_manager.is_running():
            return
        chat_id = getattr(self, '_last_telegram_chat_id', None)
        if not chat_id:
            return
        
        try:
            import threading
            def send():
                try:
                    telegram_bot_manager.send_message_to_chat(chat_id, message)
                except:
                    pass
            threading.Thread(target=send, daemon=True).start()
        except:
            pass
    
    def _append_chat(self, text, tag):
        self.chat_history.config(state="normal")
        self.chat_history.insert(tk.END, text, tag)
        self.chat_history.see(tk.END)
        self.chat_history.config(state="disabled")
    
    def _update_context_labels(self):
        if not self.chat_session:
            self.max_context_label.config(text="Model's Max Context: Unknown")
            self.total_context_label.config(text="Context Total: 0 tokens")
            self.system_prompt_label.config(text="System Prompt: 0 tokens")
            self.context_label.config(text="Prompt Context: 0 tokens")
            self.memory_context_label.config(text="Memory Context: 0 tokens")
            self.tools_context_label.config(text="Tools Context: 0 tokens")
            return
        
        info = self.chat_session.get_context_info()
        self.max_context_label.config(text=f"Model's Max Context: {info['max_context']}")
        self.total_context_label.config(text=f"Context Total: {info['total_tokens']} tokens")
        self.system_prompt_label.config(text=f"System Prompt: {info['system_tokens']} tokens")
        self.context_label.config(text=f"Prompt Context: {info['prompt_tokens']} tokens")
        self.memory_context_label.config(text=f"Memory Context: {info['memory_tokens']} tokens")
        self.tools_context_label.config(text=f"Tools Context: {info['tools_tokens']} tokens, {info['tools_count']} tools")
    
    def _check_context(self):
        if not self.chat_session:
            return
        
        info = self.chat_session.get_context_info()
        msg = f"Max Context: {info['max_context']}\n"
        msg += f"Total Tokens: {info['total_tokens']}\n"
        msg += f"System: {info['system_tokens']}\n"
        msg += f"Prompts: {info['prompt_tokens']}\n"
        msg += f"Memory: {info['memory_tokens']}\n"
        msg += f"Tools: {info['tools_tokens']}"
        
        messagebox.showinfo("Context Information", msg)
    
    def _init_agents_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Agents")

        container = tk.Frame(frame, bg=BG)
        container.pack(fill=tk.BOTH, expand=True)

        left_sidebar = tk.Frame(container, bg=BG_LIGHT, width=150)
        left_sidebar.pack(side=tk.LEFT, fill=tk.Y)
        left_sidebar.pack_propagate(False)

        tk.Label(left_sidebar, text="Agents", font=FONT_BOLD, bg=BG_LIGHT, fg=FG).pack(anchor=tk.W, padx=10, pady=(10, 5))

        tk.Button(left_sidebar, text="+ New Agent", bg=BG_LIGHTER, fg=FG,
                 font=FONT_BOLD, relief=tk.FLAT, bd=0,
                 command=self._show_new_agent).pack(fill=tk.X, padx=5, pady=2)
        tk.Frame(left_sidebar, bg=FG, height=1).pack(fill=tk.X, padx=5, pady=5)
        self.agents_list_frame = tk.Frame(left_sidebar, bg=BG_LIGHT)
        self.agents_list_frame.pack(fill=tk.X, expand=False, anchor=tk.N)

        self.agents_content_frame = tk.Frame(container, bg=BG)
        self.agents_content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20, pady=20)

        self._show_new_agent()
        self._refresh_agents_list()

    def _init_tasks_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Tasks")

        container = tk.Frame(frame, bg=BG)
        container.pack(fill=tk.BOTH, expand=True)

        left_sidebar = tk.Frame(container, bg=BG_LIGHT, width=150)
        left_sidebar.pack(side=tk.LEFT, fill=tk.Y)
        left_sidebar.pack_propagate(False)

        tk.Label(left_sidebar, text="Tasks", font=FONT_BOLD, bg=BG_LIGHT, fg=FG).pack(anchor=tk.W, padx=10, pady=(10, 5))

        tk.Button(left_sidebar, text="+ New Task", bg=BG_LIGHTER, fg=FG,
                 font=FONT_BOLD, relief=tk.FLAT, bd=0,
                 command=self._show_new_task).pack(fill=tk.X, padx=5, pady=2)
        tk.Frame(left_sidebar, bg=FG, height=1).pack(fill=tk.X, padx=5, pady=5)
        self.tasks_list_frame = tk.Frame(left_sidebar, bg=BG_LIGHT)
        self.tasks_list_frame.pack(fill=tk.X, expand=False, anchor=tk.N)

        self.tasks_content_frame = tk.Frame(container, bg=BG)
        self.tasks_content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20, pady=20)

        self._show_new_task()
        self._refresh_tasks_list()

    def _show_new_task(self):
        for widget in self.tasks_content_frame.winfo_children():
            widget.destroy()
        
        self.task_ui = TaskUIBuilder(
            self.tasks_content_frame, self.task_manager,
            BG, BG_LIGHT, BG_LIGHTER, FG, FONT, FONT_BOLD, FONT_TITLE
        )
        
        self.task_ui.build_new_task_form(
            on_save=self._save_task,
            on_cancel=None
        )

    def _refresh_tasks_list(self):
        for widget in self.tasks_list_frame.winfo_children():
            widget.destroy()
        
        tasks = self.task_manager.get_task_names()
        
        if not tasks or tasks == ["No tasks available"]:
            tk.Label(self.tasks_list_frame, text="No tasks yet", 
                    font=FONT, bg=BG_LIGHT, fg=FG).pack(anchor=tk.N, pady=10)
            return
        
        for task_name in tasks:
            if task_name != "No tasks available":
                btn = tk.Button(self.tasks_list_frame, text=task_name, bg=BG_LIGHTER, fg=FG,
                               font=FONT, relief=tk.FLAT, bd=0,
                               command=lambda n=task_name: self._view_task(n))
                btn.pack(fill=tk.X, padx=5, pady=1, anchor=tk.N)

    def _save_task(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        success, msg = save_task(
            name=self.task_ui.get_var("name").get(),
            description=self.task_ui.get_var("description").get(),
            task_mode=self.task_ui.get_var("task_mode").get(),
            timer_type=self.task_ui.get_var("timer_type").get(),
            minutes=self.task_ui.get_var("minutes").get() if self.task_ui.get_var("minutes") else "",
            specific_time=self.task_ui.get_var("specific_time").get() if self.task_ui.get_var("specific_time") else "",
            task_enabled=self.task_ui.get_var("task_enabled").get() if self.task_ui.get_var("task_enabled") else True,
            script_dir=script_dir
        )
        if success:
            messagebox.showinfo("Success", msg)
            self._refresh_tasks_list()
            self._show_new_task()
        else:
            messagebox.showerror("Error", msg)

    def _view_task(self, task_name):
        for widget in self.tasks_content_frame.winfo_children():
            widget.destroy()
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        task_data = load_task(task_name, script_dir)
        
        self._current_task_name = task_name
        
        self.task_ui = TaskUIBuilder(
            self.tasks_content_frame, self.task_manager,
            BG, BG_LIGHT, BG_LIGHTER, FG, FONT, FONT_BOLD, FONT_TITLE
        )
        
        self.task_ui.build_edit_task_form(
            task_data,
            on_save=self._update_task,
            on_delete=lambda: self._delete_task(task_name),
            on_cancel=None
        )

    def _update_task(self):
        if not hasattr(self, '_current_task_name'):
            return
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        success, msg, new_name = update_task(
            old_name=self._current_task_name,
            name=self.task_ui.get_var("name").get(),
            description=self.task_ui.get_var("description").get(),
            task_mode=self.task_ui.get_var("task_mode").get(),
            timer_type=self.task_ui.get_var("timer_type").get(),
            minutes=self.task_ui.get_var("minutes").get() if self.task_ui.get_var("minutes") else "",
            specific_time=self.task_ui.get_var("specific_time").get() if self.task_ui.get_var("specific_time") else "",
            task_enabled=self.task_ui.get_var("task_enabled").get() if self.task_ui.get_var("task_enabled") else True,
            script_dir=script_dir
        )
        
        if success:
            messagebox.showinfo("Success", msg)
            self._current_task_name = new_name
            self._refresh_tasks_list()
        else:
            messagebox.showerror("Error", msg)

    def _delete_task(self, task_name):
        if not messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete the task '{task_name}'?"):
            return
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        success, msg = delete_task(task_name, script_dir)
        
        if success:
            messagebox.showinfo("Success", msg)
            self._refresh_tasks_list()
            self._show_new_task()
        else:
            messagebox.showerror("Error", msg)

    def _show_new_agent(self):
        for widget in self.agents_content_frame.winfo_children():
            widget.destroy()
        
        db_names = get_database_names()
        model_names = self._get_model_names()
        
        self.agent_ui = AgentUIBuilder(
            self.agents_content_frame, self.agent_manager, model_names, db_names,
            BG, BG_LIGHT, BG_LIGHTER, FG, FONT, FONT_BOLD, FONT_TITLE
        )
        
        self.agent_ui.build_new_agent_form(
            on_save=self._save_agent,
            on_add_db=self._add_db_to_new_agent,
            on_remove_db=self._remove_db_from_new_agent
        )

    def _add_db_to_new_agent(self):
        db_name = self.agent_ui.get_db_var().get()
        self.agent_manager.add_db_to_new_agent(db_name)
        self.agent_ui.update_db_list_label()
    
    def _remove_db_from_new_agent(self):
        db_name = self.agent_ui.get_db_var().get()
        self.agent_manager.remove_db_from_new_agent(db_name)
        self.agent_ui.update_db_list_label()

    def _save_agent(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        success, msg = save_agent(
            name=self.agent_ui.get_var("name").get(),
            model=self.agent_ui.get_var("model").get(),
            system_prompt=self.agent_ui.get_var("prompt").get(),
            connected_dbs=self.agent_manager.new_agent_connected_dbs,
            enabled_tools=self.agent_manager.new_agent_enabled_tools,
            script_dir=script_dir
        )
        if success:
            messagebox.showinfo("Success", msg)
            self._refresh_agents_list()
            self._refresh_chat_agents()
            self._show_new_agent()
        else:
            messagebox.showerror("Error", msg)
    
    def _view_agent(self, agent_name):
        for widget in self.agents_content_frame.winfo_children():
            widget.destroy()
        
        filename = agent_name.replace(' ', '_') + '.txt'
        script_dir = os.path.dirname(os.path.abspath(__file__))
        agent_data = load_agent(filename, script_dir)
        
        if not agent_data:
            messagebox.showerror("Error", "Failed to load agent.")
            return
        
        self._current_agent_file = filename
        db_names = get_database_names(script_dir)
        model_names = self._get_model_names()
        
        self.agent_ui = AgentUIBuilder(
            self.agents_content_frame, self.agent_manager, model_names, db_names,
            BG, BG_LIGHT, BG_LIGHTER, FG, FONT, FONT_BOLD, FONT_TITLE
        )
        
        self.agent_ui.build_edit_agent_form(
            agent_data, filename,
            on_save=self._update_agent,
            on_delete=self._delete_agent,
            on_add_db=self._add_db_to_edit_agent,
            on_remove_db=self._remove_db_from_edit_agent,
            on_delete_memory=self._delete_agent_memory
        )

    def _delete_agent_memory(self):
        if not hasattr(self, '_current_agent_file'):
            return
        agent_name = self._current_agent_file.replace('.txt', '').replace('_', ' ')
        
        if not messagebox.askyesno("Confirm Delete Memory", f"Are you sure you want to delete all memory for '{agent_name}'?\n\nThis cannot be undone."):
            return
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        from Agents import delete_agent_memory
        success, msg = delete_agent_memory(self._current_agent_file, script_dir)
        
        if success:
            messagebox.showinfo("Success", msg)
        else:
            messagebox.showerror("Error", msg)

    def _add_db_to_edit_agent(self):
        db_name = self.agent_ui.get_db_var().get()
        self.agent_manager.add_db_to_edit_agent(db_name)
        self.agent_ui.update_edit_db_list_label()
    
    def _remove_db_from_edit_agent(self):
        db_name = self.agent_ui.get_db_var().get()
        self.agent_manager.remove_db_from_edit_agent(db_name)
        self.agent_ui.update_edit_db_list_label()

    def _update_agent(self):
        if not hasattr(self, '_current_agent_file'):
            return
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        success, msg, new_filename = update_agent(
            old_filename=self._current_agent_file,
            name=self.agent_ui.get_var("name").get(),
            model=self.agent_ui.get_var("model").get(),
            system_prompt=self.agent_ui.get_var("prompt").get(),
            connected_dbs=self.agent_manager.edit_agent_connected_dbs,
            enabled_tools=self.agent_manager.edit_agent_enabled_tools,
            script_dir=script_dir
        )
        
        if success:
            messagebox.showinfo("Success", msg)
            self._current_agent_file = new_filename
            self._refresh_agents_list()
            self._refresh_chat_agents()
        else:
            messagebox.showerror("Error", msg)
    
    def _delete_agent(self, filename):
        if not messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this agent?\n\nThis will also delete all associated memory."):
            return
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        success, msg = delete_agent(filename, script_dir)
        
        if success:
            messagebox.showinfo("Success", msg)
            self._refresh_agents_list()
            self._refresh_chat_agents()
            self._show_new_agent()
        else:
            messagebox.showerror("Error", msg)

    def _init_databases_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Databases")

        container = tk.Frame(frame, bg=BG)
        container.pack(fill=tk.BOTH, expand=True)

        left_sidebar = tk.Frame(container, bg=BG_LIGHT, width=150)
        left_sidebar.pack(side=tk.LEFT, fill=tk.Y)
        left_sidebar.pack_propagate(False)

        tk.Label(left_sidebar, text="Databases", font=FONT_BOLD, bg=BG_LIGHT, fg=FG).pack(anchor=tk.W, padx=10, pady=(10, 5))

        tk.Button(left_sidebar, text="+ New Database", bg=BG_LIGHTER, fg=FG,
                  font=FONT_BOLD, relief=tk.FLAT, bd=0,
                  command=self._show_new_database_form).pack(fill=tk.X, padx=5, pady=2)
        tk.Frame(left_sidebar, bg=FG, height=1).pack(fill=tk.X, padx=5, pady=5)
        self.databases_list_frame = tk.Frame(left_sidebar, bg=BG_LIGHT)
        self.databases_list_frame.pack(fill=tk.X, expand=False, anchor=tk.N)

        content_container = tk.Frame(container, bg=BG)
        content_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20, pady=20)
        canvas = tk.Canvas(content_container, bg=BG, highlightthickness=0)
        scrollbar = tk.Scrollbar(content_container, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.databases_content_frame = tk.Frame(canvas, bg=BG)
        canvas_window = canvas.create_window((0, 0), window=self.databases_content_frame, anchor="nw")

        def on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)
        canvas.bind("<Configure>", on_canvas_configure)

        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        self.databases_content_frame.bind("<Configure>", on_frame_configure)

        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", on_mousewheel)

        self._refresh_databases_list()
        self._show_new_database_form()

    def _show_new_database_form(self):
        self.db_ui = DatabaseUIBuilder(
            self.databases_content_frame, self.db_manager,
            BG, BG_LIGHT, BG_LIGHTER, FG, FONT, FONT_BOLD, FONT_TITLE
        )
        self.db_ui.build_new_db_form(on_save=self._save_database)

    def _save_database(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        success, msg = save_database(
            name=self.db_ui.get_var("name").get(),
            file_path=self.db_ui.get_var("path").get(),
            script_dir=script_dir
        )
        if success:
            messagebox.showinfo("Success", msg)
            self._refresh_databases_list()
            self._show_new_database_form()
        else:
            messagebox.showerror("Error", msg)

    def _view_database(self, db_name):
        from Databases import get_database_info
        script_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = get_database_info(db_name, script_dir)
        self._current_db_name = db_name

        self.db_ui = DatabaseUIBuilder(
            self.databases_content_frame, self.db_manager,
            BG, BG_LIGHT, BG_LIGHTER, FG, FONT, FONT_BOLD, FONT_TITLE
        )
        self.db_ui.build_edit_db_form(
            db_name, file_path,
            on_save=self._update_database,
            on_delete=lambda: self._delete_database(db_name)
        )

    def _update_database(self):
        if not hasattr(self, '_current_db_name'):
            return

        script_dir = os.path.dirname(os.path.abspath(__file__))
        success, msg, new_name = update_database(
            old_name=self._current_db_name,
            new_name=self.db_ui.get_var("name").get(),
            new_path=self.db_ui.get_var("path").get(),
            script_dir=script_dir
        )

        if success:
            messagebox.showinfo("Success", msg)
            self._current_db_name = new_name
            self._refresh_databases_list()
        else:
            messagebox.showerror("Error", msg)

    def _delete_database(self, db_name):
        if not messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete the database '{db_name}'?"):
            return

        script_dir = os.path.dirname(os.path.abspath(__file__))
        success, msg = delete_database(db_name, script_dir)

        if success:
            messagebox.showinfo("Success", msg)
            self._show_new_database_form()
            self._refresh_databases_list()
        else:
            messagebox.showerror("Error", msg)

    def _refresh_databases_list(self):
        for widget in self.databases_list_frame.winfo_children():
            widget.destroy()

        databases = self.db_manager.get_database_names()

        if not databases or databases == ["No databases available"]:
            tk.Label(self.databases_list_frame, text="No databases yet",
                    font=FONT, bg=BG_LIGHT, fg=FG).pack(anchor=tk.N, pady=10)
            return

        for db_name in databases:
            if db_name != "No databases available":
                btn = tk.Button(self.databases_list_frame, text=db_name, bg=BG_LIGHTER, fg=FG,
                               font=FONT, relief=tk.FLAT, bd=0,
                               command=lambda n=db_name: self._view_database(n))
                btn.pack(fill=tk.X, padx=5, pady=1, anchor=tk.N)

    def _init_manage_models_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Manage Models")
        sub_notebook = ttk.Notebook(frame)
        sub_notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        installed_frame = ttk.Frame(sub_notebook)
        sub_notebook.add(installed_frame, text="Installed Models")

        container = tk.Frame(installed_frame, bg=BG)
        container.pack(fill=tk.BOTH, expand=True)

        left = tk.Frame(container, bg=BG)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        tk.Label(left, text="Installed Models:", font=FONT_BOLD, bg=BG, fg=FG).pack(anchor=tk.NW)

        self.model_buttons_frame = tk.Frame(left, bg=BG)
        self.model_buttons_frame.pack(fill=tk.Y, expand=True, anchor=tk.NW)

        tk.Button(left, text="Refresh", bg=BG_LIGHTER, fg=FG,
                  font=FONT_BOLD, relief=tk.RAISED, bd=2,
                  command=self._refresh_model_buttons).pack(anchor=tk.NW, pady=(10, 0))

        self._selected_model = None
        self._selected_model_folder = None

        right = tk.Frame(container, bg="#232323")
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20, pady=10)

        self.model_info_label = tk.Label(right, text="Select a model to view details.",
                                         font=FONT, bg="#232323", fg=FG,
                                         justify=tk.LEFT, wraplength=500)
        self.model_info_label.pack(anchor=tk.NW, pady=(0, 20))

        self.delete_model_btn = tk.Button(right, text="Delete From System",
                                          bg="#aa3333", fg=FG, font=FONT_BOLD,
                                          relief=tk.RAISED, bd=2, state="disabled",
                                          command=self._delete_selected_model)
        self.delete_model_btn.pack(anchor=tk.NW, pady=(0, 10))

        self._refresh_model_buttons()
        download_frame = ttk.Frame(sub_notebook)
        sub_notebook.add(download_frame, text="Download Models")

        dl_container = tk.Frame(download_frame, bg=BG)
        dl_container.pack(fill=tk.BOTH, expand=True)

        tk.Button(dl_container, text="Open Ollama's Model Library", bg=BG_LIGHTER, fg=FG,
                  font=("Arial", 12, "bold"), relief=tk.RAISED, bd=2,
                  command=lambda: webbrowser.open("https://ollama.com/library")
                  ).place(relx=0.5, rely=0.2, anchor="center")

        input_frame = tk.Frame(dl_container, bg=BG)
        input_frame.place(relx=0.5, rely=0.32, anchor="center")

        self.download_input_var = tk.StringVar()
        tk.Entry(input_frame, textvariable=self.download_input_var, width=40,
                 font=FONT, bg=BG_LIGHT, fg=FG).pack(side=tk.LEFT, padx=(0, 10))

        tk.Button(input_frame, text="Install", bg=BG_LIGHTER, fg=FG,
                  font=FONT_BOLD, relief=tk.RAISED, bd=2,
                  command=self._install_model).pack(side=tk.LEFT)

        self.download_status = tk.Label(dl_container, text="", font=FONT, bg=BG, fg="#ffff00")
        self.download_status.place(relx=0.5, rely=0.4, anchor="n")

    def _refresh_model_buttons(self):
        for widget in self.model_buttons_frame.winfo_children():
            widget.destroy()

        models = self._get_models(force=True)
        if not models:
            tk.Label(self.model_buttons_frame, text="No models found.",
                     bg=BG, fg=FG, font=FONT).pack(anchor=tk.NW)
            return

        for model in models:
            tk.Button(self.model_buttons_frame, text=model["name"], width=25,
                      anchor="w", bg=BG_LIGHT, fg=FG, font=FONT,
                      relief=tk.RAISED, bd=1,
                      command=lambda m=model: self._display_model_info(m)).pack(fill=tk.X, pady=2)

    def _get_models(self, force=False):
        if force or self._models_cache is None:
            models, _ = get_installed_models()
            self._models_cache = models or []
        return self._models_cache

    def _display_model_info(self, model):
        self._selected_model = model["name"]
        self._selected_model_folder = get_model_folder(model["name"])

        info = f"Model Name: {model['name']}\nSize: {model['size']}\nLast Modified: {model.get('modified', 'Unknown')}\n"

        self.model_info_label.config(text=info)
        self.delete_model_btn.config(state="normal")

    def _delete_selected_model(self):
        if not self._selected_model:
            return
        if not messagebox.askyesno("Delete Model", f"Delete '{self._selected_model}' from your system?"):
            return
        success, error = uninstall_model(self._selected_model)
        if success:
            messagebox.showinfo("Deleted", f"'{self._selected_model}' has been deleted.")
            self._selected_model = None
            self._selected_model_folder = None
            self.model_info_label.config(text="Select a model to view details.")
            self.delete_model_btn.config(state="disabled")
            self._refresh_model_buttons()
        else:
            messagebox.showerror("Error", f"Failed to delete model: {error}")

    def _install_model(self):
        model = self.download_input_var.get().strip()
        if not model:
            self.download_status.config(text="Please enter a model name.", fg="red")
            return

        self.download_status.config(text=f"Downloading {model}...", fg="#ffff00")

        def on_done(name):
            self.root.after(0, lambda: self.download_status.config(
                text=f"'{name}' installed successfully.", fg="#00ff00"))

        def on_error(e):
            self.root.after(0, lambda: self.download_status.config(
                text=f"Error: {e}", fg="red"))

        download_model(model, on_done, on_error)

    def _init_remote_chats_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Remote Chats")

        container = tk.Frame(frame, bg=BG)
        container.pack(fill=tk.BOTH, expand=True)

        left_sidebar = tk.Frame(container, bg=BG_LIGHT, width=150)
        left_sidebar.pack(side=tk.LEFT, fill=tk.Y)
        left_sidebar.pack_propagate(False)

        tk.Label(left_sidebar, text="Remote Systems", font=FONT_BOLD, bg=BG_LIGHT, fg=FG).pack(anchor=tk.W, padx=10, pady=(10, 5))

        telegram_btn = tk.Button(left_sidebar, text="Telegram", bg=BG_LIGHTER, fg=FG,
                                 font=FONT_BOLD, relief=tk.FLAT, bd=0,
                                 command=self._show_telegram_section)
        telegram_btn.pack(fill=tk.X, padx=5, pady=2)

        discord_btn = tk.Button(left_sidebar, text="Discord", bg=BG_LIGHTER, fg=FG,
                                font=FONT_BOLD, relief=tk.FLAT, bd=0,
                                command=self._show_discord_section)
        discord_btn.pack(fill=tk.X, padx=5, pady=2)

        self.remote_content_frame = tk.Frame(container, bg=BG)
        self.remote_content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20, pady=20)

        self._show_telegram_section()

    def _show_telegram_section(self):
        for widget in self.remote_content_frame.winfo_children():
            widget.destroy()

        if not TelegramUIBuilder:
            tk.Label(self.remote_content_frame, text="Telegram UI not available", 
                    font=FONT, bg=BG, fg=FG).pack(anchor=tk.W, pady=(0, 10))
            return

        colors = {"bg": BG, "bg_light": BG_LIGHT, "bg_lighter": BG_LIGHTER, "fg": FG}
        fonts = {"font": FONT, "font_bold": FONT_BOLD, "font_title": FONT_TITLE}

        self.telegram_ui = TelegramUIBuilder(
            self.remote_content_frame, colors, fonts, telegram_bot_manager
        )
        self.telegram_ui.build_section(
            on_toggle=self._toggle_telegram_bot,
            on_save_token=self._save_telegram_token,
            append_chat_callback=self._append_chat,
            agent_var_getter=lambda: self.agent_var.get() if hasattr(self, 'agent_var') else None
        )

        script_dir = os.path.dirname(os.path.abspath(__file__))
        token = load_telegram_token(script_dir)
        if token:
            self.telegram_ui.get_var("token").set(token)

    def _show_discord_section(self):
        for widget in self.remote_content_frame.winfo_children():
            widget.destroy()

        if not DiscordUIBuilder:
            tk.Label(self.remote_content_frame, text="Discord UI not available", 
                    font=FONT, bg=BG, fg=FG).pack(anchor=tk.W, pady=(0, 10))
            return

        colors = {"bg": BG, "bg_light": BG_LIGHT, "bg_lighter": BG_LIGHTER, "fg": FG}
        fonts = {"font": FONT, "font_bold": FONT_BOLD, "font_title": FONT_TITLE}

        self.discord_ui = DiscordUIBuilder(
            self.remote_content_frame, colors, fonts, discord_bot_manager
        )
        self.discord_ui.build_section(
            on_toggle=self._toggle_discord_bot,
            on_save_token=self._save_discord_token,
            on_save_channel=self._save_discord_channel
        )

        script_dir = os.path.dirname(os.path.abspath(__file__))
        token = load_discord_token(script_dir)
        if token:
            self.discord_ui.get_var("token").set(token)
        channel = load_discord_channel(script_dir)
        if channel:
            self.discord_ui.get_var("channel").set(channel)

    def _toggle_discord_bot(self):
        if not DISCORD_AVAILABLE:
            messagebox.showerror("Discord Not Available", "discord.py library is not installed.\nInstall it with: pip install discord.py")
            return

        token = self.discord_ui.get_var("token").get().strip()
        if not token:
            messagebox.showwarning("No Token", "Please enter a Discord bot token first.")
            return

        current = self.discord_ui.get_widget("status_label").cget("text")
        if current == "Status: Off":
            agent_name = self.agent_var.get()
            if not agent_name or agent_name == "No agents":
                messagebox.showwarning("No Agent", "Please select an agent in the Chat tab first.")
                return
            script_dir = os.path.dirname(os.path.abspath(__file__))
            from Chat import load_agent_config
            config = load_agent_config(agent_name, script_dir)
            model = config.get("model", "")

            if not model:
                messagebox.showwarning("No Model", "Selected agent has no model configured.")
                return

            discord_bot_manager.set_model(model)

            def discord_callback(direction, message):
                if direction == "discord_in":
                    self._append_chat(f"{message}\n\n", "user")
                else:
                    self._append_chat(f"{message}\n\n", "model")

            success, msg = discord_bot_manager.start(token, callback=discord_callback)
            if success:
                self.discord_ui.get_widget("status_label").config(text="Status: On (Paused)", fg="orange")
                self.discord_ui.get_widget("toggle_btn").config(text="Turn Off")
                def status_callback(is_paused, status_text, color):
                    try:
                        self.discord_ui.get_widget("status_label").config(text=status_text, fg=color)
                    except tk.TclError:
                        pass
                discord_bot_manager.set_status_callback(status_callback)
            else:
                messagebox.showerror("Error", msg)
        else:
            success, msg = discord_bot_manager.stop()
            if success:
                self.discord_ui.get_widget("status_label").config(text="Status: Off", fg="red")
                self.discord_ui.get_widget("toggle_btn").config(text="Turn On")
            else:
                messagebox.showerror("Error", msg)

    def _save_discord_channel(self):
        channel_id = self.discord_ui.get_var("channel").get()
        script_dir = os.path.dirname(os.path.abspath(__file__))
        success, msg = save_discord_channel(channel_id, script_dir)
        if success:
            messagebox.showinfo("Saved", msg)
        else:
            messagebox.showerror("Error", msg)

    def _send_to_discord(self, message):
        if not DISCORD_AVAILABLE:
            return
        if not discord_bot_manager or not discord_bot_manager.is_running():
            return
        channel_id = self.discord_ui.get_var("channel").get().strip()
        if not channel_id:
            return

        try:
            import threading
            def send():
                try:
                    discord_bot_manager.send_message_to_channel(channel_id, message)
                except:
                    pass
            threading.Thread(target=send, daemon=True).start()
        except:
            pass

    def _save_discord_token(self):
        token = self.discord_ui.get_var("token").get()
        script_dir = os.path.dirname(os.path.abspath(__file__))
        success, msg = save_discord_token(token, script_dir)
        if success:
            messagebox.showinfo("Saved", msg)
        else:
            messagebox.showerror("Error", msg)

    def _toggle_telegram_bot(self):
        if not TELEGRAM_AVAILABLE:
            messagebox.showerror("Telegram Not Available", "python-telegram-bot library is not installed.\nInstall it with: pip install python-telegram-bot")
            return

        token = self.telegram_ui.get_var("token").get().strip()
        if not token:
            messagebox.showwarning("No Token", "Please enter a Telegram bot token first.")
            return

        current = self.telegram_ui.get_widget("status_label").cget("text")
        if current == "Status: Off":
            agent_name = self.agent_var.get()
            if not agent_name or agent_name == "No agents":
                messagebox.showwarning("No Agent", "Please select an agent in the Chat tab first.")
                return
            script_dir = os.path.dirname(os.path.abspath(__file__))
            from Chat import load_agent_config
            config = load_agent_config(agent_name, script_dir)
            model = config.get("model", "")

            if not model:
                messagebox.showwarning("No Model", "Selected agent has no model configured.")
                return

            telegram_bot_manager.set_model(model)

            def telegram_callback(direction, message):
                if direction == "telegram_in":
                    self._append_chat(f"{message}\n\n", "user")
                else:
                    self._append_chat(f"{message}\n\n", "model")

            success, msg = telegram_bot_manager.start(token, callback=telegram_callback)
            if success:
                self.telegram_ui.get_widget("status_label").config(text="Status: On (Paused)", fg="orange")
                self.telegram_ui.get_widget("toggle_btn").config(text="Turn Off")
                def status_callback(is_paused, status_text, color):
                    try:
                        self.telegram_ui.get_widget("status_label").config(text=status_text, fg=color)
                    except tk.TclError:
                        pass
                telegram_bot_manager.set_status_callback(status_callback)
            else:
                messagebox.showerror("Error", msg)
        else:
            success, msg = telegram_bot_manager.stop()
            if success:
                self.telegram_ui.get_widget("status_label").config(text="Status: Off", fg="red")
                self.telegram_ui.get_widget("toggle_btn").config(text="Turn On")
            else:
                messagebox.showerror("Error", msg)

    def _save_telegram_token(self):
        token = self.telegram_ui.get_var("token").get()
        script_dir = os.path.dirname(os.path.abspath(__file__))
        success, msg = save_telegram_token(token, script_dir)
        if success:
            messagebox.showinfo("Saved", msg)
        else:
            messagebox.showerror("Error", msg)

    def _init_settings_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Settings")

        container = tk.Frame(frame, bg=BG)
        container.pack(fill=tk.BOTH, expand=True)

        left_sidebar = tk.Frame(container, bg=BG_LIGHT, width=150)
        left_sidebar.pack(side=tk.LEFT, fill=tk.Y)
        left_sidebar.pack_propagate(False)

        tk.Label(left_sidebar, text="Settings", font=FONT_BOLD, bg=BG_LIGHT, fg=FG).pack(anchor=tk.W, padx=10, pady=(10, 5))

        reddit_btn = tk.Button(left_sidebar, text="Reddit API", bg=BG_LIGHTER, fg=FG,
                               font=FONT_BOLD, relief=tk.FLAT, bd=0,
                               command=self._show_reddit_settings)
        reddit_btn.pack(fill=tk.X, padx=5, pady=2)

        tavily_btn = tk.Button(left_sidebar, text="Tavily API", bg=BG_LIGHTER, fg=FG,
                               font=FONT_BOLD, relief=tk.FLAT, bd=0,
                               command=self._show_tavily_settings)
        tavily_btn.pack(fill=tk.X, padx=5, pady=2)

        self.settings_content_frame = tk.Frame(container, bg=BG)
        self.settings_content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20, pady=20)

        self._show_reddit_settings()

    def _show_reddit_settings(self):
        for widget in self.settings_content_frame.winfo_children():
            widget.destroy()

        colors = {"bg": BG, "bg_light": BG_LIGHT, "bg_lighter": BG_LIGHTER, "fg": FG}
        fonts = {"font": FONT, "font_bold": FONT_BOLD, "font_title": FONT_TITLE}

        self.settings_ui = SettingsUIBuilder(
            self.settings_content_frame, self.settings_manager, colors, fonts
        )
        self.settings_ui.build_settings_tab(
            on_save_callback=self._save_settings,
            on_open_reddit_callback=self._open_reddit_apps,
            section_type="reddit"
        )
        self.settings_ui.load_values(section_type="reddit")

    def _show_tavily_settings(self):
        for widget in self.settings_content_frame.winfo_children():
            widget.destroy()

        colors = {"bg": BG, "bg_light": BG_LIGHT, "bg_lighter": BG_LIGHTER, "fg": FG}
        fonts = {"font": FONT, "font_bold": FONT_BOLD, "font_title": FONT_TITLE}

        self.settings_ui = SettingsUIBuilder(
            self.settings_content_frame, self.settings_manager, colors, fonts
        )
        self.settings_ui.build_settings_tab(
            on_save_callback=self._save_tavily_settings,
            on_open_tavily_callback=self._open_tavily_site,
            section_type="tavily"
        )
        self.settings_ui.load_values(section_type="tavily")

    def _save_tavily_settings(self):
        api_key = self.settings_ui.get_var("tavily_api_key").get()
        success, msg = self.settings_manager.save_tavily_credentials(api_key)
        if success:
            messagebox.showinfo("Saved", msg)
        else:
            messagebox.showerror("Error", msg)

    def _open_reddit_apps(self):
        webbrowser.open("https://www.reddit.com/prefs/apps")

    def _open_tavily_site(self):
        webbrowser.open("https://www.tavily.com")

    def _save_settings(self):
        client_id = self.settings_ui.get_var("reddit_client_id").get()
        client_secret = self.settings_ui.get_var("reddit_client_secret").get()
        success, msg = self.settings_manager.save_reddit_credentials(client_id, client_secret)
        if success:
            messagebox.showinfo("Saved", msg)
        else:
            messagebox.showerror("Error", msg)


def main():
    root = tk.Tk()
    app = DinoFlow(root)
    root.mainloop()


if __name__ == "__main__":
    main()
