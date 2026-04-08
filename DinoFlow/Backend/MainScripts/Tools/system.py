"""System operation tools for DinoFlow."""
import os
import sys
import psutil
import datetime
import subprocess
import heapq
import ast


def get_system_info():
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        if sys.platform == "win32":
            system_drive = os.environ.get('SystemDrive', 'C:')
            disk = psutil.disk_usage(system_drive + '\\')
        else:
            disk = psutil.disk_usage("/")
        info = [
            f"CPU: {cpu_percent}%",
            f"RAM: {memory.percent}% used ({memory.used // (1024**3)}GB / {memory.total // (1024**3)}GB)",
            f"Disk: {disk.percent}% used ({disk.used // (1024**3)}GB / {disk.total // (1024**3)}GB)"
        ]
        return "\n".join(info)
    except Exception as e:
        return f"Error getting system info: {e}"


def get_current_time():
    try:
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        return f"Error getting time: {e}"


def list_processes(limit=20):
    try:
        processes = []
        idx = 0
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                pinfo = proc.info
                cpu_val = pinfo.get('cpu_percent', 0) or 0
                processes.append((-cpu_val, idx, pinfo))
                idx += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        top_n = heapq.nsmallest(limit, processes)

        lines = [f"{'PID':<8} {'Name':<25} {'CPU%':<8} {'RAM%':<8}", "-" * 50]
        for neg_cpu, _, p in top_n:
            lines.append(f"{p['pid']:<8} {p['name'][:24]:<25} {p.get('cpu_percent', 0):<8.1f} {p.get('memory_percent', 0):<8.1f}")
        return "\n".join(lines)
    except Exception as e:
        return f"Error listing processes: {e}"


def run_shell_command(command, timeout=30):
    blocked = ["rm -rf /", "dd if=/dev/zero", "mkfs", "mkfs.ext", "mkfs.ntfs", ">/dev/sda", "shutdown", "reboot", "halt", "init 0"]
    for bad in blocked:
        if bad in command.lower():
            return f"Error: Command blocked for safety (contains '{bad}')"
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=timeout)
        output = result.stdout
        if result.stderr:
            output += f"\n[stderr]: {result.stderr}"
        return f"Exit code: {result.returncode}\n{output[:2000]}"
    except subprocess.TimeoutExpired:
        return f"Error: Command timed out after {timeout} seconds"
    except Exception as e:
        return f"Error executing command: {e}"


def run_python_code(code, timeout=10):
    BLOCKED_IMPORTS = {'os', 'sys', 'subprocess', 'shutil', 'pathlib', 'socket', 'urllib', 'http', 'ftplib'}
    BLOCKED_CALLS = {'open', 'exec', 'eval', 'compile', '__import__', 'input', 'breakpoint'}

    try:
        tree = ast.parse(code)

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in BLOCKED_IMPORTS or any(alias.name.startswith(m + '.') for m in BLOCKED_IMPORTS):
                        return f"Error: Import '{alias.name}' is blocked for security"

            if isinstance(node, ast.ImportFrom):
                if node.module in BLOCKED_IMPORTS:
                    return f"Error: Import from '{node.module}' is blocked for security"

            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in BLOCKED_CALLS:
                        return f"Error: Function '{node.func.id}' is blocked for security"

                if isinstance(node.func, ast.Attribute):
                    if node.func.attr in {'system', 'popen', 'spawn', 'call', 'run'}:
                        return f"Error: Method '{node.func.attr}' is blocked for security"

            if isinstance(node, ast.Name):
                if node.id == '__builtins__':
                    return "Error: Access to __builtins__ is blocked for security"

        python_cmd = "python" if sys.platform == "win32" else "python3"
        result = subprocess.run([python_cmd, "-c", code], capture_output=True, text=True, timeout=timeout)
        output = result.stdout
        if result.stderr:
            output += f"\n[stderr]: {result.stderr}"
        return f"Exit code: {result.returncode}\n{output[:2000]}"
    except subprocess.TimeoutExpired:
        return f"Error: Code execution timed out after {timeout} seconds"
    except SyntaxError as e:
        return f"Error: Invalid Python syntax: {e}"
    except Exception as e:
        return f"Error executing code: {e}"


def kill_process(pid_or_name, force=False):
    ollama_names = ['ollama', 'ollama.exe', 'ollama_llama_server']
    try:
        pid = int(pid_or_name)
        try:
            proc = psutil.Process(pid)
            proc_name = proc.name().lower()
            if any(name in proc_name for name in ollama_names):
                return f"Error: Cannot kill Ollama process {pid} ({proc.name()}) - protected to keep the AI running"
        except:
            pass
    except ValueError:
        name_lower = pid_or_name.lower()
        if any(ollama in name_lower for ollama in ollama_names):
            return f"Error: Cannot kill Ollama process '{pid_or_name}' - protected to keep the AI running"
    
    try:
        try:
            pid = int(pid_or_name)
            try:
                proc = psutil.Process(pid)
                proc_name = proc.name()
                if force:
                    proc.kill()
                else:
                    proc.terminate()
                return f"Successfully {'force killed' if force else 'terminated'} process {pid} ({proc_name})"
            except psutil.NoSuchProcess:
                return f"Error: No process found with PID {pid}"
            except psutil.AccessDenied:
                return f"Error: Access denied to kill process {pid}. Try running with sudo/admin privileges."
        except ValueError:
            name = pid_or_name
            killed = []
            errors = []
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if proc.info['name'].lower() == name.lower():
                        p = psutil.Process(proc.info['pid'])
                        if force:
                            p.kill()
                        else:
                            p.terminate()
                        killed.append(proc.info['pid'])
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            if killed:
                action = "force killed" if force else "terminated"
                return f"Successfully {action} {len(killed)} process(es) named '{name}': PIDs {killed}"
            else:
                return f"Error: No process named '{name}' found or no permission to kill it"
    except Exception as e:
        return f"Error killing process: {e}"


def start_process(command, shell=True, wait=False, timeout=30):
    try:
        if wait:
            result = subprocess.run(
                command,
                shell=shell,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            output = result.stdout
            if result.stderr:
                output += f"\n[stderr]: {result.stderr}"
            return f"Process completed with exit code {result.returncode}\n{output[:2000]}"
        else:
            if sys.platform == "win32":
                process = subprocess.Popen(
                    command,
                    shell=shell,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                )
            else:
                process = subprocess.Popen(
                    command,
                    shell=shell,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True
                )
            return f"Started process with PID {process.pid}"
    except subprocess.TimeoutExpired:
        return f"Error: Process timed out after {timeout} seconds"
    except Exception as e:
        return f"Error starting process: {e}"
