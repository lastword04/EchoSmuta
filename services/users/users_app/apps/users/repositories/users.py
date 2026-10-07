import uuid
import sqlalchemy as sa
from typing_extensions import Self
from shared.schemas.users import PasswordSchema
from ....core.repositories.base_repository import BaseRepositoryImpl
from ....core.utils.exceptions import (
    ModelFieldNotFoundException,
    ModelNotFoundException,
)
from ..models import User
from ..schemas import UserReadDBSchema, UserUpdateDBSchema, UserCreateDBSchema


class UserRepositoryProtocol(
    BaseRepositoryImpl[User, UserReadDBSchema, UserCreateDBSchema, UserUpdateDBSchema]
):
    async def get_by_email(self: Self, email: str) -> UserReadDBSchema:
        """
        Retrieves a user by their email address.

        :param email: The email address of the user.
        :return: UserReadDBSchema containing user information.
        """
        ...

    async def change_password(
        self: Self, record_id: uuid.UUID, password: PasswordSchema
    ) -> UserReadDBSchema: ...


class UserRepository(UserRepositoryProtocol):
    async def get_by_email(self: Self, email: str) -> UserReadDBSchema:
        """
        Retrieves a user by their email address.

        :param email: The email address of the user.
        :return: UserReadDBSchema containing user information.
        """
        async with self.session as session:
            stmt = sa.select(self.model_type).where(self.model_type.email == email)
            user = (await session.execute(stmt)).scalar_one_or_none()

            if user is None:
                return ModelFieldNotFoundException(self.model_type, "email", email)

            return self.read_schema_type.model_validate(user, from_attributes=True)

    async def change_password(
        self: Self, record_id: uuid.UUID, password: PasswordSchema
    ) -> UserReadDBSchema:
        async with self.session as session, session.begin():
            stmt = (
                sa.update(self.model_type)
                .where(self.model_type.id == record_id)
                .values(password.model_dump())
                .returning(self.model_type)
            )
            user = (await session.execute(stmt)).scalar_one_or_none()
            if user is None:
                raise ModelNotFoundException(self.model_type, record_id)

            return self.read_schema_type.model_validate(user, from_attributes=True)
