from fastapi import status
from typing import Any
from shared.exceptions import CoreException

class FileUploadError(CoreException):
    """
    Ошибка, если файл не загружен.
    """
    def __init__(
        self,
        filename: str,
        headers: dict[str, str] | None = None,
        extras: dict[str, Any] | None = None
    ) -> None:
        detail = f'File {filename} not upload.'
        
        # Подготовка дополнительных данных
        extras_data = extras or {}
        extras_data["filename"] = filename
        
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            error_code="FILE_NOT_UPLOAD",
            error_type="FileNotUpload",
            extras=extras_data,
            headers=headers
        )
        self.filename = filename