try:
    import discord
    from discord.ext import commands
    DISCORD_AVAILABLE = True
except ImportError:
    DISCORD_AVAILABLE = False
    discord = None
    commands = None

import asyncio
import threading
import json
import requests
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "Tools"))
from Tools import TOOL_DEFINITIONS as TOOLS
from Tools import execute_tool as _execute_tool

OLLAMA_API = "http://localhost:11434/api/chat"

# Initialize bot only if discord is available
if DISCORD_AVAILABLE:
    intents = discord.Intents.default()
    intents.message_content = True
    bot = commands.Bot(command_prefix="/GF", intents=intents)
else:
    bot = None

conversation_histories = {}
current_model = "llama3.2:latest"
bot_paused = True
message_callback = None
is_thinking = False  # Flag to track if model is processing

def set_thinking(state):
    """Set the thinking state from DinoFlow."""
    global is_thinking
    is_thinking = state

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
    """Send message to Ollama and get response with tool support, tracking screenshots and tool calls"""
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
                    
                    # Track this tool call
                    tool_calls_list.append({"name": name, "args": args})
                    
                    result = _execute_tool(name, args)
                    
                    # Track screenshot path
                    if name in ("take_screenshot", "screenshot_browser") and "saved to:" in result:
                        try:
                            # Extract path - handle "saved to: /path/file.png. Some text..."
                            after_saved = result.split("saved to:")[1].strip()
                            # Get just the path (up to first space or period followed by space)
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

if DISCORD_AVAILABLE:
    @bot.event
    async def on_ready():
        print(f"DinoFlow Discord Bot logged in as {bot.user}")

    @bot.event
    async def on_message(message):
        if message.author == bot.user:
            return
        
        if message.content.startswith("/GF"):
            query = message.content[3:].strip()
            if not query:
                await message.channel.send("Please provide a message after /GF")
                return
            
            global current_model, bot_paused, message_callback, is_thinking
            
            # Check if model is already thinking
            if is_thinking:
                await message.channel.send("Your agent is already thinking, so your last prompt was thrown away")
                return
            
            # Notify GUI of incoming Discord message
            if message_callback:
                try:
                    message_callback("discord_in", f"[Discord] {message.author.display_name}: {query}")
                except:
                    pass
            
            await message.channel.send("Thinking...")
            
            if bot_paused:
                await message.channel.send("Bot is paused. Please start a chat session in DinoFlow to activate the model.")
                return
            
            model_name = current_model
            
            def run_model():
                return get_model_response_with_screenshot(model_name, query, message.author.id)
            
            response, screenshot_path, tool_calls_list = await asyncio.get_event_loop().run_in_executor(None, run_model)
            
            # Notify about each tool used
            for tool_call in tool_calls_list:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                args_str = ", ".join([f"{k}={v}" for k, v in tool_args.items()])
                tool_msg = f"[Tool: {tool_name}({args_str})]"
                
                # Send to Discord
                await message.channel.send(tool_msg)
                
                # Send to GUI
                if message_callback:
                    try:
                        message_callback("discord_out", f"[Discord Bot] {tool_msg}")
                    except:
                        pass
            
            # Notify GUI of bot response
            if message_callback:
                try:
                    message_callback("discord_out", f"[Discord Bot] {response}")
                except:
                    pass
            
            if len(response) > 2000:
                response = response[:1997] + "..."
            
            await message.channel.send(response)
            
            # Send screenshot if one was taken (after text response)
            if screenshot_path:
                if os.path.isfile(screenshot_path):
                    try:
                        await message.channel.send(file=discord.File(screenshot_path))
                        # Add screenshot info to conversation for context
                        screenshot_note = f"[Screenshot captured and sent to Discord: {screenshot_path}]"
                        conversation_histories[message.author.id].append({
                            "role": "system",
                            "content": screenshot_note
                        })
                    except Exception as e:
                        await message.channel.send(f"[Screenshot error: {e}]")
                else:
                    await message.channel.send(f"[Screenshot file not found: {screenshot_path}]")
        
        await bot.process_commands(message)

class DiscordBotManager:
    def __init__(self):
        self.bot = bot
        self.thread = None
        self.running = False
        self.paused = True
        self._loop = None
        self._token = None
        self._status_callback = None
    
    def set_status_callback(self, callback):
        """Set callback for status updates. Called with (is_paused, status_text, color)."""
        self._status_callback = callback
    
    def _notify_status(self, is_paused):
        """Notify status callback of pause state change."""
        if self._status_callback:
            if is_paused:
                self._status_callback(True, "Status: On (Paused)", "orange")
            else:
                self._status_callback(False, "Status: On (Active)", "green")
    
    def start(self, token, callback=None):
        if not DISCORD_AVAILABLE:
            return False, "discord.py is not installed. Install it with: pip install discord.py"
        if self.running:
            return False, "Bot is already running"
        
        self._token = token
        
        def run_bot():
            try:
                # Create new event loop for this thread
                self._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._loop)
                bot.run(token)
            except Exception as e:
                print(f"Bot error: {e}")
            finally:
                self._loop = None
        
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
        
        # Schedule bot close on the bot's event loop if it exists
        if self._loop and self._loop.is_running() and bot:
            try:
                # Use call_soon_threadsafe to schedule from different thread
                self._loop.call_soon_threadsafe(bot.close)
            except Exception as e:
                print(f"Error scheduling bot close: {e}")
        
        self.running = False
        return True, "Bot stopped"
    
    def send_message_to_channel(self, channel_id, message):
        """Send a message to a specific Discord channel.
        
        Args:
            channel_id: Discord channel ID (string or int)
            message: Message text to send
        
        Returns:
            (success: bool, result: str)
        """
        if not DISCORD_AVAILABLE or not bot:
            return False, "discord.py is not installed"
        if not self.running:
            return False, "Bot is not running"
        
        # Wait a moment for loop to be available if bot just started
        if self._loop is None:
            import time
            time.sleep(0.5)
            if self._loop is None:
                return False, "Bot event loop not available"
        
        try:
            # Convert channel_id to int if it's a string
            if isinstance(channel_id, str):
                channel_id = int(channel_id)
        except ValueError:
            return False, f"Invalid channel ID format: {channel_id}"
        
        async def send_msg():
            try:
                channel = bot.get_channel(channel_id)
                if not channel:
                    # Try fetching the channel if not in cache
                    try:
                        channel = await bot.fetch_channel(channel_id)
                    except Exception as fetch_err:
                        return False, f"Failed to fetch channel {channel_id}: {fetch_err}"
                
                if not channel:
                    return False, f"Channel {channel_id} not found"
                
                # Discord message limit is 2000 characters
                if len(message) > 2000:
                    # Split into chunks
                    chunks = [message[i:i+1990] for i in range(0, len(message), 1990)]
                    for chunk in chunks:
                        await channel.send(chunk)
                else:
                    await channel.send(message)
                
                return True, "Message sent successfully"
            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                print(f"Discord send_msg error: {e}\n{error_details}")
                return False, f"Error sending message: {e}"
        
        # Schedule the coroutine on the bot's event loop
        try:
            # Use bot.loop which is the actual loop the bot is running on
            target_loop = bot.loop if bot and bot.loop else self._loop
            if not target_loop:
                return False, "No event loop available"
            future = asyncio.run_coroutine_threadsafe(send_msg(), target_loop)
        except RuntimeError as e:
            if "loop is closed" in str(e):
                return False, "Bot event loop is closed"
            return False, f"Failed to schedule message: {e}"
        except Exception as schedule_err:
            return False, f"Failed to schedule message: {schedule_err}"
        
        try:
            # Wait for result with timeout
            success, result = future.result(timeout=10)
            return success, result
        except asyncio.TimeoutError:
            return False, "Timeout waiting for Discord response (10s)"
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Discord future.result error: {e}\n{error_details}")
            return False, f"Error getting result: {e}"
    
    def is_running(self):
        return self.running and self.thread.is_alive() if self.thread else False

bot_manager = DiscordBotManager()

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        token = sys.argv[1]
        bot_manager.start(token)
    else:
        print("Usage: python discord_bot.py <bot_token>")
