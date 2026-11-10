from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from ..models import ChatCompletionRequest
from ..state import state
from ..history import history_service

router = APIRouter()


@router.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    """
    Endpoint yang dipanggil Hermes Agent.
    Menyimpan prompt asli & menunggu user submit jawaban via Web UI.
    """
    last_message = request.messages[-1].content

    # Simpan prompt ASLI dari Hermes (untuk audit trail)
    state.original_prompt = last_message
    # current_prompt awalnya sama dengan original; bisa diubah user via UI
    state.current_prompt = last_message

    # Reset state untuk tugas baru
    state.response_event.clear()
    state.final_response = None
    state.is_waiting = True

    print(f"[Hermes Request] Prompt diterima: {last_message[:100]}...")

    # HOLD & WAIT sampai user submit via Web UI
    try:
        await state.response_event.wait()
    except Exception as e:
        print(f"Error waiting for event: {e}")
    finally:
        state.is_waiting = False
        state.current_prompt = None
        state.original_prompt = None

    return JSONResponse(content=state.final_response)


@router.get("/get_prompt")
async def get_prompt():
    """
    Dipolling oleh Web UI setiap 2 detik.
    Mengembalikan prompt yang sedang menunggu jawaban.
    """
    if state.current_prompt:
        return {
            "prompt": state.current_prompt,
            "original_prompt": state.original_prompt,
            "status": "waiting"
        }
    return {"prompt": None, "original_prompt": None, "status": "idle"}


@router.post("/submit_response")
async def submit_response(request: Request):
    """
    Dipanggil Web UI saat user mengirim jawaban DeepSeek.
    Menerima optional 'edited_prompt' - prompt hasil edit user.
    """
    body = await request.json()
    user_response = body.get("response", "")
    # Prompt yang benar-benar dikirim ke DeepSeek (bisa hasil edit user)
    edited_prompt = body.get("edited_prompt")

    # Tentukan prompt final yang akan disimpan ke history:
    # - Jika user mengedit prompt, gunakan edited_prompt sebagai 'prompt'
    # - original_prompt tetap menyimpan versi asli dari Hermes
    final_prompt = edited_prompt if edited_prompt else state.current_prompt
    original = state.original_prompt

    # Simpan ke history dengan informasi lengkap
    if final_prompt:
        history_service.save_conversation(
            prompt=final_prompt,
            response=user_response,
            model="deepseek-manual",
            original_prompt=original
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