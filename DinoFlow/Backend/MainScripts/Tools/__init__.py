import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from . import system
from . import General
from . import Browser
from . import Files
from . import Inputs

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_system_info",
            "description": "Get CPU, RAM, and disk usage information",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Get the current date and time in formatted string",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_processes",
            "description": "List running processes with PID, name, CPU, and memory usage",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Maximum number of processes to return (default 20)"}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "kill_process",
            "description": "Kill a process by PID (integer) or process name (string). Works on Linux and Windows. Use force=True to force kill.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pid_or_name": {"type": ["integer", "string"], "description": "Process ID (number) or process name (string) to kill"},
                    "force": {"type": "boolean", "description": "If true, force kill the process (SIGKILL on Linux, /F on Windows)"}
                },
                "required": ["pid_or_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "start_process",
            "description": "Start a new process with the given command. Use wait=True to run synchronously and get output, or wait=False to start asynchronously and get the PID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Command to execute"},
                    "shell": {"type": "boolean", "description": "Run through shell (default true)"},
                    "wait": {"type": "boolean", "description": "Wait for completion and return output (default false)"},
                    "timeout": {"type": "integer", "description": "Timeout in seconds when wait=True (default 30)"}
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_shell_command",
            "description": "Execute a shell command with safety blocks for dangerous operations (rm -rf /, dd, mkfs, etc.)",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Shell command to execute"},
                    "timeout": {"type": "integer", "description": "Timeout in seconds (default 30)"}
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_python_code",
            "description": "Execute Python code in a sandboxed environment without file/network access (safe for untrusted code)",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Python code to execute"},
                    "timeout": {"type": "integer", "description": "Timeout in seconds (default 10)"}
                },
                "required": ["code"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "take_screenshot",
            "description": "Take a screenshot of the full screen and save it to a file",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to save screenshot (optional, uses default if not provided)"}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "save_to_memory",
            "description": "Save important information to the agent's episodic memory for future recall. Use this when you learn something valuable that should persist across conversations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "The information to save (summary text)"},
                    "importance": {"type": "number", "description": "Importance from 0.5-2.0, higher = more likely to be retrieved (default 1.0)"},
                    "category": {"type": "string", "description": "Category: general, fact, preference, or lesson (default general)"}
                },
                "required": ["content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "toggle_task",
            "description": "Enable or disable an existing task. Use this to toggle a task's enabled status. Tasks that are disabled will not fire during chat sessions, even when Tasks Enabled mode is active.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_name": {"type": "string", "description": "The name of the task to toggle"},
                    "enabled": {"type": "boolean", "description": "True to enable, False to disable the task"}
                },
                "required": ["task_name", "enabled"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_task",
            "description": "Create a new automated task that fires during chat sessions when Tasks Enabled mode is active. Use this when the user asks to create a scheduled task. You must extract: task name, the prompt to execute, when it should fire (minutes after start or specific time), and whether it repeats. Example: User says 'create a task named CheckEmail that checks my email every 30 minutes' -> name='CheckEmail', task_prompt='Check the email', task_mode='Repeat', timer_type='Minutes', minutes='30'",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "The task name (e.g., 'CheckEmail', 'DailyReport', 'BrowserOpen')"},
                    "task_prompt": {"type": "string", "description": "The exact text/prompt to send to the model when the task fires"},
                    "task_mode": {"type": "string", "description": "'Once' for single execution, 'Repeat' for recurring (default: Once)"},
                    "timer_type": {"type": "string", "description": "'Minutes' to fire X minutes after chat starts, 'Specific Time' to fire at HH:MM (default: Minutes)"},
                    "minutes": {"type": "string", "description": "Required if timer_type is 'Minutes'. Number of minutes after chat start to fire (e.g., '5', '30', '120')"},
                    "specific_time": {"type": "string", "description": "Required if timer_type is 'Specific Time'. Time in HH:MM format (e.g., '14:00', '09:30')"}
                },
                "required": ["name", "task_prompt"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "launch_browser",
            "description": "Launch a new Selenium browser session",
            "parameters": {
                "type": "object",
                "properties": {
                    "headless": {"type": "boolean", "description": "Run browser in headless mode (default: False)"}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "navigate_to",
            "description": "Navigate the browser to a URL",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "The URL to navigate to"},
                    "wait_seconds": {"type": "number", "description": "Time to wait for page load (default 2.0)"}
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_page_text",
            "description": "Get the visible text content of the current browser page",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "click_element",
            "description": "Click an element on the current browser page",
            "parameters": {
                "type": "object",
                "properties": {
                    "selector": {"type": "string", "description": "CSS selector or XPath to find the element"},
                    "by": {"type": "string", "description": "Method to find element - 'css' (default) or 'xpath'"},
                    "wait_seconds": {"type": "number", "description": "Time to wait after click"}
                },
                "required": ["selector"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "find_elements",
            "description": "Find elements on the current browser page and return their descriptions",
            "parameters": {
                "type": "object",
                "properties": {
                    "selector": {"type": "string", "description": "CSS selector or XPath"},
                    "by": {"type": "string", "description": "Method to find elements - 'css' (default) or 'xpath'"}
                },
                "required": ["selector"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "browser_screenshot",
            "description": "Take a screenshot of the current browser view and return as base64",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "scroll_page",
            "description": "Scroll the current browser page up or down",
            "parameters": {
                "type": "object",
                "properties": {
                    "direction": {"type": "string", "description": '"down" or "up" (default: "down")'},
                    "amount": {"type": "integer", "description": "Pixels to scroll (default 500)"}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "close_browser",
            "description": "Close the browser session",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a file at the given path",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file"},
                    "max_size": {"type": "integer", "description": "Maximum file size to read in bytes (default 10MB)"}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write content to a file, overwriting it if it exists",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file"},
                    "content": {"type": "string", "description": "Content to write"}
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_file",
            "description": "Delete a file at the given path",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file"}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "List the contents of a directory",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the directory"}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_files",
            "description": "Search for files by name or content within a directory",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {"type": "string", "description": "Directory to search in"},
                    "filename": {"type": "string", "description": "Filename pattern to search for (optional)"},
                    "content": {"type": "string", "description": "Content pattern to search for (optional)"}
                },
                "required": ["directory"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_folder",
            "description": "Create a new folder at the given path",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path for the new folder"}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "move_file",
            "description": "Move a file or folder from source to destination",
            "parameters": {
                "type": "object",
                "properties": {
                    "source": {"type": "string", "description": "Path to file or folder to move"},
                    "destination": {"type": "string", "description": "Destination path"}
                },
                "required": ["source", "destination"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "copy_file",
            "description": "Copy a file or folder from source to destination",
            "parameters": {
                "type": "object",
                "properties": {
                    "source": {"type": "string", "description": "Path to file or folder to copy"},
                    "destination": {"type": "string", "description": "Destination path"},
                    "preserve_attrs": {"type": "boolean", "description": "Preserve permissions, timestamps (default True)"}
                },
                "required": ["source", "destination"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "type_text",
            "description": "Type text into the currently focused application or input field",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "The text string to type"},
                    "interval": {"type": "number", "description": "Delay between keystrokes in seconds (default 0.01)"}
                },
                "required": ["text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "press_key",
            "description": "Send keyboard shortcut to the focused application (e.g., 'ctrl+t', 'alt+f4', 'ctrl+shift+tab')",
            "parameters": {
                "type": "object",
                "properties": {
                    "key_combination": {"type": "string", "description": "Key combination to press, separated by '+' (e.g., 'ctrl+t')"}
                },
                "required": ["key_combination"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_mouse_position",
            "description": "Get the current mouse cursor screen coordinates",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "move_mouse",
            "description": "Move the mouse cursor to specified screen coordinates",
            "parameters": {
                "type": "object",
                "properties": {
                    "x": {"type": "integer", "description": "X coordinate on screen"},
                    "y": {"type": "integer", "description": "Y coordinate on screen"}
                },
                "required": ["x", "y"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "click_mouse",
            "description": "Click a mouse button at the current cursor position",
            "parameters": {
                "type": "object",
                "properties": {
                    "button": {"type": "string", "description": "Mouse button to click: 'left', 'right', or 'middle' (default: 'left')"}
                },
                "required": []
            }
        }
    }
]


def execute_tool(name, args):
    if name == "get_system_info":
        return system.get_system_info()

    if name == "get_current_time":
        return system.get_current_time()

    if name == "list_processes":
        return system.list_processes(args.get("limit", 20))

    if name == "kill_process":
        return system.kill_process(args.get("pid_or_name"), args.get("force", False))

    if name == "start_process":
        return system.start_process(args.get("command"), args.get("shell", True), args.get("wait", False), args.get("timeout", 30))

    if name == "run_shell_command":
        return system.run_shell_command(args.get("command", ""), args.get("timeout", 30))

    if name == "run_python_code":
        return system.run_python_code(args.get("code", ""), args.get("timeout", 10))

    if name == "take_screenshot":
        return General.take_screenshot(args.get("path", ""))

    if name == "save_to_memory":
        return General.save_to_memory(
            args.get("content", ""),
            args.get("importance", 1.0),
            args.get("category", "general"),
            ""
        )

    if name == "toggle_task":
        return General.toggle_task(
            args.get("task_name", ""),
            args.get("enabled", True)
        )

    if name == "create_task":
        return General.create_task(
            args.get("name", ""),
            args.get("task_prompt", ""),
            args.get("task_mode", "Once"),
            args.get("timer_type", "Minutes"),
            args.get("minutes", ""),
            args.get("specific_time", "")
        )

    if name == "launch_browser":
        return Browser.launch_browser(args.get("headless", False))

    if name == "navigate_to":
        return Browser.navigate_to(args.get("url"), args.get("wait_seconds", 2.0))

    if name == "get_page_text":
        return Browser.get_page_text()

    if name == "click_element":
        return Browser.click_element(args.get("selector"), args.get("by", "css"), args.get("wait_seconds", 1.0))

    if name == "find_elements":
        return Browser.find_elements(args.get("selector"), args.get("by", "css"))

    if name == "scroll_page":
        return Browser.scroll_page(args.get("direction", "down"), args.get("amount", 500))

    if name == "close_browser":
        return Browser.close_browser()

    if name == "read_file":
        return Files.read_file(args.get("path"), args.get("max_size", 10*1024*1024))

    if name == "write_file":
        return Files.write_file(args.get("path"), args.get("content"))

    if name == "delete_file":
        return Files.delete_file(args.get("path"))

    if name == "list_directory":
        return Files.list_directory(args.get("path"))

    if name == "search_files":
        return Files.search_files(args.get("directory"), args.get("filename", ""), args.get("content", ""))

    if name == "create_folder":
        return Files.create_folder(args.get("path"))

    if name == "move_file":
        return Files.move_file(args.get("source"), args.get("destination"))

    if name == "copy_file":
        return Files.copy_file(args.get("source"), args.get("destination"), args.get("preserve_attrs", True))

    if name == "type_text":
        return Inputs.type_text(args.get("text", ""), args.get("interval", 0.01))

    if name == "press_key":
        return Inputs.press_key(args.get("key_combination", ""))

    if name == "get_mouse_position":
        return Inputs.get_mouse_position()

    if name == "move_mouse":
        return Inputs.move_mouse(args.get("x", 0), args.get("y", 0))

    if name == "click_mouse":
        return Inputs.click_mouse(args.get("button", "left"))

    if name == "scroll_mouse":
        return Inputs.scroll_mouse(args.get("direction", "down"), args.get("amount", 3))

    return f"Error: Unknown tool '{name}'"
