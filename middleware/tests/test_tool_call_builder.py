"""
Test untuk Modul D: build_tool_call_response()
Pastikan pytest dijalankan dari root middleware:
cd /home/farhan/Proyek/Hermes/middleware
pytest tests/test_tool_call_builder.py -v
"""
import pytest
import json
from app.tool_call_builder import build_tool_call_response, build_tool_call_object

def test_build_tool_call_response_default_id():
    """Test pembuatan response dengan ID yang digenerate otomatis."""
    tool_name = "write_file"
    arguments = {"path": "hello.py", "content": "print('Halo')"}
    
    response = build_tool_call_response(tool_name, arguments)
    
    # Validasi struktur dasar pesan assistant OpenAI
    assert response["object"] == "chat.completion"
    assert response["model"] == "deepseek-manual"
    assert len(response["choices"]) == 1
    assert response["choices"][0]["finish_reason"] == "tool_calls"
    
    message = response["choices"][0]["message"]
    assert message["role"] == "assistant"
    assert message["content"] is None
    assert len(message["tool_calls"]) == 1
    
    tool_call = message["tool_calls"][0]
    assert tool_call["id"].startswith("call_")
    assert tool_call["type"] == "function"
    assert tool_call["function"]["name"] == tool_name
    
    # Pastikan arguments adalah string JSON yang valid dan bisa di-parse kembali
    parsed_args = json.loads(tool_call["function"]["arguments"])
    assert parsed_args == arguments

def test_build_tool_call_response_custom_id():
    """Test pembuatan response dengan tool_call_id yang diberikan secara manual."""
    tool_name = "read_file"
    arguments = {"path": "config.yaml"}
    custom_id = "call_custom123456"
    
    response = build_tool_call_response(tool_name, arguments, tool_call_id=custom_id)
    
    tool_call = response["choices"][0]["message"]["tool_calls"][0]
    assert tool_call["id"] == custom_id
    assert tool_call["function"]["name"] == tool_name

def test_build_tool_call_response_empty_arguments():
    """Test pembuatan response dengan argumen kosong."""
    tool_name = "get_current_time"
    arguments = {}
    
    response = build_tool_call_response(tool_name, arguments)
    
    tool_call = response["choices"][0]["message"]["tool_calls"][0]
    parsed_args = json.loads(tool_call["function"]["arguments"])
    assert parsed_args == {}

def test_build_tool_call_response_unicode_arguments():
    """Test pembuatan response dengan argumen yang mengandung karakter unicode/emoji."""
    tool_name = "send_message"
    arguments = {"text": "Halo, apa kabar? 🚀"}
    
    response = build_tool_call_response(tool_name, arguments)
    
    tool_call = response["choices"][0]["message"]["tool_calls"][0]
    # Pastikan emoji tidak di-escape menjadi \ud83d\ude80
    assert "🚀" in tool_call["function"]["arguments"]
    parsed_args = json.loads(tool_call["function"]["arguments"])
    assert parsed_args == arguments

def test_build_tool_call_object():
    """Test pembuatan objek tool call tunggal tanpa wrapper pesan."""
    tool_name = "execute_code"
    arguments = {"code": "print('hello')"}
    
    obj = build_tool_call_object(tool_name, arguments)
    
    assert obj["type"] == "function"
    assert obj["function"]["name"] == tool_name
    parsed_args = json.loads(obj["function"]["arguments"])
    assert parsed_args == arguments