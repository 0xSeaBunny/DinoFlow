"""Utility functions for Ollama integration."""
import subprocess
import platform
import threading


def get_startupinfo():

    if platform.system() == "Windows":
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = 0
        return si
    return None


def run_in_thread(fn, on_done, on_error):

    def run():
        try:
            result = fn()
            on_done(result)
        except Exception as e:
            on_error(str(e))
    threading.Thread(target=run, daemon=True).start()
