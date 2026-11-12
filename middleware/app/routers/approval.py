"""
Modul E: Approval Router untuk Hermes Manual Bridge.
Menyediakan endpoint untuk validasi path dan mendapatkan informasi sumber path.
Endpoint ini digunakan oleh Web UI untuk validasi sebelum approve tool call.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from ..path_extractor import extract_and_validate_path, validate_path
from ..detect_path_source import get_source_info

router = APIRouter(prefix="/approval", tags=["approval"])


class ValidatePathRequest(BaseModel):
    """Request body untuk validasi path."""
    path: str


class ValidatePathResponse(BaseModel):
    """Response body untuk validasi path."""
    is_valid: bool
    error_message: Optional[str] = None
    source: Optional[str] = None
    source_info: Optional[dict] = None


class PathInfoRequest(BaseModel):
    """Request body untuk mendapatkan informasi path dari prompt."""
    prompt: str


class PathInfoResponse(BaseModel):
    """Response body untuk informasi path."""
    path: Optional[str] = None
    source: str
    source_info: dict
    validation_error: Optional[str] = None


@router.post("/validate-path", response_model=ValidatePathResponse)
async def validate_path_endpoint(request: ValidatePathRequest):
    """
    Validasi path file untuk keamanan.
    Digunakan oleh Web UI sebelum approve tool call.
    
    Args:
        request: Path yang akan divalidasi
    
    Returns:
        Status validasi dan pesan error jika ada
    """
    is_valid, error_message = validate_path(request.path)
    
    return ValidatePathResponse(
        is_valid=is_valid,
        error_message=error_message if not is_valid else None
    )


@router.post("/path-info", response_model=PathInfoResponse)
async def get_path_info(request: PathInfoRequest):
    """
    Ekstrak informasi path dari prompt Hermes.
    Mengembalikan path, sumber path, dan info untuk UI.
    
    Args:
        request: Prompt dari Hermes Agent
    
    Returns:
        Informasi path lengkap untuk ditampilkan di UI
    """
    if not request.prompt:
        return PathInfoResponse(
            path=None,
            source="manual",
            source_info=get_source_info("manual"),
            validation_error=None
        )
    
    path, source, validation_error = extract_and_validate_path(request.prompt)
    
    return PathInfoResponse(
        path=path,
        source=source,
        source_info=get_source_info(source),
        validation_error=validation_error if validation_error else None
    )


@router.get("/source-info/{source}")
async def get_source_info_endpoint(source: str):
    """
    Dapatkan informasi tampilan untuk sumber path tertentu.
    
    Args:
        source: 'explicit' | 'natural_language' | 'manual'
    
    Returns:
        Dict dengan description, icon, dan color
    """
    valid_sources = ["explicit", "natural_language", "manual"]
    if source not in valid_sources:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid source. Must be one of: {', '.join(valid_sources)}"
        )
    
    return get_source_info(source)