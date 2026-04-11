import sys
import subprocess
import time

try:
    import pyautogui
    _PYAUTOGUI_AVAILABLE = True
except ImportError:
    _PYAUTOGUI_AVAILABLE = False


def type_text(text, interval=0.01):
    try:
        if sys.platform == "win32":
            if _PYAUTOGUI_AVAILABLE:
                pyautogui.typewrite(text, interval=interval)
                return f"Typed: '{text[:50]}{'...' if len(text) > 50 else ''}'"
            import ctypes
            
            user32 = ctypes.windll.user32
            
            VK_SHIFT = 0x10
            KEYEVENTF_KEYUP = 0x0002
            
            for char in text:
                vk = user32.VkKeyScanW(ord(char))
                if vk == -1:
                    continue
                
                scan_code = vk & 0xFF
                shift = (vk >> 8) & 1
                
                if shift:
                    user32.keybd_event(VK_SHIFT, 0, 0, 0)
                
                user32.keybd_event(scan_code, 0, 0, 0)
                user32.keybd_event(scan_code, 0, KEYEVENTF_KEYUP, 0)
                
                if shift:
                    user32.keybd_event(VK_SHIFT, 0, KEYEVENTF_KEYUP, 0)
                
                time.sleep(interval)
            
            return f"Typed: '{text[:50]}{'...' if len(text) > 50 else ''}'"
        elif sys.platform == "darwin":
            escaped_text = text.replace('"', '\\"')
            result = subprocess.run(
                ["osascript", "-e", f'tell application "System Events" to keystroke "{escaped_text}"'],
                capture_output=True,
                timeout=30
            )
            if result.returncode == 0:
                return f"Typed: '{text[:50]}{'...' if len(text) > 50 else ''}'"
            return f"Error typing text: {result.stderr.decode()}"
        else:
            escaped_text = text.replace("'", "'\\''")
            result = subprocess.run(
                ["xdotool", "type", "--delay", str(int(interval * 1000)), text],
                capture_output=True,
                timeout=30
            )
            if result.returncode == 0:
                return f"Typed: '{text[:50]}{'...' if len(text) > 50 else ''}'"
            return f"Error typing text (xdotool required): {result.stderr.decode()}"
    except Exception as e:
        return f"Error typing text: {e}"


def press_key(key_combination):
    try:
        keys = key_combination.lower().split("+")
        
        if sys.platform == "win32":
            if _PYAUTOGUI_AVAILABLE:
                pyautogui.hotkey(*keys)
                return f"Pressed: {key_combination}"
            import ctypes
            
            user32 = ctypes.windll.user32
            KEYEVENTF_KEYUP = 0x0002

            key_map = {
                'ctrl': 0x11, 'control': 0x11,
                'alt': 0x12, 'menu': 0x12,
                'shift': 0x10,
                'win': 0x5B, 'windows': 0x5B,
                'tab': 0x09,
                'enter': 0x0D, 'return': 0x0D,
                'esc': 0x1B, 'escape': 0x1B,
                'space': 0x20,
                'backspace': 0x08, 'bksp': 0x08,
                'delete': 0x2E, 'del': 0x2E,
                'insert': 0x2D, 'ins': 0x2D,
                'home': 0x24,
                'end': 0x23,
                'pgup': 0x21, 'pageup': 0x21,
                'pgdn': 0x22, 'pagedown': 0x22,
                'up': 0x26,
                'down': 0x28,
                'left': 0x25,
                'right': 0x27,
                'f1': 0x70, 'f2': 0x71, 'f3': 0x72, 'f4': 0x73,
                'f5': 0x74, 'f6': 0x75, 'f7': 0x76, 'f8': 0x77,
                'f9': 0x78, 'f10': 0x79, 'f11': 0x7A, 'f12': 0x7B,
            }
            

            vk_codes = []
            for key in keys:
                key = key.strip()
                if key in key_map:
                    vk_codes.append(key_map[key])
                elif len(key) == 1:
                    vk = user32.VkKeyScanW(ord(key.upper()))
                    if vk != -1:
                        vk_codes.append(vk & 0xFF)
            

            for vk in vk_codes:
                user32.keybd_event(vk, 0, 0, 0)
            

            for vk in reversed(vk_codes):
                user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)
            
            return f"Pressed: {key_combination}"
        elif sys.platform == "darwin":
            key_map = {
                'ctrl': 'control', 'control': 'control',
                'cmd': 'command', 'command': 'command',
                'alt': 'option', 'option': 'option',
                'shift': 'shift',
            }
            
            modifiers = []
            main_key = None
            
            for key in keys:
                key = key.strip()
                if key in key_map:
                    modifiers.append(key_map[key])
                else:
                    main_key = key
            
            if main_key:
                if modifiers:
                    mod_str = " using {" + ", ".join(modifiers) + "}"
                    script = f'tell application "System Events" to keystroke "{main_key}"{mod_str}'
                else:
                    script = f'tell application "System Events" to keystroke "{main_key}"'
                
                result = subprocess.run(
                    ["osascript", "-e", script],
                    capture_output=True,
                    timeout=10
                )
                if result.returncode == 0:
                    return f"Pressed: {key_combination}"
                return f"Error pressing keys: {result.stderr.decode()}"
            return "Error: No main key specified"
        else:
            xdo_keys = []
            for key in keys:
                key = key.strip()
                if key in ['ctrl', 'control']:
                    xdo_keys.append('ctrl')
                elif key in ['alt']:
                    xdo_keys.append('alt')
                elif key in ['shift']:
                    xdo_keys.append('shift')
                elif key in ['win', 'windows', 'super']:
                    xdo_keys.append('super')
                else:
                    xdo_keys.append(key)
            
            key_str = "+".join(xdo_keys)
            result = subprocess.run(
                ["xdotool", "key", key_str],
                capture_output=True,
                timeout=10
            )
            if result.returncode == 0:
                return f"Pressed: {key_combination}"
            return f"Error pressing keys (xdotool required): {result.stderr.decode()}"
    except Exception as e:
        return f"Error pressing keys: {e}"


def _get_screen_size():
    try:
        if sys.platform == "win32":
            if _PYAUTOGUI_AVAILABLE:
                return pyautogui.size()
            import ctypes
            user32 = ctypes.windll.user32
            width = user32.GetSystemMetrics(0)
            height = user32.GetSystemMetrics(1)
            return width, height
        else:
            result = subprocess.run(
                ["xdotool", "getdisplaygeometry"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                parts = result.stdout.strip().split()
                return int(parts[0]), int(parts[1])
            return None, None
    except Exception as e:
        return None, None


def get_mouse_position():
    try:
        if sys.platform == "win32":
            if _PYAUTOGUI_AVAILABLE:
                x, y = pyautogui.position()
                return f"Mouse position: X={x}, Y={y}"
            import ctypes
            from ctypes import wintypes
            
            user32 = ctypes.windll.user32
            pt = wintypes.POINT()
            user32.GetCursorPos(ctypes.byref(pt))
            return f"Mouse position: X={pt.x}, Y={pt.y}"
        else:
            result = subprocess.run(
                ["xdotool", "getmouselocation"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                parts = result.stdout.strip().split()
                x = int(parts[0].split(":")[1])
                y = int(parts[1].split(":")[1])
                return f"Mouse position: X={x}, Y={y}"
            return "Error: Could not get mouse position (xdotool required)"
    except Exception as e:
        return f"Error getting mouse position: {e}"


def move_mouse(x, y):
    try:
        if sys.platform == "win32":
            if _PYAUTOGUI_AVAILABLE:
                pyautogui.moveTo(x, y)
                return f"Mouse moved to X={x}, Y={y}"
            import ctypes
            
            user32 = ctypes.windll.user32
            success = user32.SetCursorPos(x, y)
            if success:
                return f"Mouse moved to X={x}, Y={y}"
            return "Error: Failed to move mouse"
        else:
            result = subprocess.run(
                ["xdotool", "mousemove", str(x), str(y)],
                capture_output=True,
                timeout=5
            )
            if result.returncode == 0:
                return f"Mouse moved to X={x}, Y={y}"
            return "Error: Could not move mouse (xdotool required)"
    except Exception as e:
        return f"Error moving mouse: {e}"


def click_mouse(button="left"):
    try:
        if button not in ("left", "right", "middle"):
            return f"Error: Invalid button '{button}'. Use 'left', 'right', or 'middle'."
        
        if sys.platform == "win32":
            if _PYAUTOGUI_AVAILABLE:
                if button == "left":
                    pyautogui.click()
                elif button == "right":
                    pyautogui.rightClick()
                else:
                    pyautogui.middleClick()
                return f"{button.capitalize()} mouse button clicked"
            import ctypes
            
            user32 = ctypes.windll.user32
            
            MOUSEEVENTF_LEFTDOWN = 0x0002
            MOUSEEVENTF_LEFTUP = 0x0004
            MOUSEEVENTF_RIGHTDOWN = 0x0008
            MOUSEEVENTF_RIGHTUP = 0x0010
            MOUSEEVENTF_MIDDLEDOWN = 0x0020
            MOUSEEVENTF_MIDDLEUP = 0x0040
            
            if button == "left":
                user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
            elif button == "right":
                user32.mouse_event(MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
                user32.mouse_event(MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
            else:
                user32.mouse_event(MOUSEEVENTF_MIDDLEDOWN, 0, 0, 0, 0)
                user32.mouse_event(MOUSEEVENTF_MIDDLEUP, 0, 0, 0, 0)
            
            return f"{button.capitalize()} mouse button clicked"
        else:
            xdotool_button = "1" if button == "left" else "3" if button == "right" else "2"
            result = subprocess.run(
                ["xdotool", "click", xdotool_button],
                capture_output=True,
                timeout=5
            )
            if result.returncode == 0:
                return f"{button.capitalize()} mouse button clicked"
            return "Error: Could not click mouse (xdotool required)"
    except Exception as e:
        return f"Error clicking mouse: {e}"


def scroll_mouse(direction="down", amount=3):
    try:
        if direction not in ("up", "down"):
            return f"Error: Invalid direction '{direction}'. Use 'up' or 'down'."
        
        if sys.platform == "win32":
            if _PYAUTOGUI_AVAILABLE:
                clicks = amount if direction == "down" else -amount
                pyautogui.scroll(clicks * 100)
                return f"Scrolled {direction} by {amount} units"
            import ctypes
            
            user32 = ctypes.windll.user32
            
            WHEEL_DELTA = 120
            clicks = amount if direction == "down" else -amount
            wheel_amount = clicks * WHEEL_DELTA
            
            user32.mouse_event(0x0800, 0, 0, wheel_amount, 0)
            
            return f"Scrolled {direction} by {amount} units"
        else:
            button = "5" if direction == "down" else "4"
            result = subprocess.run(
                ["xdotool", "click", "--repeat", str(amount), button],
                capture_output=True,
                timeout=5
            )
            if result.returncode == 0:
                return f"Scrolled {direction} by {amount} units"
            return "Error: Could not scroll (xdotool required)"
    except Exception as e:
        return f"Error scrolling mouse: {e}"
