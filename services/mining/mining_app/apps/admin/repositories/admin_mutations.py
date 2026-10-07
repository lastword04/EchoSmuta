import uuid

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import AdminLog


class AdminMutationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_log(
        self,
        admin_user_id: uuid.UUID,
        character_id: uuid.UUID,
        action: str,
        details: dict,
    ) -> AdminLog:
        async with self.session as session:
            log = AdminLog(
                admin_user_id=admin_user_id,
                character_id=character_id,
                action=action,
                details=details,
            )
            session.add(log)
            await session.commit()
            await session.refresh(log)
            return log

    async def list_logs(self, character_id: uuid.UUID | None, limit: int, offset: int) -> tuple[list[AdminLog], int]:
        filters = [AdminLog.character_id == character_id] if character_id else []
        statement = sa.select(AdminLog).where(*filters).order_by(AdminLog.created_at.desc()).offset(offset).limit(limit)
        count_statement = sa.select(sa.func.count()).select_from(AdminLog).where(*filters)
        async with self.session as session:
            logs = list((await session.scalars(statement)).all())
            count = await session.scalar(count_statement) or 0
            return logs, count
