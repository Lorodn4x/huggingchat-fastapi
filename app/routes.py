from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse
from .models import ChatCompletionRequest
from .chat_manager import HuggingChatManager
import asyncio
import json
import time
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

chat_manager = None

@router.on_event("startup")
async def startup_event():
    global chat_manager
    chat_manager = HuggingChatManager(default_model="meta-llama/Meta-Llama-3.1-70B-Instruct")

async def chat_stream(request: Request, chat_completion_request: ChatCompletionRequest):
    if not chat_manager:
        raise HTTPException(status_code=500, detail="Chat manager is not initialized")
    
    async for chunk in chat_manager.chat_stream(chat_completion_request):
        yield chunk

@router.get("/chat/stream")
async def chat_stream_route(request: Request, chat_completion_request: ChatCompletionRequest):
    return StreamingResponse(chat_stream(request, chat_completion_request), media_type="text/event-stream")

@router.post("/chat/completions")
async def chat_completions_route(chat_completion_request: ChatCompletionRequest):
    if not chat_manager:
        raise HTTPException(status_code=500, detail="Chat manager is not initialized")
    
    try:
        response = await chat_manager.chat_completions(chat_completion_request)
        return JSONResponse(content=response, media_type="application/json")
    except Exception as e:
        logger.error(f"Error in chat_completions: {e}")
        raise HTTPException(status_code=500, detail="Error in chat_completions")

@router.get("/models")
async def get_models_route():
    if not chat_manager:
        raise HTTPException(status_code=500, detail="Chat manager is not initialized")
    
    return JSONResponse(content=chat_manager.get_models(), media_type="application/json")

@router.get("/")
async def root():
    return JSONResponse(content={"message": "HuggingChat API"}, media_type="application/json")