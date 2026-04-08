import asyncio
import threading
import json
import requests
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from Tools import TOOL_DEFINITIONS as TOOLS, execute_tool as _execute_tool

OLLAMA_API = "http://localhost:11434/api/chat"

conversation_histories = {}
current_model = "llama3.2:latest"
bot_paused = True
message_callback = None
is_thinking = False

def set_thinking(state):
    global is_thinking
    is_thinking = state

telegram_app = None


def set_model(model_name):
    global current_model
    current_model = model_name


def set_paused(state):
    global bot_paused
    bot_paused = state


def set_message_callback(callback):

    global message_callback
    message_callback = callback


def get_model_response_with_screenshot(model_name, message_content, user_id):
    if user_id not in conversation_histories:
        conversation_histories[user_id] = []
    
    conversation_histories[user_id].append({"role": "user", "content": message_content})
    screenshot_path = None
    tool_calls_list = []
    
    try:
        while True:
            payload = {
                "model": model_name,
                "messages": conversation_histories[user_id],
                "tools": TOOLS,
                "stream": False
            }
            
            resp = requests.post(OLLAMA_API, json=payload, timeout=120)
            resp.raise_for_status()
            data = resp.json()
            msg = data.get("message", {})
            
            tool_calls = msg.get("tool_calls")
            if tool_calls:
                conversation_histories[user_id].append(msg)
                for call in tool_calls:
                    fn = call.get("function", {})
                    name = fn.get("name")
                    args = fn.get("arguments", {})
                    if isinstance(args, str):
                        args = json.loads(args)
                    
                    tool_calls_list.append({"name": name, "args": args})
                    
                    result = _execute_tool(name, args)
                    

                    if name == "take_screenshot" and "saved to:" in result:
                        try:
                            after_saved = result.split("saved to:")[1].strip()
                            path_part = after_saved.split()[0].rstrip(".")
                            screenshot_path = path_part
                        except:
                            pass
                    
                    conversation_histories[user_id].append({
                        "role": "tool",
                        "content": result
                    })
            else:
                content = msg.get("content", "").strip()
                if content:
                    conversation_histories[user_id].append({"role": "assistant", "content": content})
                    return content, screenshot_path, tool_calls_list
                return "No response from model.", screenshot_path, tool_calls_list
                
    except Exception as e:
        return f"Error: {str(e)}", screenshot_path, tool_calls_list


async def handle_telegram_message(update, context):
    global bot_paused, current_model, message_callback, is_thinking
    
    if update.effective_user.is_bot:
        return
    
    message_text = update.message.text
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    if is_thinking:
        await update.message.reply_text(
            "Your agent is already thinking, so your last prompt was thrown away"
        )
        return
    
    if message_callback:
        try:
            user_name = update.effective_user.username or update.effective_user.first_name
            message_callback("telegram_in", f"[Telegram] {user_name}: {message_text}")
        except:
            pass
    
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    
    if bot_paused:
        await update.message.reply_text(
            "Bot is paused. Please start a chat session in DinoFlow to activate the model."
        )
        return
    
    model_name = current_model
    
    def process_message():
        return get_model_response_with_screenshot(model_name, message_text, user_id)
    
    response, screenshot_path, tool_calls_list = await asyncio.get_event_loop().run_in_executor(None, process_message)
    
    for tool_call in tool_calls_list:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        args_str = ", ".join([f"{k}={v}" for k, v in tool_args.items()])
        tool_msg = f"[Tool: {tool_name}({args_str})]"
        
        await update.message.reply_text(tool_msg)
        
        if message_callback:
            try:
                message_callback("telegram_out", f"[Telegram Bot] {tool_msg}")
            except:
                pass
    if message_callback:
        try:
            message_callback("telegram_out", f"[Telegram Bot] {response}")
        except:
            pass
    
    if len(response) > 4000:
        response = response[:3997] + "..."
    
    await update.message.reply_text(response)
    
    if screenshot_path:
        if os.path.isfile(screenshot_path):
            try:
                await context.bot.send_photo(chat_id=chat_id, photo=open(screenshot_path, 'rb'))
                screenshot_note = f"[Screenshot captured and sent to Telegram: {screenshot_path}]"
                conversation_histories[user_id].append({
                    "role": "system",
                    "content": screenshot_note
                })
            except Exception as e:
                await update.message.reply_text(f"[Screenshot error: {e}]")
        else:
            await update.message.reply_text(f"[Screenshot file not found: {screenshot_path}]")


class TelegramBotManager:
    
    def __init__(self):
        self.app = None
        self.thread = None
        self.running = False
        self.paused = True
        self._token = None
        self._status_callback = None
    
    def set_status_callback(self, callback):
        self._status_callback = callback
    
    def _notify_status(self, is_paused):
        if self._status_callback:
            if is_paused:
                self._status_callback(True, "Status: On (Paused)", "orange")
            else:
                self._status_callback(False, "Status: On (Active)", "green")
    
    def start(self, token, callback=None):
        if self.running:
            return False, "Bot is already running"
        
        self._token = token
        
        def run_bot():
            try:
                global telegram_app
                
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                from telegram.ext import Application
                
                self.app = Application.builder().token(token).build()
                telegram_app = self.app
                
                from telegram.ext import MessageHandler, filters
                self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_telegram_message))
                
                async def start_polling():
                    await self.app.initialize()
                    await self.app.start()
                    await self.app.updater.start_polling(allowed_updates=["message"])
                
                self._event_loop = loop
                
                loop.run_until_complete(start_polling())
                
                loop.run_forever()
            except Exception as e:
                import traceback
                print(f"Telegram bot error: {e}\n{traceback.format_exc()}")
        
        self.thread = threading.Thread(target=run_bot, daemon=True)
        self.thread.start()
        self.running = True
        self.paused = True
        
        if callback:
            set_message_callback(callback)
        
        return True, "Bot started"
    
    def set_model(self, model_name):
        set_model(model_name)
        return True
    
    def pause(self):
        self.paused = True
        set_paused(True)
        self._notify_status(True)
        return True, "Bot paused"
    
    def unpause(self):
        self.paused = False
        set_paused(False)
        self._notify_status(False)
        return True, "Bot unpaused"
    
    def is_paused(self):
        return self.paused
    
    def stop(self):
        if not self.running:
            return False, "Bot is not running"
        
        if self.app:
            try:
                self.app.stop()
            except Exception as e:
                print(f"Error stopping bot: {e}")
        
        self.running = False
        return True, "Bot stopped"
    
    def is_running(self):
        return self.running and self.thread and self.thread.is_alive()
    
    def send_message_to_chat(self, chat_id, message):
        if not self.running or not self.app:
            return False, "Bot is not running"
        
        try:
            if isinstance(chat_id, str):
                chat_id = int(chat_id)
        except ValueError:
            return False, f"Invalid chat ID format: {chat_id}"
        
        async def send_msg():
            try:
                if len(message) > 4000:
                    chunks = [message[i:i+4000] for i in range(0, len(message), 4000)]
                    for chunk in chunks:
                        await self.app.bot.send_message(chat_id=chat_id, text=chunk)
                else:
                    await self.app.bot.send_message(chat_id=chat_id, text=message)
                
                return True, "Message sent successfully"
            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                print(f"Telegram send_msg error: {e}\n{error_details}")
                return False, f"Error sending message: {e}"
        
        try:
            future = asyncio.run_coroutine_threadsafe(send_msg(), self.app._event_loop)
            success, result = future.result(timeout=10)
            return success, result
        except Exception as e:
            return False, f"Failed to send message: {e}"


telegram_bot_manager = TelegramBotManager()


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        token = sys.argv[1]
        telegram_bot_manager.start(token)
        input("Press Enter to stop...")
        telegram_bot_manager.stop()
    else:
        print("Usage: python TelegramBot.py <bot_token>")
