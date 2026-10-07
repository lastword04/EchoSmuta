import logging
from typing import Protocol
import bcrypt

logger = logging.getLogger(__name__)

class PasswordServiceProtocol(Protocol):
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        ...
    
    def get_password_hash(self, password: str) -> str:
        ...


class PasswordService(PasswordServiceProtocol):

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        logger.info("Verifying password")
        password_bytes = plain_password.encode('utf-8')
        hashed_password_bytes = hashed_password.encode('utf-8')
        is_valid = bcrypt.checkpw(password_bytes, hashed_password_bytes)
        logger.info(f"Password verification {'succeeded' if is_valid else 'failed'}")
        return is_valid 
    
    def get_password_hash(self, password: str) -> str:
        logger.info("Generating password hash")
        pwd_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(pwd_bytes, salt)
        logger.info("Password hashed successfully")
        return hashed_password.decode('utf-8')

