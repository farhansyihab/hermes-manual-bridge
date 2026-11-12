"""
Modul D: Implementasi fungsi build_tool_call_response()
untuk membungkus hasil parsing tool name dan arguments
ke dalam format OpenAI tool call.
"""
import json
import uuid
from typing import Dict, Any, Optional

def build_tool_call_response(
    tool_name: str, 
    arguments: Dict[str, Any], 
    tool_call_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Membungkus nama tool dan argumen ke dalam format pesan OpenAI assistant message.
    
    Args:
        tool_name (str): Nama fungsi/tool yang akan dipanggil (misal: "write_file").
        arguments (dict): Argumen untuk tool tersebut dalam bentuk dictionary.
        tool_call_id (str, optional): ID unik untuk tool call. Jika None, akan digenerate otomatis.
        
    Returns:
        dict: Pesan dalam format OpenAI assistant message dengan tool_calls.
    """
    # Generate ID otomatis jika tidak diberikan
    if not tool_call_id:
        tool_call_id = f"call_{uuid.uuid4().hex[:24]}"
        
    # Pastikan arguments diubah menjadi string JSON yang valid
    # ensure_ascii=False digunakan agar karakter unicode (seperti emoji) tidak di-escape
    arguments_str = json.dumps(arguments, ensure_ascii=False)
    
    return {
        "id": f"chatcmpl-manual-{uuid.uuid4().hex[:8]}",
        "object": "chat.completion",
        "created": 1677652288,  # Bisa diganti dengan int(time.time()) jika diimpor
        "model": "deepseek-manual",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": tool_call_id,
                            "type": "function",
                            "function": {
                                "name": tool_name,
                                "arguments": arguments_str
                            }
                        }
                    ]
                },
                "finish_reason": "tool_calls"
            }
        ],
        "usage": {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }
    }

def build_tool_call_object(
    tool_name: str,
    arguments: Dict[str, Any],
    tool_call_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Membungkus nama tool dan argumen ke dalam format objek tool call tunggal.
    Berguna jika hanya membutuhkan objek tool call tanpa wrapper pesan assistant lengkap.
    """
    if not tool_call_id:
        tool_call_id = f"call_{uuid.uuid4().hex[:24]}"
        
    return {
        "id": tool_call_id,
        "type": "function",
        "function": {
            "name": tool_name,
            "arguments": json.dumps(arguments, ensure_ascii=False)
        }
    }