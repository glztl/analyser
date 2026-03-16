from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from app.services.file_service import FileService
from pydantic import BaseModel
from pathlib import Path

router = APIRouter(prefix="/files", tags=["Files"])


class FileUploadResponse(BaseModel):
    file_id: str
    filename: str
    file_path: str
    size: int


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """
    上传数据文件
    """
    # 检查文件大小
    file_size = 0
    content = await file.read()
    file_size = len(content)

    if file_size > 10 * 1024 * 1024:  # 10MB
        raise HTTPException(status_code=400, detail="文件大小超过 10MB 限制")

    # 重置文件指针
    await file.seek(0)
    # 保存文件
    file_path = await FileService.save_file(file, user_id="default")

    # 提取文件 ID (文件名部分)
    file_id = Path(file_path).name

    return FileUploadResponse(
        file_id=file_id,
        filename=file.filename or "unknown",
        file_path=file_path,
        size=file_size
    )
