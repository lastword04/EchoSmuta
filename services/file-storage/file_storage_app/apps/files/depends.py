import redis.asyncio as redis
from fastapi import Depends
from ...core.db import AsyncSession, get_async_session
from ...core.clients.s3_client import S3ClientFactory
from ...core.redis import get_redis_client
from ...settings import Settings, get_settings
from .repositories.files import FileRepositoryProtocol, FileRepository
from .repositories.files_cache import FileRedisRepositoryProtocol, FileRedisRepository
from .services.file_service import FileServiceProtocol, S3FileService
from .services.file_managment_service import FileManagmentServiceProtocol, FileManagmentService, \
    DefaultTemplateFilesGeneratorProtocol, DefaultTemplateFilesGenerator
from .use_cases.create import CreateFileUseCaseProtocol, CreateFileUseCase
from .use_cases.delete import DeleteFileUseCaseProtocol, DeleteFileUseCase
from .use_cases.get import GetFileUseCaseProtocol, GetFileUseCase
from .use_cases.get_by_template import GetByTemplateFileUseCaseProtocol, GetByTemplateFileUseCase
from .use_cases.initialize_template_files import CreateIfNotExistFilesUseCaseProtocol, CreateIfNotExistFilesUseCase
from .use_cases.create_batch import CreateBatchFileUseCaseProtocol, CreateBatchFileUseCase
from .use_cases.get_by_ids import GetIdsFileUseCaseProtocol, GetIdsFileUseCase
from .use_cases.create_by_service import CreateFileByServiceUseCaseProtocol, CreateFileByServiceUseCase

def __get_file_repository(session: AsyncSession = Depends(get_async_session)
                          ) -> FileRepositoryProtocol:
    return FileRepository(session)

def get_s3_client(settings: Settings = Depends(get_settings)) -> S3ClientFactory:
    return S3ClientFactory(
        endpoint_url=settings.minio.endpoint,
        aws_access_key_id=settings.minio.access_key,
        aws_secret_access_key=settings.minio.secret_key
    )


def get_file_cache_repository(redis_client: redis.Redis = Depends(get_redis_client)) -> FileRedisRepositoryProtocol:
    """
    Provides a repository for file caching.
    
    :param redis_client: Redis client for caching.
    :return: FileRepository instance configured for caching.
    """
    return FileRedisRepository(redis_client=redis_client)

def get_file_service(client: S3ClientFactory = Depends(get_s3_client),
                     settings: Settings = Depends(get_settings)
                     ) -> FileServiceProtocol:
    return S3FileService(client_factory=client,
                         bucket_name=settings.minio.bucket_name,
                         real_url=settings.minio.real_url,
                         url_to_change=settings.minio.url_to_change)


def get_file_managment_service(file_repository: FileRepositoryProtocol = Depends(__get_file_repository),
                               file_cache_repository: FileRedisRepositoryProtocol = Depends(get_file_cache_repository),
                               file_service: FileServiceProtocol = Depends(get_file_service),
                                settings: Settings = Depends(get_settings)
                               ) -> FileManagmentServiceProtocol:
    return FileManagmentService(file_repository, file_cache_repository, file_service, settings.minio.standart_path, settings.redis_ttl)


def get_default_generator_files_service(file_managment_service: FileManagmentServiceProtocol = Depends(get_file_managment_service),
                                        settings: Settings = Depends(get_settings)
                                        ) -> DefaultTemplateFilesGeneratorProtocol:
    return DefaultTemplateFilesGenerator(file_managment_service, settings.template_file_dir)

def get_file_create_use_case(file_managment_service: FileManagmentServiceProtocol = Depends(get_file_managment_service)
                             ) -> CreateFileUseCaseProtocol:
    return CreateFileUseCase(file_managment_service)


def get_file_delete_use_case(file_managment_service: FileManagmentServiceProtocol = Depends(get_file_managment_service)
                             ) -> DeleteFileUseCaseProtocol:
    return DeleteFileUseCase(file_managment_service)


def get_file_get_use_case(file_managment_service: FileManagmentServiceProtocol = Depends(get_file_managment_service)
                             ) -> GetFileUseCaseProtocol:
    return GetFileUseCase(file_managment_service)


def get_file_get_by_template_use_case(file_managment_service: FileManagmentServiceProtocol = Depends(get_file_managment_service)
                             ) -> GetByTemplateFileUseCaseProtocol:
    return GetByTemplateFileUseCase(file_managment_service)

def get_file_create_batch_use_case(file_managment_service: FileManagmentServiceProtocol = Depends(get_file_managment_service)
                                ) -> CreateBatchFileUseCaseProtocol:
    return CreateBatchFileUseCase(file_managment_service)

def get_file_get_by_ids_use_case(file_managment_service: FileManagmentServiceProtocol = Depends(get_file_managment_service)
                                ) -> GetIdsFileUseCaseProtocol:
    return GetIdsFileUseCase(file_managment_service)

def get_file_create_if_not_exist_use_case(session: AsyncSession) -> CreateIfNotExistFilesUseCaseProtocol:
    repo = __get_file_repository(session)
    settings = get_settings()
    s3_client = get_s3_client(settings)
    redis_client = get_redis_client()
    file_cache_repo = get_file_cache_repository(redis_client)
    file_service = get_file_service(s3_client, settings)
    file_manager = get_file_managment_service(repo, file_cache_repo, file_service, settings)
    file_generator = get_default_generator_files_service(file_manager, settings)
    return CreateIfNotExistFilesUseCase(file_generator)

def get_create_file_by_service_use_case(file_managment_service: FileManagmentServiceProtocol = Depends(get_file_managment_service)
                             ) -> CreateFileByServiceUseCaseProtocol:
    return CreateFileByServiceUseCase(file_managment_service)