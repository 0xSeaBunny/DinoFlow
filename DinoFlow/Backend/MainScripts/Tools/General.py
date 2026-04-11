import os
import sys
import subprocess
import threading

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "Extra"))
from Memory import get_episodic_memory


def take_screenshot(path=""):
    if not path:
        path = "/tmp/screenshot.png" if sys.platform != "win32" else os.path.join(os.environ.get("TEMP", "C:\temp"), "screenshot.png")
    try:
        if sys.platform == "win32":
            try:
                from PIL import ImageGrab
                screenshot = ImageGrab.grab()
                screenshot.save(path, optimize=True, compress_level=6)
                return f"Screenshot saved to: {path}. A full screen capture has been saved and is ready for review."
            except ImportError:
                return "Error: PIL/Pillow not installed. Install with: pip install Pillow"
        else:
            result = subprocess.run(["gnome-screenshot", "-f", path], capture_output=True, timeout=5)
            if result.returncode == 0:
                _optimize_png(path)
                return f"GNOME Screenshot captured and saved to: {path}. Full screen image has been captured using gnome-screenshot and is ready for review."
            result = subprocess.run(["scrot", path], capture_output=True, timeout=10)
            if result.returncode == 0:
                _optimize_png(path)
                return f"Screenshot saved to: {path}. Full screen capture has been saved using scrot and is ready for review."
            result = subprocess.run(["import", "-window", "root", path], capture_output=True, timeout=10)
            if result.returncode == 0:
                _optimize_png(path)
                return f"Screenshot saved to: {path}. Full screen capture has been saved using ImageMagick and is ready for review."
            return "Error: No screenshot tool available. Install gnome-screenshot, scrot, or ImageMagick."
    except Exception as e:
        return f"Error taking screenshot: {e}"


def save_to_memory(content: str, importance: float = 1.0, category: str = "general", agent_name: str = ""):
    try:
        effective_agent = agent_name if agent_name else get_current_agent()
        episodic = get_episodic_memory(effective_agent)
        
        memory_id = episodic.add_memory(
            summary=content,
            context={"category": category, "saved_by": "agent"},
            importance=min(max(importance, 0.5), 2.0)  # Clamp between 0.5 and 2.0
        )
        
        return f"Memory saved successfully (ID: {memory_id}). Content: {content[:100]}..."
    except Exception as e:
        return f"Error saving memory: {e}"


def _optimize_png(path, max_dimension=1920, quality=85):

    try:
        try:
            from PIL import Image
            with Image.open(path) as img:
                width, height = img.size
                if width > max_dimension or height > max_dimension:
                    ratio = min(max_dimension / width, max_dimension / height)
                    new_size = (int(width * ratio), int(height * ratio))
                    img = img.resize(new_size, Image.Resampling.LANCZOS)
                img.save(path, optimize=True, compress_level=6)
                return True
        except ImportError:
            pass
        
        if sys.platform != "win32":
            result = subprocess.run(
                ["convert", path, "-resize", f"{max_dimension}x{max_dimension}>", "-define", "png:compression-level=6", path],
                capture_output=True,
                timeout=10
            )
            if result.returncode == 0:
                return True
    except Exception:
        pass
    return False


def toggle_task(task_name: str, enabled: bool = True, script_dir: str = ""):
    try:
        if not script_dir:
            script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        tasks_dir = os.path.join(script_dir, "Backend", "SavedInfo", "Tasks")
        filename = task_name.replace(' ', '_') + ".txt"
        filepath = os.path.join(tasks_dir, filename)
        
        if not os.path.exists(filepath):
            return f"Error: Task '{task_name}' not found."
        
        task_data = {}
        lines = []
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
            for line in lines:
                line = line.strip()
                if line.startswith("Task Enabled: "):
                    task_data["task_enabled"] = line[14:].lower() == "true"
        
        new_lines = []
        found = False
        for line in lines:
            if line.strip().startswith("Task Enabled: "):
                new_lines.append(f"Task Enabled: {enabled}\n")
                found = True
            else:
                new_lines.append(line)
        
        if not found:
            new_lines.append(f"Task Enabled: {enabled}\n")
        

        with open(filepath, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        
        status = "enabled" if enabled else "disabled"
        return f"Task '{task_name}' is now {status}."
    except Exception as e:
        return f"Error toggling task: {e}"


def create_task(name: str, task_prompt: str, task_mode: str = "Once", timer_type: str = "Minutes", 
                minutes: str = "", specific_time: str = "", script_dir: str = ""):

    try:
        if not script_dir:
            script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        if not name:
            return "Error: Task name is required."
        
        tasks_dir = os.path.join(script_dir, "Backend", "SavedInfo", "Tasks")
        os.makedirs(tasks_dir, exist_ok=True)
        
        filename = name.replace(' ', '_') + ".txt"
        filepath = os.path.join(tasks_dir, filename)
        

        if os.path.exists(filepath):
            return f"Error: Task '{name}' already exists. Use toggle_task to enable/disable it."
        

        if task_mode not in ["Once", "Repeat"]:
            return "Error: task_mode must be 'Once' or 'Repeat'."
        
        if timer_type not in ["Minutes", "Specific Time"]:
            return "Error: timer_type must be 'Minutes' or 'Specific Time'."
        
        if timer_type == "Minutes":
            if not minutes or not minutes.isdigit():
                return "Error: minutes must be a positive number when timer_type is 'Minutes'."
        
        if timer_type == "Specific Time":
            if not specific_time:
                return "Error: specific_time is required when timer_type is 'Specific Time' (format: HH:MM)."
        

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"Name: {name}\n")
            f.write(f"Task Prompt: {task_prompt}\n")
            f.write(f"Task Mode: {task_mode}\n")
            f.write(f"Timer Type: {timer_type}\n")
            if timer_type == "Minutes":
                f.write(f"Minutes: {minutes}\n")
            else:
                f.write(f"Specific Time: {specific_time}\n")
            f.write(f"Task Enabled: True\n")
        
        scheduled_now = False
        try:
            sys.path.insert(0, os.path.join(script_dir, "Backend", "Extra"))
            from Chat import schedule_task_dynamically
            task_data = {
                "name": name,
                "description": task_prompt,
                "task_mode": task_mode,
                "timer_type": timer_type,
                "minutes": minutes,
                "specific_time": specific_time,
                "task_enabled": True
            }
            scheduled_now = schedule_task_dynamically(task_data)
        except:
            pass
        
        if scheduled_now:
            return f"Task '{name}' created and scheduled successfully. It will fire in {minutes} minute(s) during this active chat session."
        else:
            return f"Task '{name}' created successfully. It will be enabled and ready to fire during chat sessions with 'Tasks Enabled' mode."
    except Exception as e:
        return f"Error creating task: {e}"
