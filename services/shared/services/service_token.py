import jwt
import datetime
from typing import Protocol
from typing_extensions import Self


class ServiceTokenGeneratorProtocol(Protocol):
    def generate(self: Self) -> str: ...


class ServiceTokenGenerator(ServiceTokenGeneratorProtocol):
    def __init__(self: Self, secret_key: str, algorithm: str, service_name: str, expire_minutes: int = 60) -> None:
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.service_name = service_name
        self.expire_minutes = expire_minutes

    def generate(self: Self) -> str:
        now = datetime.datetime.now(datetime.timezone.utc)
        payload = {
            "sub": self.service_name,
            "service": self.service_name,
            "iat": int(now.timestamp()),
            "exp": int((now + datetime.timedelta(minutes=self.expire_minutes)).timestamp())
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
