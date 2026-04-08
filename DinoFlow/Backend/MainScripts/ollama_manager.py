"""Ollama Manager - Handles Ollama CLI operations."""
import subprocess
import os
from utils import get_startupinfo, run_in_thread


def _run_ollama_command(command, timeout=30):

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            startupinfo=get_startupinfo()
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except FileNotFoundError:
        return False, "", "Ollama not found in PATH"
    except Exception as e:
        return False, "", str(e)


def get_installed_models():

    success, stdout, stderr = _run_ollama_command(["ollama", "list"], timeout=30)

    if not success:
        return None, stderr

    lines = stdout.strip().split("\n")
    models = []

    if len(lines) > 1:
        header = lines[0]
        name_start = header.find("NAME")
        id_start = header.find("ID")
        size_start = header.find("SIZE")
        mod_start = header.find("MODIFIED")

        for line in lines[1:]:
            if line.strip():
                models.append({
                    "name": line[name_start:id_start].strip(),
                    "id": line[id_start:size_start].strip(),
                    "size": line[size_start:mod_start].strip(),
                    "modified": line[mod_start:].strip()
                })

    return models, None


def uninstall_model(model_name):

    success, stdout, stderr = _run_ollama_command(["ollama", "rm", model_name], timeout=30)
    if success:
        return True, None
    return False, stderr.strip() or stdout.strip()


def download_model(model_name, on_done, on_error):

    def fn():
        success, stdout, stderr = _run_ollama_command(["ollama", "pull", model_name], timeout=600)
        if not success:
            raise Exception(stderr.strip() or stdout.strip() or "Unknown error")
        return model_name

    run_in_thread(fn, on_done, on_error)


def get_model_folder(model_name):

    base_dir = os.path.expandvars(r"%USERPROFILE%\.ollama\models") if os.name == "nt" else os.path.expanduser("~/.ollama/models")
    if not os.path.exists(base_dir):
        return None
    for root, dirs, _ in os.walk(base_dir):
        for d in dirs:
            if model_name.lower() in d.lower():
                return os.path.join(root, d)
    return None
