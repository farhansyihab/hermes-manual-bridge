from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from ..models import ChatCompletionRequest
from ..state import state
from ..history import history_service

router = APIRouter()

@router.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    last_message = request.messages[-1].content
    state.current_prompt = last_message
    
    # Reset state untuk tugas baru
    state.response_event.clear()
    state.final_response = None
    state.is_waiting = True
    
    print(f"[Hermes Request] Prompt diterima: {last_message[:100]}...")
    
    # HOLD & WAIT
    try:
        await state.response_event.wait()
    except Exception as e:
        print(f"Error waiting for event: {e}")
    finally:
        state.is_waiting = False
        state.current_prompt = None
    
    return JSONResponse(content=state.final_response)

@router.get("/get_prompt")
async def get_prompt():
    if state.current_prompt:
        return {"prompt": state.current_prompt, "status": "waiting"}
    return {"prompt": None, "status": "idle"}

@router.post("/submit_response")
async def submit_response(request: Request):
    body = await request.json()
    user_response = body.get("response", "")
    
    # Simpan ke history
    if state.current_prompt:
        history_service.save_conversation(
            prompt=state.current_prompt,
            response=user_response,
            model="deepseek-manual"
        )
    
    # Bungkus ke format JSON standar OpenAI
    state.final_response = {
        "id": "chatcmpl-manual-123",
        "object": "chat.completion",
        "created": 1677652288,
        "model": "deepseek-manual",
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": user_response
            },
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }
    }
    
    # Lepaskan kunci asyncio.Event
    state.response_event.set()
    
    return {"status": "submitted", "message": "Respons dikirim ke Hermes"}