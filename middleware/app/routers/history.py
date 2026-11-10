from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from ..history import history_service

router = APIRouter()

@router.get("/history")
async def get_history(limit: int = 50):
    """Ambil riwayat percakapan"""
    conversations = history_service.get_recent(limit)
    return {"conversations": conversations, "count": len(conversations)}

@router.get("/history/{conversation_id}")
async def get_conversation(conversation_id: int):
    """Ambil detail percakapan berdasarkan ID"""
    conv = history_service.get_by_id(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv

@router.delete("/history/{conversation_id}")
async def delete_conversation(conversation_id: int):
    """Hapus percakapan berdasarkan ID"""
    deleted = history_service.delete_by_id(conversation_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"status": "deleted", "id": conversation_id}

@router.delete("/history/clear")
async def clear_history():
    """Hapus semua riwayat percakapan"""
    count = history_service.clear_all()
    return {"status": "cleared", "count": count}

@router.get("/history/export/json")
async def export_history_json():
    """Export semua riwayat ke JSON"""
    import json
    json_str = history_service.export_to_json()
    return JSONResponse(content=json.loads(json_str))

@router.get("/history/stats")
async def get_history_stats():
    """Dapatkan statistik riwayat"""
    stats = history_service.get_stats()
    return stats