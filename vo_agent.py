import json
import base64
import asyncio
import random
import sys
from typing import Optional

import numpy as np
import aiohttp

# ==== Configuration ====
VOICE = "marina"
DEFAULT_CITY = "Москва"
SILENCE_THRESHOLD_MS = 500
MODEL_NAME = "speech-realtime-250923"
API_ENDPOINT = "wss://rest-assistant.api.cloud.yandex.net/v1/realtime/openai"
CONVERSATION_MODE = "default"


# Audio Configuration
IN_RATE = 44100
OUT_RATE = 44100
CHANNELS = 1
FRAME_MS = 500
IN_SAMPLES = int(IN_RATE * FRAME_MS / 1000)
OUT_BLOCK = int(OUT_RATE * 0.02)


# ======== Utility Functions ========
def float_to_pcm16(data: np.ndarray) -> bytes:
    """Convert float32 audio to PCM16 format."""
    data = np.clip(data, -1.0, 1.0)
    return (data * 32767).astype(np.int16).tobytes()


def b64_decode(s: str) -> bytes:
    """Decode base64 string to bytes."""
    return base64.b64decode(s)


def b64_encode(b: bytes) -> str:
    """Encode bytes to base64 string."""
    return base64.b64encode(b).decode("ascii")


def log(*args):
    """Thread-safe logging."""
    print(*args)
    sys.stdout.flush()


def fake_weather(city: str) -> str:
    """Generate fake weather data as JSON string.
    
    This is a placeholder function that simulates a weather API call.
    In a real implementation, this would call an actual weather service.
    """
    rng = random.Random(hash(city) & 0xFFFFFFFF)

    weather_data = {
        "city": city,
        "temperature_c": rng.randint(-10, 35),
        "condition": rng.choice(["ясно", "облачно", "дождь", "снег", "гроза", "туман"]),
        "wind_m_s": round(rng.uniform(0.5, 10.0), 1),
        "advice": rng.choice([
            "Возьми лёгкую куртку.",
            "Зонт пригодится.",
            "Пей воду и избегай солнца.",
            "На дорогах скользко — будь аккуратнее.",
            "Ветрено, капюшон не помешает.",
        ]),
    }

    return json.dumps(weather_data, ensure_ascii=False)
        

class RealTimeAgent:
    """A real-time voice agent that connects to Yandex Cloud API.
    
    This agent handles real-time audio streaming, WebSocket communication
    with Yandex Cloud's speech API, and function calling for weather information.
    
    Attributes:
        api_key (str): The API key for Yandex Cloud.
        folder_id (str): The folder ID for Yandex Cloud.
        running (bool): Whether the agent is running.
        realtime_api_url (str): The WebSocket URL for the Yandex Cloud API.
        authorization_header (dict): The authorization header for the API.
        ws: The WebSocket connection.
        session: The aiohttp session.
    """
    
    def __init__(self, api_key, folder_id):
        self.api_key = api_key
        self.folder_id = folder_id
        self.running = True
        
        # API Configuration
        self.realtime_api_url = (
            f"{API_ENDPOINT}"
            f"?model=gpt://{self.folder_id}/{MODEL_NAME}"
        )
        self.authorization_header = {"Authorization": f"api-key {self.api_key}"}
        
        # Initialize WebSocket connection
        self.ws = None
        self.session = None
    
    async def initialize_yandex_connection(self):
        """Initialize connection to Yandex Cloud API."""
        log(f"KEY: {self.api_key} FOLDER_ID:{self.folder_id}")
        self.session = aiohttp.ClientSession()
        
        self.ws = await self.session.ws_connect(self.realtime_api_url, headers=self.authorization_header, heartbeat=20.0)
        log("✅ Connected to Yandex Realtime API.")

        # Session configuration
        await self.ws.send_json({
            "type": "session.update",
            "session": {
                "instructions": (
                    "Ты ассистент по подбору товаров и ответы на вопросы интернет-магазина Яндекс Маркет. "
                    "Твоя задача - помогать пользователям находить товары и отвечать на их вопросы. "
                    "Если требуется поиск в интернете, искать надо только на сайте market.yandex.ru. "
                    "Если найден подходящий товар, предоставь ссылки на сайт. "
                    "Отвечай четко и по делу, избегай лишних слов. "
                    "Если не знаешь точного ответа, честно скажи об этом."
                    "Задавай не больше 3 уточняющих вопросов"
                ),
                "turn_detection": {"type": "server_vad", "silence_ms": SILENCE_THRESHOLD_MS},
                "input_audio_format": {
                    "type": "pcm16",
                    "sample_rate": IN_RATE,
                    "channels": CHANNELS
                },
                "output_audio_format": {
                    "type": "pcm16",
                    "sample_rate": OUT_RATE,
                    "channels": CHANNELS
                },
                "response": {
                    "modalities": ["audio", "text"],
                    "voice": VOICE
                },
                "tool_choice": {"type": "auto"},
                
                "tools": [
                    {
                        "type": "function",
                        "name": "web_search",  # зарезервированное имя функции веб-поиска
                        "description": "Поиск в интернете",
                        "parameters": {}  # временно не параметризуется
                    } #,
                    # {
                    #     "type": "function",
                    #     "name": "file_search",  # зарезервированное имя функции поиска по файлам
                    #     "description": "<идентификатор_поискового_индекса>",  # идентификатор индекса, созданного с помощью Vector stores API
                    #     "parameters": {}  # временно не используется
                    # },
                    # {
                    # "type": "mcp",  # указывает, что инструмент — MCP-сервер
                    # "server_label": "..",  # логическое имя сервера для модели
                    # "server_url": "...",  # адрес MCP-сервера со сторонними API
                    # "authorization": "{access_token}",  # данные для авторизации на MCP-сервере
                    # "require_approval": "{never или always}"  # политика подтверждения перед вызовом инструментов
                    # }
                ]
            }
        })
        
        return self.session
    
    async def send_audio_to_yandex(self, base64_audio_data):
        """Send audio data to Yandex Cloud API."""
        try:
            if self.running and self.ws:
                log(f"Sending audio data to Yandex Cloud API: {base64_audio_data}"[:100])
                # log(f"Raw data: ", b64_decode(base64_audio_data))
                
                realtime_audio_data_payload = {
                    "type": "input_audio_buffer.append",
                    "audio": base64_audio_data
                }
                
                await self.ws.send_json(realtime_audio_data_payload)
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            log("[Realtime api ws SEND ERROR]", e)
    
    
    async def handle_yandex_messages(self, client_ws):
        """Handle incoming messages from Yandex Cloud API."""
        session_id = None
        play_epoch = 0
        current_response_epoch = None

        if not self.ws:
            log("WebSocket connection not established")
            return

        async for msg in self.ws:
            if msg.type != aiohttp.WSMsgType.TEXT:
                continue


            message = json.loads(msg.data)
            msg_type = message.get("type")
            
            # log(f"received from yandex {msg_type}", msg_type)

            if msg_type not in {"input_audio_buffer.commit"}:
                log(f"### on_message: {msg_type}")
                
            if msg_type in {"input_audio_buffer.commit"}:
                log(f"### on_message commit: {msg_type}")            

            if msg_type == "session.created":
                session_id = (message.get("session") or {}).get("id")
                log(f"🪪 session.id = {session_id}")
                continue

            # User speech started - interrupt current response
            if msg_type == "input_audio_buffer.speech_started":
                play_epoch += 1
                current_response_epoch = None
                if client_ws:
                    log("websocket mode audio send ...")
                    try:
                        await client_ws.send_json({
                            "type": "user_speech_started"
                        })
                    except Exception as e:
                        log(f"Error sending speech_started notification to client: {e}")            
                continue

            # New assistant response started
            if msg_type == "response.created":
                current_response_epoch = play_epoch
                continue

            # Audio delta from assistant
            if msg_type == "response.output_audio.delta":
                if current_response_epoch == play_epoch:
                    # Send audio data to client WebSocket if provided
                    if client_ws:
                        log("websocket mode audio send ...")
                        try:
                            await client_ws.send_json({
                                "type": "audio",
                                "data": message["delta"]  # Already base64 encoded
                            })
                        except Exception as e:
                            log(f"Error sending audio to client: {e}")
                continue

            # Function call completed
            if msg_type == "response.output_item.done":
                item = message.get("item") or {}

                if item.get("type") == "function_call":
                    call_id = item.get("call_id")
                    args_text = item.get("arguments") or "{}"

                    try:
                        args = json.loads(args_text)
                    except Exception:
                        args = {}

                    city = (args.get("city") or DEFAULT_CITY).strip()
                    weather_json = fake_weather(city)

                    payload_item = {
                        "type": "conversation.item.create",
                        "item": {
                            "type": "function_call_output",
                            "call_id": call_id,
                            "output": weather_json
                        }
                    }

                    log("🧩 [FUNC] conversation.item.create(function_call_output):",
                        json.dumps(payload_item, ensure_ascii=False))
                    await self.ws.send_json(payload_item)

                    # Trigger assistant response
                    log("🧩 [ASSIST] sending response.create after tool output")
                    await self.ws.send_json({
                        "type": "response.create",
                        "response": {
                            "modalities": ["audio", "text"],
                            "conversation": CONVERSATION_MODE
                        }
                    })
                continue

            # Response completed
            if msg_type == "response.done":
                log("✅ Response completed")
                continue

            # Error handling
            if msg_type == "error":
                log("❌ SERVER ERROR:", json.dumps(message, ensure_ascii=False))
                continue

        log("WS closed")
        
    def is_connected(self):
        """Check if the WebSocket connection is active."""
        return self.ws is not None and not self.ws.closed

    async def stop(self):
        if self.ws:
            await self.ws.close()
        if self.session:
            await self.session.close()

    async def reconnect(self):
        """Reconnect to the Yandex Cloud API."""
        await self.stop()
        self.session = None
        self.ws = None
        return await self.initialize_yandex_connection()

    def set_running(self, state: bool):
        """Set the running state of the agent."""
        self.running = state

    def get_status(self):
        """Get the current status of the agent."""
        return {
            "running": self.running,
            "connected": self.is_connected(),
            "api_key": self.api_key[:5] + "..." if self.api_key else None,
            "folder_id": self.folder_id
        }

    async def update_instructions(self, new_instructions: str):
        """Update the agent's instructions."""
        if not self.ws:
            log("WebSocket connection not established")
            return
            
        await self.ws.send_json({
            "type": "session.update",
            "session": {
                "instructions": new_instructions
            }
        })

    async def clear_audio_buffer(self):
        """Clear the audio input buffer."""
        if not self.ws:
            log("WebSocket connection not established")
            return
            
        await self.ws.send_json({
            "type": "input_audio_buffer.clear"
        })

    async def commit_audio_buffer(self):
        """Commit the audio input buffer."""
        if not self.ws:
            log("WebSocket connection not established")
            return
            
        await self.ws.send_json({
            "type": "input_audio_buffer.commit"
        })

    async def interrupt_response(self):
        """Interrupt the current response."""
        if not self.ws:
            log("WebSocket connection not established")
            return
            
        await self.ws.send_json({
            "type": "response.cancel"
        })

    async def reset_conversation(self):
        """Reset the conversation history."""
        if not self.ws:
            log("WebSocket connection not established")
            return
            
        await self.ws.send_json({
            "type": "conversation.item.delete",
            "item_id": "all"
        })

    async def set_audio_output(self, enable: bool = True):
        """Enable or disable audio output."""
        if not self.ws:
            log("WebSocket connection not established")
            return
            
        modalities = ["text"]
        if enable:
            modalities.append("audio")
            
        await self.ws.send_json({
            "type": "session.update",
            "session": {
                "response": {
                    "modalities": modalities
                }
            }
        })

    async def set_temperature(self, temperature: float = 0.7):
        """Set the temperature for the model."""
        if not self.ws:
            log("WebSocket connection not established")
            return
            
        await self.ws.send_json({
            "type": "session.update",
            "session": {
                "temperature": temperature
            }
        })

    async def set_max_tokens(self, max_tokens: int = 1000):
        """Set the maximum tokens for the model."""
        if not self.ws:
            log("WebSocket connection not established")
            return
            
        await self.ws.send_json({
            "type": "session.update",
            "session": {
                "max_response_output_tokens": max_tokens
            }
        })

    async def set_frequency_penalty(self, penalty: float = 0.0):
        """Set the frequency penalty for the model."""
        if not self.ws:
            log("WebSocket connection not established")
            return
            
        await self.ws.send_json({
            "type": "session.update",
            "session": {
                "frequency_penalty": penalty
            }
        })

    async def set_presence_penalty(self, penalty: float = 0.0):
        """Set the presence penalty for the model."""
        if not self.ws:
            log("WebSocket connection not established")
            return
            
        await self.ws.send_json({
            "type": "session.update",
            "session": {
                "presence_penalty": penalty
            }
        })

    async def get_conversation_history(self):
        """Get the conversation history."""
        if not self.ws:
            log("WebSocket connection not established")
            return
            
        await self.ws.send_json({
            "type": "conversation.item.list"
        })

    async def set_turn_detection(self, silence_ms: int = SILENCE_THRESHOLD_MS):
        """Set the turn detection parameters."""
        if not self.ws:
            log("WebSocket connection not established")
            return
            
        await self.ws.send_json({
            "type": "session.update",
            "session": {
                "turn_detection": {
                    "type": "server_vad",
                    "silence_ms": silence_ms
                }
            }
        })
        
