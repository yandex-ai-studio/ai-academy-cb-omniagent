from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn
import json
import base64
from typing import Optional
import asyncio
import sys
import os

from text_agent import TextAgent
from vo_agent import RealTimeAgent

app = FastAPI(title="Chat Support Bot API")

# Import the WebSocket audio handler from vo_agent.py
import asyncio

# CORS middleware для разрешения запросов с фронтенда
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory="static", html=True), name="static")

def log(*args):
    """Thread-safe logging."""
    print(*args)
    sys.stdout.flush()

# Модели данных
class ChatMessage(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    timestamp: Optional[str] = None
    

api_key = os.environ['API_KEY']
project = os.environ['PROJECT']
base_url='https://rest-assistant.api.cloud.yandex.net/v1'

agent = TextAgent(api_key=api_key, base_url=base_url, project=project)

# REST API endpoints

@app.get("/")
async def root():
    """Корневой endpoint"""
    return {
        "message": "Chat Support Bot API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "chat": "/chat (POST)",
            "websocket": "/ws"
        }
    }

@app.get("/health")
async def health_check():
    """Проверка состояния сервера"""
    return {
        "status": "healthy",
        "service": "chat-bot-api"
    }

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(message: ChatMessage):
    """
    REST API endpoint для текстовых сообщений.
    Принимает сообщение пользователя и возвращает ответ бота.
    """
    try:
        # Имитация задержки обработки (как будто бот "думает")
        await asyncio.sleep(0.5)
        
        # Генерируем ответ
        # bot_response = generate_bot_response(message.message)
        bot_response = agent.send(message.message)
        
        
        return ChatResponse(response=bot_response)
    
    except Exception as e:
        return ChatResponse(response=f"Извините, произошла ошибка: {str(e)}")

# WebSocket для голосового режима

class ConnectionManager:
    """Менеджер WebSocket соединений"""
    
    def __init__(self):
        self.active_connections: list[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"New WebSocket connection. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        print(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_message(self, message: dict, websocket: WebSocket):
        await websocket.send_text(json.dumps(message))

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint для голосового режима.
    Принимает аудио данные, обрабатывает их и отправляет ответ.
    """
    await manager.connect(websocket)
    
    
    try:
        # Initialize connection to Yandex Cloud API for this WebSocket connection
        realtime_agent = RealTimeAgent(api_key=api_key, folder_id=project)
        await realtime_agent.initialize_yandex_connection()
        receive_task_rta = asyncio.create_task(realtime_agent.handle_yandex_messages(websocket))

        f = open("incoming_audio.pcm", "ab")
        
        try:
            while True:
                # Получаем данные от клиента
                data = await websocket.receive_text()
                
                message_data = json.loads(data)
                # log(f"Received message from client: {message_data}")
                print('.', end='', flush=True)
                
                if message_data.get("type") == "audio":
                    # Получаем base64 аудио данные
                    audio_base64 = message_data.get("data")
                    f = open("incoming_audio.pcm", "ab")
                    try:
                        # Декодируем аудио
                        audio_bytes = base64.b64decode(audio_base64)
                        f.write(audio_bytes)

                        # Отправляем аудио данные в Yandex Cloud API через WebSocket audio handler
                        await realtime_agent.send_audio_to_yandex(audio_base64)
                        
                    except Exception as e:
                        await manager.send_message({
                            "type": "error",
                            "message": f"Ошибка обработки аудио: {str(e)}"
                        }, websocket)
                
                elif message_data.get("type") == "text":
                    # Обработка текстовых сообщений через WebSocket
                    text = message_data.get("text", "")
                    response = agent.send(text)
                    
                    await manager.send_message({
                        "type": "response",
                        "text": response
                    }, websocket)
        
        finally:
            # Cleanup when the WebSocket connection is closed
            await realtime_agent.stop()
            receive_task_rta.cancel()
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("Client disconnected")
    
    except Exception as e:
        print(f"WebSocket error: {str(e)}")
        manager.disconnect(websocket)

# Дополнительные endpoints для расширенной функциональности

@app.get("/stats")
async def get_stats():
    """Получить статистику активных соединений"""
    return {
        "active_websocket_connections": len(manager.active_connections),
        "server_status": "running"
    }

@app.post("/feedback")
async def submit_feedback(rating: int, comment: Optional[str] = None):
    """Endpoint для отправки обратной связи"""
    return {
        "status": "success",
        "message": "Спасибо за ваш отзыв!",
        "rating": rating,
        "comment": comment
    }

if __name__ == "__main__":
    print("=" * 50)
    print("🚀 Starting Chat Support Bot Server")
    print("=" * 50)
    print("📍 Server URL: http://0.0.0.0:8000")
    print("📍 API Docs: http://0.0.0.0:8000/docs")
    print("📍 WebSocket: ws://0.0.0.0:8000/ws")
    print("=" * 50)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )