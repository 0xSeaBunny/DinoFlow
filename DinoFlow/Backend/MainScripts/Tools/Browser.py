from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
import time
import base64
import threading

_browser = None
_browser_lock = threading.Lock()


def _get_browser():
    global _browser
    if _browser is None:
        try:
            chrome_options = Options()
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            
            service = Service(ChromeDriverManager().install())
            _browser = webdriver.Chrome(service=service, options=chrome_options)
        except Exception as e:
            return None, f"Failed to launch browser: {e}"
    return _browser, None


def _close_browser():
    global _browser
    if _browser:
        try:
            _browser.quit()
        except:
            pass
        _browser = None


def launch_browser(headless: bool = False):
    with _browser_lock:
        global _browser
        
        _close_browser()
        
        try:
            chrome_options = Options()
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            if headless:
                chrome_options.add_argument("--headless")
            
            service = Service(ChromeDriverManager().install())
            _browser = webdriver.Chrome(service=service, options=chrome_options)
            
            return "Browser launched successfully"
        except Exception as e:
            return f"Error launching browser: {e}"


def navigate_to(url: str, wait_seconds: float = 2.0):
    with _browser_lock:
        browser, error = _get_browser()
        if error:
            return error
        
        try:
            browser.set_page_load_timeout(30)
            browser.get(url)
            time.sleep(wait_seconds)
            title = browser.title
            return f"Navigated to: {title}\nURL: {browser.current_url}"
        except Exception as e:
            return f"Error navigating to {url}: {e}"


def get_page_text():
    with _browser_lock:
        browser, error = _get_browser()
        if error:
            return error
        
        try:
            body = browser.find_element(By.TAG_NAME, "body")
            text = body.text
            if len(text) > 8000:
                text = text[:8000] + "\n\n[Content truncated - page too long]"
            return text
        except Exception as e:
            return f"Error getting page text: {e}"


def click_element(selector: str, by: str = "css", wait_seconds: float = 1.0):
    with _browser_lock:
        browser, error = _get_browser()
        if error:
            return error
        
        try:
            by_method = By.CSS_SELECTOR if by == "css" else By.XPATH
            element = WebDriverWait(browser, 10).until(
                EC.element_to_be_clickable((by_method, selector))
            )
            element.click()
            time.sleep(wait_seconds)
            return f"Clicked element: {selector}"
        except TimeoutException:
            return f"Element not found or not clickable: {selector}"
        except Exception as e:
            return f"Error clicking element: {e}"


def find_elements(selector: str, by: str = "css"):
    with _browser_lock:
        browser, error = _get_browser()
        if error:
            return error
        
        try:
            by_method = By.CSS_SELECTOR if by == "css" else By.XPATH
            elements = browser.find_elements(by_method, selector)
            
            if not elements:
                return f"No elements found matching: {selector}"
            
            results = []
            for i, elem in enumerate(elements[:10], 1):
                text = elem.text[:100]
                tag = elem.tag_name
                elem_id = elem.get_attribute("id") or ""
                elem_class = elem.get_attribute("class") or ""
                
                desc = f"[{i}] <{tag}>"
                if elem_id:
                    desc += f" id='{elem_id}'"
                if elem_class:
                    desc += f" class='{elem_class[:50]}'"
                if text:
                    desc += f" text='{text}'"
                
                results.append(desc)
            
            if len(elements) > 10:
                results.append(f"\n... and {len(elements) - 10} more elements")
            
            return "\n".join(results)
        except Exception as e:
            return f"Error finding elements: {e}"


def scroll_page(direction: str = "down", amount: int = 500):
    with _browser_lock:
        browser, error = _get_browser()
        if error:
            return error
        
        try:
            if direction == "down":
                browser.execute_script(f"window.scrollBy(0, {amount});")
            else:
                browser.execute_script(f"window.scrollBy(0, -{amount});")
            return f"Scrolled {direction} by {amount} pixels"
        except Exception as e:
            return f"Error scrolling: {e}"


def close_browser():
    with _browser_lock:
        global _browser
        if _browser:
            _close_browser()
            return "Browser closed"
        return "No browser was running"
