from typing import Protocol
from typing_extensions import Self
import logging
from jose import jwt, JWTError
from uuid import UUID
from datetime import datetime
from ..enums import UserRole
from ..exceptions import PermissionDeniedError
from ..schemas.auth import UserTokenDataReadSchema

logger = logging.getLogger(__name__)


class DecodeAccessTokenProtocol(Protocol):
    def decode_access_token(self: Self, token: str) -> UserTokenDataReadSchema:
        """
        Decodes an access token and returns the user token data.
        
        :param token: The access token to decode.
        :return: UserTokenDataReadSchema containing user information.
        """

class DecodeAccessTokenService(DecodeAccessTokenProtocol):
    def __init__(self, secret_key: str, algorithm: str):
        self.secret_key = secret_key
        self.algorithm = algorithm  
    
    def decode_access_token(self: Self, token: str) -> UserTokenDataReadSchema:
        
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm], options={"verify_aud": False})
            user_id_str = payload.get("user_id")
            character_id_str = payload.get("character_id")
            role = payload.get("role")
            exp = payload.get("exp")
            is_main = payload.get("is_main", False)

            if user_id_str is None:
                logger.error("Invalid token: missing user_id")
                raise PermissionDeniedError()
    
            try:
                user_id = UUID(user_id_str)
            except ValueError:
                logger.error("Invalid token: user_id not a valid UUID")
                raise PermissionDeniedError()

            try:
                character_id = UUID(character_id_str) if character_id_str else None # may be null if user not in game
            except ValueError:
                logger.error("Invalid token: character_id not a valid UUID")
                raise PermissionDeniedError()

            if exp is None:
                logger.error("Invalid token: missing expiration time")
                raise PermissionDeniedError()

            try:
                role_enum = UserRole(role)
            except ValueError:
                logger.error(f"Invalid token: unknown role {role}")
                raise PermissionDeniedError()

            token_data = UserTokenDataReadSchema(
                user_id=user_id,
                character_id=character_id,
                role=role_enum,
                is_main=is_main,
                expiration=datetime.fromtimestamp(exp)
            )           

            return token_data

        except JWTError:
            logger.warning("Failed to decode token", exc_info=True)
            raise PermissionDeniedError()
        
class DecodeTokenServiceProtocol(Protocol):
    def decode_service_token(self: Self, token: str, expected_audience: str) -> dict:
        """
        Decodes a service token and verifies its audience.
        
        :param token: The service token to decode.
        :param expected_audience: The expected audience for the token.
        :return: Decoded payload of the service token.
        """

class DecodeTokenService(DecodeTokenServiceProtocol):
    def __init__(self, secret_key: str, algorithm: str):
        self.secret_key = secret_key
        self.algorithm = algorithm

    def decode_service_token(self: Self, token: str, expected_audience: str) -> dict:
        """
        Decodes and verifies a service JWT.
        
        :param token: The token to verify.
        :param expected_audience: The expected audience (should match the aud in the token).
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                audience=expected_audience
            )
            return payload
        except JWTError:
            logger.error("Invalid service token: %s", token)
            raise PermissionDeniedError()


    

