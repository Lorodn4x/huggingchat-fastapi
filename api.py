import os
from dotenv import load_dotenv

load_dotenv()  # Это загрузит переменные из файла .env, если он существует

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, ValidationError
from typing import List, Optional, Union
from hugchat import hugchat
from hugchat.login import Login
import asyncio
import json
import time
import logging
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI()

# Добавление CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Message(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: Optional[str] = None
    messages: List[Message]
    stream: Optional[bool] = False
    max_tokens: Optional[int] = None
    temperature: Optional[float] = 1.0
    top_p: Optional[float] = 1.0
    n: Optional[int] = 1
    stop: Optional[Union[str, List[str]]] = None
    presence_penalty: Optional[float] = 0.0
    frequency_penalty: Optional[float] = 0.0
    logit_bias: Optional[dict] = None
    user: Optional[str] = None
    web_search: Optional[bool] = False

    class Config:
        extra = "allow"  # Позволяет принимать дополнительные поля

class HuggingChatManager:
    def __init__(self, default_model="meta-llama/Meta-Llama-3.1-70B-Instruct"):
        self.email = os.getenv("HUGGINGCHAT_EMAIL")
        self.password = os.getenv("HUGGINGCHAT_PASSWORD")
        cookie_path_dir = "./cookies/"
        self.sign = Login(self.email, self.password)
        self.cookies = self.sign.login(cookie_dir_path=cookie_path_dir, save_cookies=True)
        self.chatbot = None
        self.available_models = None
        self.current_model_index = 0
        self.default_model = default_model
        self.initialize_chatbot()

    def initialize_chatbot(self):
        if self.chatbot is None:
            self.chatbot = hugchat.ChatBot(cookies=self.cookies.get_dict())
            self.available_models = self.chatbot.get_available_llm_models()
            logger.info(f"Available models: {[model.id for model in self.available_models]}")
            self.switch_to_default_model()
            logger.info(f"Initial model: {self.get_current_model()}")

    def switch_to_default_model(self):
        if not self.switch_model(self.default_model):
            logger.warning(f"Failed to switch to default model {self.default_model}. Using the first available model.")
            self.switch_model(self.available_models[0].id)

    def get_chatbot(self):
        return self.chatbot

    def get_models(self):
        return self.available_models

    def switch_model(self, model_name):
        for i, model in enumerate(self.available_models):
            if model.id == model_name:
                logger.info(f"Switching to model: {model_name} (index: {i})")
                self.chatbot.switch_llm(i)
                self.current_model_index = i
                self.delete_current_conversation()
                self.ensure_conversation()
                logger.info(f"Current model after switch: {self.get_current_model()}")
                return True
        logger.warning(f"Model {model_name} not found")
        return False

    def get_current_model(self):
        return self.available_models[self.current_model_index].id

    def ensure_conversation(self):
        if not self.chatbot.current_conversation:
            logger.info("Creating new conversation")
            self.chatbot.new_conversation(switch_to=True)

    def delete_current_conversation(self):
        if self.chatbot.current_conversation:
            logger.info(f"Deleting conversation: {self.chatbot.current_conversation}")
            self.chatbot.delete_conversation(self.chatbot.current_conversation)
            self.chatbot.current_conversation = None
        else:
            logger.info("No current conversation to delete")

chat_manager = None

@app.on_event("startup")
async def startup_event():
    global chat_manager
    chat_manager = HuggingChatManager(default_model="meta-llama/Meta-Llama-3.1-70B-Instruct")

async def chat_stream(prompt: str, chatbot, request: ChatCompletionRequest):
    try:
        logger.info(f"Starting stream with model: {chat_manager.get_current_model()}")
        for response in chatbot.chat(prompt, web_search=request.web_search):
            chunk = {
                "id": f"chatcmpl-{int(time.time())}",
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": chat_manager.get_current_model(),
                "choices": [{
                    "delta": {"content": response},
                    "index": 0,
                    "finish_reason": None
                }]
            }
            yield f"data: {json.dumps(chunk)}\n\n"
            await asyncio.sleep(0)
    except Exception as e:
        logger.error(f"Error in chat_stream: {e}")
        yield f"data: {{\"error\": \"{str(e)}\"}}\n\n"
    finally:
        yield "data: [DONE]\n\n"

# Обработка ошибок валидации
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=400,
        content={"error": {"message": str(exc), "type": "invalid_request_error"}},
    )

# Обработка HTTP исключений
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"message": str(exc.detail), "type": "api_error"}},
    )

@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    try:
        body = await request.json()
        chat_request = ChatCompletionRequest(**body)
        
        if not chat_manager:
            raise HTTPException(status_code=500, detail="ChatBot manager not initialized")

        chatbot = chat_manager.get_chatbot()
        
        if chat_request.model:
            if not chat_manager.switch_model(chat_request.model):
                raise HTTPException(status_code=400, detail=f"Model {chat_request.model} not found")

        prompt = "\n".join([f"{msg.role}: {msg.content}" for msg in chat_request.messages])

        try:
            if chat_request.stream:
                return StreamingResponse(chat_stream(prompt, chatbot, chat_request), media_type="text/event-stream")
            else:
                message_result = chatbot.chat(prompt, web_search=chat_request.web_search)
                message = message_result.wait_until_done()
                
                response = {
                    "id": f"chatcmpl-{int(time.time())}",
                    "object": "chat.completion",
                    "created": int(time.time()),
                    "model": chat_manager.get_current_model(),
                    "choices": [{
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": message,
                        },
                        "finish_reason": "stop"
                    }],
                    "usage": {
                        "prompt_tokens": len(prompt.split()),
                        "completion_tokens": len(message.split()),
                        "total_tokens": len(prompt.split()) + len(message.split())
                    }
                }
                
                if chat_request.web_search:
                    response["web_search_sources"] = [
                        {"link": source.link, "title": source.title, "hostname": source.hostname}
                        for source in message_result.web_search_sources
                    ]
                
                return response
        finally:
            chat_manager.delete_current_conversation()

    except Exception as e:
        logger.error(f"Critical error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/v1/models")
async def get_models():
    if not chat_manager:
        raise HTTPException(status_code=500, detail="ChatBot manager not initialized")
    models = chat_manager.get_models()
    return {
        "object": "list",
        "data": [{"id": model.id, "object": "model", "created": int(time.time()), "owned_by": "huggingface"} for model in models],
    }

@app.get("/")
async def root():
    return {"message": "Welcome to the HuggingChat API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")