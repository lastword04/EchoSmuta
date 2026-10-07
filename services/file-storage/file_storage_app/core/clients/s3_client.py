import aioboto3
from typing import Optional
from typing_extensions import Self
from types_aiobotocore_s3 import S3Client


class S3ClientFactory:
    # Кэш на уровне КЛАССА: общий для всех экземпляров,
    # переживает пересоздание фабрики FastAPI на каждый запрос
    _clients: dict = {}

    def __init__(
        self: Self,
        endpoint_url: str,
        aws_access_key_id: str,
        aws_secret_access_key: str,
        region_name: str = "us-east-1"
    ):
        self._endpoint_url = endpoint_url
        self._aws_access_key_id = aws_access_key_id
        self._aws_secret_access_key = aws_secret_access_key
        self._region_name = region_name
        self._session = aioboto3.Session()

    async def get_client(self) -> S3Client:
        cache_key = (self._endpoint_url, self._aws_access_key_id, self._region_name)
        client = S3ClientFactory._clients.get(cache_key)

        if client is None:
            client = await self._session.client(
                "s3",
                endpoint_url=self._endpoint_url,
                aws_access_key_id=self._aws_access_key_id,
                aws_secret_access_key=self._aws_secret_access_key,
                region_name=self._region_name
            ).__aenter__()
            S3ClientFactory._clients[cache_key] = client

        return client