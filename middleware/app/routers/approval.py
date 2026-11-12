"""
Modul E: Approval Router untuk Hermes Manual Bridge.
Menyediakan endpoint untuk validasi path, whitelist check, dan mendapatkan
informasi sumber path.

KEAMANAN & FALLBACK (Fase 3):
- Endpoint /approval/check-whitelist: validasi path terhadap whitelist direktori
- Endpoint /approval/whitelist-info: dapatkan info whitelist untuk UI
- Validasi path mencakup: format, ekstensi, whitelist direktori

Endpoint ini digunakan oleh Web UI untuk validasi sebelum approve tool call.

Version: 1.1.0 (Keamanan & Fallback)
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from ..path_extractor import (
    extract_and_validate_path,
    validate_path,
    validate_path_against_whitelist,
    validate_file_content,
    get_whitelist_info,
)
from ..detect_path_source import get_source_info
from ..config import security_config


router = APIRouter(prefix="/approval", tags=["approval"])


# ============================================================
# REQUEST/RESPONSE MODELS
# ============================================================

class ValidatePathRequest(BaseModel):
    """Request body untuk validasi path."""
    path: str


class ValidatePathResponse(BaseModel):
    """Response body untuk validasi path."""
    is_valid: bool
    error_message: Optional[str] = None
    source: Optional[str] = None
    source_info: Optional[dict] = None
    whitelist_valid: Optional[bool] = None
    whitelist_error: Optional[str] = None


class PathInfoRequest(BaseModel):
    """Request body untuk mendapatkan informasi path dari prompt."""
    prompt: str


class PathInfoResponse(BaseModel):
    """Response body untuk informasi path."""
    path: Optional[str] = None
    source: str
    source_info: dict
    validation_error: Optional[str] = None
    whitelist_valid: Optional[bool] = None
    whitelist_error: Optional[str] = None
    warnings: List[str] = []


class CheckWhitelistRequest(BaseModel):
    """Request body untuk validasi whitelist."""
    path: str
    base_dir: Optional[str] = None


class CheckWhitelistResponse(BaseModel):
    """Response body untuk validasi whitelist."""
    is_valid: bool
    error_message: Optional[str] = None
    whitelisted_directories: List[str] = []


class ValidateContentRequest(BaseModel):
    """Request body untuk validasi isi file."""
    content: str


class ValidateContentResponse(BaseModel):
    """Response body untuk validasi isi file."""
    is_valid: bool
    error_message: Optional[str] = None
    size_bytes: int = 0
    size_lines: int = 0


# ============================================================
# ENDPOINTS
# ============================================================

@router.post("/validate-path", response_model=ValidatePathResponse)
async def validate_path_endpoint(request: ValidatePathRequest):
    """
    Validasi path file untuk keamanan (format + whitelist).
    Digunakan oleh Web UI sebelum approve tool call.
    
    Args:
        request: Path yang akan divalidasi
        
    Returns:
        Status validasi dan pesan error jika ada
    """
    # Validasi format dasar
    is_valid, error_message = validate_path(request.path)
    
    # Validasi whitelist
    whitelist_valid = None
    whitelist_error = None
    if is_valid:
        whitelist_valid, whitelist_error = validate_path_against_whitelist(request.path)
    
    return ValidatePathResponse(
        is_valid=is_valid,
        error_message=error_message if not is_valid else None,
        whitelist_valid=whitelist_valid,
        whitelist_error=whitelist_error if not whitelist_valid else None,
    )


@router.post("/path-info", response_model=PathInfoResponse)
async def get_path_info(request: PathInfoRequest):
    """
    Ekstrak informasi path dari prompt Hermes.
    Mengembalikan path, sumber path, info untuk UI, dan warnings.
    
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
            validation_error=None,
            whitelist_valid=None,
            whitelist_error=None,
            warnings=[],
        )
    
    path, source, validation_error, warnings = extract_and_validate_path(request.prompt)
    
    # Validasi whitelist jika path ditemukan
    whitelist_valid = None
    whitelist_error = None
    if path:
        whitelist_valid, whitelist_error = validate_path_against_whitelist(path)
        if not whitelist_valid and whitelist_error:
            warnings.append(whitelist_error)
    
    return PathInfoResponse(
        path=path,
        source=source,
        source_info=get_source_info(source),
        validation_error=validation_error if validation_error else None,
        whitelist_valid=whitelist_valid,
        whitelist_error=whitelist_error if not whitelist_valid else None,
        warnings=warnings,
    )


@router.post("/check-whitelist", response_model=CheckWhitelistResponse)
async def check_whitelist(request: CheckWhitelistRequest):
    """
    Validasi path terhadap whitelist direktori.
    
    Args:
        request: Path dan optional base_dir
        
    Returns:
        Status validasi whitelist
    """
    is_valid, error_message = validate_path_against_whitelist(
        request.path,
        request.base_dir
    )
    
    return CheckWhitelistResponse(
        is_valid=is_valid,
        error_message=error_message if not is_valid else None,
        whitelisted_directories=security_config.WHITELISTED_DIRECTORIES,
    )


@router.get("/whitelist-info")
async def get_whitelist_info_endpoint():
    """
    Dapatkan informasi whitelist untuk ditampilkan di UI.
    
    Returns:
        Dict dengan daftar direktori yang di-whitelist dan info lainnya
    """
    return get_whitelist_info()


@router.post("/validate-content", response_model=ValidateContentResponse)
async def validate_content_endpoint(request: ValidateContentRequest):
    """
    Validasi isi file (ukuran, jumlah baris).
    
    Args:
        request: Isi file yang akan divalidasi
        
    Returns:
        Status validasi dan info ukuran
    """
    is_valid, error_message = validate_file_content(request.content)
    
    size_bytes = len(request.content.encode("utf-8")) if request.content else 0
    size_lines = request.content.count("\n") + 1 if request.content else 0
    
    return ValidateContentResponse(
        is_valid=is_valid,
        error_message=error_message if not is_valid else None,
        size_bytes=size_bytes,
        size_lines=size_lines,
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