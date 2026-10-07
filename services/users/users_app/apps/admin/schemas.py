from pydantic import BaseModel


class PermissionRequest(BaseModel):
    permission: str
