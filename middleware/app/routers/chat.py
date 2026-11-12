"""
Router untuk Chat Completions API (Modul A) + Fallback Mode (Fase 3).

KEAMANAN & FALLBACK (Fase 3):
- Mendukung mode fallback: jika parsing gagal, kirim sebagai teks biasa
- Endpoint /submit_response menerima parameter is_fallback untuk mode teks biasa
- Audit trail: simpan original_prompt dan edited_prompt untuk tracking

Version: 1.1.0 (Keamanan & Fallback)
"""
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from ..models import ChatCompletionRequest
from ..state import state
from ..history import history_service
import uuid
import time


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
    
    MENDUKUNG 2 MODE (Fase 3 - Keamanan & Fallback):
    1. Mode Tool Call (default): kirim sebagai tool call write_file
    2. Mode Fallback/Teks Biasa: kirim sebagai teks biasa (jika parsing gagal)
    
    Request body:
    {
        "response": "jawaban DeepSeek",
        "edited_prompt": "prompt hasil edit user (opsional)",
        "is_tool_call": true/false,  # BARU: flag untuk mode tool call
        "tool_call": {               # BARU: data tool call (jika is_tool_call=true)
            "file_path": "path/ke/file.ext",
            "path_source": "explicit|natural_language|manual",
            "language": "python",
            "content": "isi kode"
        },
        "is_fallback": true/false    # BARU: flag untuk mode fallback
    }
    """
    body = await request.json()
    user_response = body.get("response", "")
    
    # Prompt yang benar-benar dikirim ke DeepSeek (bisa hasil edit user)
    edited_prompt = body.get("edited_prompt")
    
    # Flag untuk mode tool call vs fallback
    is_tool_call = body.get("is_tool_call", False)
    is_fallback = body.get("is_fallback", False)
    tool_call_data = body.get("tool_call")
    
    # Tentukan prompt final yang akan disimpan ke history
    final_prompt = edited_prompt if edited_prompt else state.current_prompt
    original = state.original_prompt
    
    # Simpan ke history dengan informasi lengkap
    if final_prompt:
        history_service.save_conversation(
            prompt=final_prompt,
            response=user_response,
            model="deepseek-manual",
            status="fallback" if is_fallback else "completed",
            original_prompt=original
        )
    
    # ============================================================
    # MODE 1: FALLBACK / TEKS BIASA
    # ============================================================
    # Jika parsing gagal atau user pilih fallback, kirim sebagai teks biasa
    if is_fallback or not is_tool_call:
        state.final_response = {
            "id": f"chatcmpl-manual-{uuid.uuid4().hex[:8]}",
            "object": "chat.completion",
            "created": int(time.time()),
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
        print("[Submit] Mode: FALLBACK (teks biasa)")
    
    # ============================================================
    # MODE 2: TOOL CALL (write_file)
    # ============================================================
    # Jika user approve tool call, bungkus ke format OpenAI tool call
    elif is_tool_call and tool_call_data:
        from ..tool_call_builder import build_tool_call_response
        
        # Bangun argumen untuk tool call
        arguments = {
            "path": tool_call_data.get("file_path"),
            "content": tool_call_data.get("content"),
        }
        
        # Bangun tool call response
        state.final_response = build_tool_call_response(
            tool_name="write_file",
            arguments=arguments,
        )
        
        print(f"[Submit] Mode: TOOL CALL (write_file -> {tool_call_data.get('file_path')})")
    
    # ============================================================
    # MODE 3: TEKS BIASA (default, backward compatibility)
    # ============================================================
    else:
        state.final_response = {
            "id": f"chatcmpl-manual-{uuid.uuid4().hex[:8]}",
            "object": "chat.completion",
            "created": int(time.time()),
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
        print("[Submit] Mode: TEKS BIASA (default)")
    
    # Lepaskan kunci asyncio.Event
    state.response_event.set()
    
    return {
        "status": "submitted",
        "message": "Respons dikirim ke Hermes",
        "mode": "fallback" if is_fallback else ("tool_call" if is_tool_call else "text")
    }