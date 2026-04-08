"""API Chat - Chat with Ollama using HTTP API (supports streaming and tools)."""
import threading
import json
import requests
import sys
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

from Tools import TOOL_DEFINITIONS as TOOLS, execute_tool as _execute_tool

OLLAMA_API = "http://localhost:11434/api/chat"

TOOLS_UNSUPPORTED_MODELS = set()


def _send_chat_request(model_name, messages, tools=None, stream=False):
    payload = {
        "model": model_name,
        "messages": messages,
        "stream": stream
    }
    if tools:
        payload["tools"] = tools

    resp = requests.post(OLLAMA_API, json=payload, timeout=120)
    resp.raise_for_status()
    return resp.json(), tools is not None


def send_chat_request(model_name, messages, stream=False):

    payload = {
        "model": model_name,
        "messages": messages,
        "stream": stream
    }

    resp = requests.post(OLLAMA_API, json=payload, timeout=120)
    resp.raise_for_status()
    return resp.json()


def chat_with_api(model_name, messages, on_response, on_error, on_stream=None, on_tool_call=None, filtered_tools=None, agent_config=None):

    def run():
        model_supports_tools = model_name not in TOOLS_UNSUPPORTED_MODELS
        if filtered_tools is not None:
            tools_to_use = filtered_tools if model_supports_tools else None
        else:
            tools_to_use = TOOLS if model_supports_tools else None

        try:
            while True:
                try:
                    data, used_tools = _send_chat_request(model_name, messages, tools_to_use)
                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 400 and tools_to_use:
                        TOOLS_UNSUPPORTED_MODELS.add(model_name)
                        data, used_tools = _send_chat_request(model_name, messages, tools=None)
                        on_response(f"[Model {model_name} doesn't support tools. Using plain chat.]\n\n", messages)
                    else:
                        raise

                msg = data.get("message", {})

                if used_tools:
                    tool_calls = msg.get("tool_calls")
                    if tool_calls:
                        messages.append(msg)
                        for call in tool_calls:
                            fn = call.get("function", {})
                            name = fn.get("name")
                            args = fn.get("arguments", {})
                            if isinstance(args, str):
                                args = json.loads(args)

                            if on_tool_call:
                                on_tool_call(name, args)

                            result = _execute_tool(name, args)
                            messages.append({
                                "role": "tool",
                                "content": result
                            })
                        continue

                content = msg.get("content", "").strip()
                if content:
                    messages.append(msg)
                    on_response(content, messages)
                else:
                    on_error("No response received.")
                break

        except requests.exceptions.ConnectionError:
            on_error("Cannot connect to Ollama. Make sure it is running.")
        except Exception as e:
            on_error(str(e))

    threading.Thread(target=run, daemon=True).start()


def get_model_info(model_name):

    try:
        resp = requests.post(
            "http://localhost:11434/api/show",
            json={"name": model_name},
            timeout=5
        )
        if resp.status_code == 200:
            return resp.json()
    except:
        pass
    return None


def get_model_max_context(model_name):

    data = get_model_info(model_name)
    if data:
        model_info = data.get("model_info", {})
        
        for key in model_info.keys():
            if key.endswith(".context_length") or key == "context_length":
                return int(model_info[key])
        
        for key in ["max_position_embeddings", "n_ctx", "max_context"]:
            if key in model_info:
                return int(model_info[key])
        
        params = data.get("parameters", {})
        if "context_length" in params:
            return int(params["context_length"])
    
    return 2048
