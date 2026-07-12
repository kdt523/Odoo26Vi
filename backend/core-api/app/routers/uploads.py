"""
app/routers/uploads.py — File/document upload service.

Endpoints:
  POST /uploads       — Upload a new file (returns file_id and url)
  GET  /uploads/{id}  — Securely download/view an uploaded file
"""

import os
import uuid
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import require_authenticated
from app.db import get_db
from app.models.employee import Employee
from app.models.upload import UploadRecord
from app.models.asset import Asset
from app.models.maintenance_request import MaintenanceRequest
from app.schemas.upload import UploadOut

router = APIRouter(prefix="/uploads", tags=["uploads"])

LOCAL_UPLOADS_DIR = "local_uploads"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "application/pdf"}

# Ensure the upload directory exists
os.makedirs(LOCAL_UPLOADS_DIR, exist_ok=True)


@router.post("/", response_model=UploadOut, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    current_user: Employee = Depends(require_authenticated),
    db: AsyncSession = Depends(get_db)
):
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {file.content_type}. Allowed types: {', '.join(ALLOWED_CONTENT_TYPES)}"
        )
        
    content = await file.read()
    file_size = len(content)
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds the 10MB limit (size: {file_size} bytes)"
        )

    file_id = uuid.uuid4()
    file_extension = os.path.splitext(file.filename)[1] if file.filename else ""
    local_filename = f"{file_id}{file_extension}"
    file_path = os.path.join(LOCAL_UPLOADS_DIR, local_filename)

    with open(file_path, "wb") as out_file:
        out_file.write(content)
        
    upload_record = UploadRecord(
        id=file_id,
        original_filename=file.filename or local_filename,
        content_type=file.content_type,
        size=file_size,
        uploaded_by=current_user.id
    )
    
    db.add(upload_record)
    await db.commit()
    await db.refresh(upload_record)
    
    return {
        "file_id": upload_record.id,
        "filename": upload_record.original_filename,
        "url": f"/uploads/{upload_record.id}"
    }


@router.get("/{file_id}", response_class=FileResponse)
async def get_uploaded_file(
    file_id: uuid.UUID,
    current_user: Employee = Depends(require_authenticated),
    db: AsyncSession = Depends(get_db)
):
    upload_record = await db.get(UploadRecord, file_id)
    if not upload_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
        
    # Auth-gating logic:
    # 1. Uploader can always see their own file (e.g. before linking)
    if upload_record.uploaded_by == current_user.id:
        return _serve_file(upload_record)
        
    file_id_str = str(file_id)
    
    # 2. Check if file is linked to any Asset (Assets are generally viewable by auth users)
    asset_stmt = select(Asset).where((Asset.photo_ref == file_id_str) | (Asset.document_ref == file_id_str)).limit(1)
    asset_res = await db.execute(asset_stmt)
    if asset_res.scalar_one_or_none():
        return _serve_file(upload_record)
        
    # 3. Check if file is linked to any MaintenanceRequest
    # (MRs viewable by Admin, AssetManager, DepartmentHead, or the raiser)
    mr_stmt = select(MaintenanceRequest).where(MaintenanceRequest.photo_ref == file_id_str).limit(1)
    mr_res = await db.execute(mr_stmt)
    mr = mr_res.scalar_one_or_none()
    
    if mr:
        if current_user.role in ["Admin", "AssetManager", "DepartmentHead"] or mr.raised_by == current_user.id:
            return _serve_file(upload_record)
            
    # If we got here, the user is not authorized to view the file
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this file")


def _serve_file(upload_record: UploadRecord) -> FileResponse:
    # Find the local file path by checking extensions or storing the exact path
    # Since we didn't store the exact local path (we could have, but let's reconstruct it)
    # The file could be saved with an extension. We'll glob or check standard extensions.
    file_id_str = str(upload_record.id)
    file_extension = os.path.splitext(upload_record.original_filename)[1] if upload_record.original_filename else ""
    local_filename = f"{file_id_str}{file_extension}"
    file_path = os.path.join(LOCAL_UPLOADS_DIR, local_filename)
    
    if not os.path.exists(file_path):
        # Fallback if extension logic was different or missing
        # We can scan the directory for the file_id prefix
        found = False
        for f in os.listdir(LOCAL_UPLOADS_DIR):
            if f.startswith(file_id_str):
                file_path = os.path.join(LOCAL_UPLOADS_DIR, f)
                found = True
                break
        if not found:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File exists in DB but missing on disk")
            
    return FileResponse(
        path=file_path,
        media_type=upload_record.content_type,
        filename=upload_record.original_filename
    )
