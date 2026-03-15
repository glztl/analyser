import os
import uuid
import shutil
import aiofiles  # ✅ 确保导入 aiofiles
from pathlib import Path
from fastapi import UploadFile, HTTPException
from app.core.config import settings


class FileService:
    """
    文件服务类
    处理文件上传、验证、存储和清理
    """

    @staticmethod
    def validate_file(file: UploadFile) -> None:
        """
        验证文件类型和大小
        """
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件类型：{file_ext}。允许的类型：{settings.ALLOWED_EXTENSIONS}",
            )

    @staticmethod
    async def save_file(file: UploadFile, user_id: str = "default") -> str:
        """
        保存文件并返回存储路径（字符串格式）
        """
        # 1. 验证文件
        FileService.validate_file(file)

        # 2. 生成唯一文件名
        file_ext = Path(file.filename).suffix.lower()
        unique_filename = f"{uuid.uuid4().hex}{file_ext}"

        # 3. 创建用户目录 (按用户隔离文件)
        user_dir = Path(settings.UPLOAD_DIR) / user_id
        user_dir.mkdir(parents=True, exist_ok=True)

        # 4. 构建完整文件路径
        file_path: Path = user_dir / unique_filename

        # 5. 异步保存文件
        try:
            content = await file.read()

            # 检查文件大小
            if len(content) > settings.MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=400,
                    detail=f"文件大小超过限制 ({settings.MAX_FILE_SIZE} bytes)",
                )

            
            async with aiofiles.open(file_path, "wb") as out_file:
                await out_file.write(content)

            
            return str(file_path)

        except HTTPException:
            # 重新抛出 HTTP 异常
            raise
        except Exception as e:
            # 其他异常转为 HTTP 500
            raise HTTPException(status_code=500, detail=f"文件保存失败：{str(e)}")

    @staticmethod
    def get_file_path(file_id: str, user_id: str = "default") -> Path:
        """
        根据文件 ID 获取文件路径 (Path 对象)
        """
        return Path(settings.UPLOAD_DIR) / user_id / file_id

    @staticmethod
    def delete_file(file_path: str) -> None:
        """
        删除文件
        """
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
        except Exception as e:
            # 记录日志但不抛出异常
            print(f"! 删除文件失败：{e}")
