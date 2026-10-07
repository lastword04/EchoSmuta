from uuid import UUID
from typing import Protocol
from typing_extensions import Self
import logging
from shared.schemas.users import (
    UserCreateSchema,
    UserReadSchema,
    UserLoginSchema,
    PasswordSchema,
)
from shared.enums import UserRole
from ....core.utils.exceptions import PermissionDeniedError
from ..schemas import UserCreateDBSchema, UserAdditionalInformationCreateSchema
from ..repositories.users import UserRepositoryProtocol
from ..repositories.users_info import UserAdditionalInfoRepositoryProtocol
from ..services.passwords import PasswordServiceProtocol

logger = logging.getLogger(__name__)


class UserServiceProtocol(Protocol):
    async def create(self: Self, user_data: UserCreateSchema) -> UserReadSchema: ...

    async def authenticate_user(
        self: Self, user: UserLoginSchema
    ) -> UserReadSchema: ...

    async def get(self: Self, user_id: UUID) -> UserReadSchema: ...

    async def delete(self: Self, user_id: UUID) -> None: ...

    async def get_by_email(self: Self, email: str) -> UserReadSchema:
        """
        Retrieves a user by their email address.

        :param email: The email address of the user to retrieve.
        :return: UserReadSchema containing user information.
        """
        ...

    async def change_password(
        self: Self, record_id: UUID, password: PasswordSchema
    ) -> UserReadSchema: ...


class UserService(UserServiceProtocol):
    def __init__(
        self,
        user_repository: UserRepositoryProtocol,
        password_service: PasswordServiceProtocol,
        user_additional_info_repository: UserAdditionalInfoRepositoryProtocol,
    ) -> None:

        self.user_repository = user_repository
        self.password_service = password_service
        self.user_additional_info_repository = user_additional_info_repository
        logger.info("UserService initialized")

    async def create(self, user_data: UserCreateSchema) -> UserReadSchema:
        try:
            logger.info(f"Creating user with email: {user_data.email}")

            hashed_password = self.password_service.get_password_hash(
                user_data.password
            )
            logger.debug("Password hashed successfully")

            user_create = UserCreateDBSchema(
                **user_data.model_dump(exclude={"password", "source_of_knowledge"}),
                password=hashed_password,
                role=UserRole.USER,
            )

            created_user = await self.user_repository.create(user_create)
            logger.info(f"User created successfully with id: {created_user.id}")

            if user_data.source_of_knowledge:
                logger.info("Creating additional user information")
                user_info = UserAdditionalInformationCreateSchema(
                    user_id=created_user.id,
                    source_of_knowledge=user_data.source_of_knowledge,
                )
                await self.user_additional_info_repository.create(user_info)
                logger.debug("Additional user information created successfully")

            return UserReadSchema(**created_user.model_dump(exclude={"password"}))

        except Exception as e:
            logger.error(f"Error creating user: {str(e)}", exc_info=True)
            raise

    async def authenticate_user(self, user: UserLoginSchema) -> UserReadSchema:
        try:
            logger.info(f"Authenticating user with id: {user.user_id}")

            db_user = await self.user_repository.get(user.user_id)
            logger.debug("User found in database")

            if not self.password_service.verify_password(
                user.password, db_user.password
            ):
                logger.warning(f"Authentication failed for user id: {user.user_id}")
                raise PermissionDeniedError()

            logger.info(f"User authenticated successfully: {user.user_id}")
            return UserReadSchema(**db_user.model_dump(exclude={"password"}))

        except PermissionDeniedError:
            logger.warning(f"Permission denied for user id: {user.user_id}")
            raise
        except Exception as e:
            logger.error(f"Error during user authentication: {str(e)}", exc_info=True)
            raise

    async def get(self, user_id: UUID) -> UserReadSchema:
        try:
            logger.info(f"Getting user with id: {user_id}")

            user = await self.user_repository.get(user_id)
            logger.debug(f"User found: {user_id}")

            result = UserReadSchema(**user.model_dump(exclude={"password"}))
            logger.info(f"User data retrieved successfully: {user_id}")

            return result

        except Exception as e:
            logger.error(f"Error getting user {user_id}: {str(e)}", exc_info=True)
            raise

    async def delete(self, user_id: UUID) -> None:
        try:
            logger.info(f"Deleting user with id: {user_id}")

            await self.user_repository.delete(user_id)
            logger.info(f"User deleted successfully: {user_id}")

        except Exception as e:
            logger.error(f"Error deleting user {user_id}: {str(e)}", exc_info=True)
            raise

    async def get_by_email(self, email: str) -> UserReadSchema:
        """
        Retrieves a user by their email address.

        :param email: The email address of the user to retrieve.
        :return: UserReadSchema containing user information.
        """
        try:
            logger.info(f"Retrieving user by email: {email}")

            user = await self.user_repository.get_by_email(email)
            logger.debug(f"User found with email: {email}")

            return UserReadSchema(**user.model_dump(exclude={"password"}))

        except Exception as e:
            logger.error(
                f"Error retrieving user by email {email}: {str(e)}", exc_info=True
            )
            raise

    async def change_password(
        self: Self, record_id: UUID, password: PasswordSchema
    ) -> UserReadSchema:
        try:
            logger.info(f"Changing password for user with id: {record_id}")
            hashed_password = self.password_service.get_password_hash(password.password)
            logger.debug("Password hashed successfully")
            user = await self.user_repository.change_password(
                record_id, PasswordSchema(password=hashed_password)
            )
            logger.info(f"Password changed successfully for user: {record_id}")
            return UserReadSchema(**user.model_dump(exclude={"password"}))
        except Exception as e:
            logger.error(
                f"Error changing password for user {record_id}: {str(e)}", exc_info=True
            )
            raise
