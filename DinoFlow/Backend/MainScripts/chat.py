"""Chat - Basic chat functionality with Ollama models."""
import subprocess
import threading
import time
import sys

from utils import get_startupinfo


def close_model(process):
    try:
        if process and process.poll() is None:
            process.terminate()
            process.wait(timeout=5)
    except Exception:
        pass


def send_to_process(model_name, message, on_response, on_error):

    def run():
        process = None
        try:
            process = subprocess.Popen(
                ["ollama", "run", model_name],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                encoding="utf-8",
                errors="replace",
                startupinfo=get_startupinfo()
            )
            stdout, stderr = process.communicate(input=message + "\n")
            response = stdout.strip()
            if response:
                on_response(response)
            else:
                on_error(stderr.strip() or "No response received.")
        except FileNotFoundError:
            on_error("Ollama not found in PATH.")
        except Exception as e:
            on_error(str(e))
        finally:
            close_model(process)

    threading.Thread(target=run, daemon=True).start()
