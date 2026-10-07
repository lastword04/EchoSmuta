import aiofiles
import asyncio
import uuid
import json
import hashlib
import logging
from fastapi import UploadFile
from typing import Optional, Protocol, List
from typing_extensions import Self
from pathlib import Path
from shared.schemas.files import (
    FileReadSchema, FilesListReadSchema, FileCreateSchema, FileIdsSchema
)
from ....core.utils.exceptions import FileNotFound
from ..schemas import (
    FileUpdateSchema,
    FileCreateDBSchema, FileUpdateDBSchema,
    FileReadDBSchema,
)
from ..repositories.files import FileRepositoryProtocol
from ..repositories.files_cache import FileRedisRepositoryProtocol
from ..exceptions import FileUploadError
from .file_service import FileServiceProtocol


logger = logging.getLogger(__name__)

class FileManagmentServiceProtocol(Protocol):
    async def create(self: Self, data: FileCreateSchema, file: UploadFile, user_id: uuid.UUID) -> FileReadSchema:
        ...

    async def create_from_content(self: Self, data: FileCreateSchema, content: bytes, filename: str, user_id: uuid.UUID, content_type: str = "application/octet-stream") -> FileReadSchema:
        ...

    async def update(self: Self, id: uuid.UUID, data: FileUpdateSchema, file: UploadFile) -> FileReadSchema:
        ...

    async def delete(self: Self, id: uuid.UUID, creator_user_id: uuid.UUID) -> bool:
        ...

    async def get(self: Self, id: uuid.UUID) -> FileReadSchema:
        ...
    
    async def get_by_template(self: Self, template: str) -> FileReadSchema:
        ...

    async def get_by_template_or_none(self: Self, template: str) -> FileReadSchema:
        ...

    async def create_batch(self: Self, data_list: list[FileCreateSchema], files: list[UploadFile], user_id: uuid.UUID) -> FilesListReadSchema:
        ...

    async def get_by_ids(self: Self, ids: FileIdsSchema) -> FilesListReadSchema:
        ...

class FileManagmentService(FileManagmentServiceProtocol):
    def __init__(self: Self, file_repository: FileRepositoryProtocol, 
                 file_repository_cache: FileRedisRepositoryProtocol,
                 file_service: FileServiceProtocol,
                 standart_path: str,
                 ttl: int = 30 * 60):
        self.file_repository = file_repository
        self.file_repository_cache = file_repository_cache  
        self.file_service = file_service
        self.standart_path = standart_path
        self.ttl = ttl

    async def create(self: Self, data: FileCreateSchema, file: UploadFile, user_id: uuid.UUID) -> FileReadSchema:
        # Читаем содержимое файла
        contents = await file.read()
        content_type = file.content_type or "application/octet-stream"
        
        # Делегируем работу методу create_from_content
        return await self.create_from_content(data, contents, file.filename, user_id, content_type)

    async def create_from_content(self: Self, data: FileCreateSchema, content: bytes, filename: str, user_id: uuid.UUID, content_type: str = "application/octet-stream") -> FileReadSchema:
        generated_id = uuid.uuid4()
        path = self._generate_photo_path(generated_id, data.subdir, filename)
        
        # Используем upload_content вместо upload
        is_upload = await self.file_service.upload_content(path, content, content_type)
        
        if not is_upload:
            raise FileUploadError(filename)
        
        file_for_create = FileCreateDBSchema(
            id=generated_id,
            filename=data.filename or filename,
            content_type=content_type,
            size=len(content),
            template_name=data.template_name,
            path=path,
            creator_user_id=user_id
        )

        created_file = await self.file_repository.create(file_for_create)
        uploaded_file_url = await self.get_file_url(created_file.path)

        # # Кэшируем URL файла
        # await self._cache_file_url(created_file.path, uploaded_file_url)
        # # Кэшируем сам файл
        # await self._cache_file_data(created_file.id, created_file)

        return FileReadSchema(
            **created_file.model_dump(exclude={"path"}),
            url=uploaded_file_url
        )
    
    async def create_batch(self: Self, data_list: list[FileCreateSchema], files: list[UploadFile], user_id: uuid.UUID) -> FilesListReadSchema:
        files_id = []
        files_to_upload: list[tuple[str, UploadFile]] = []
        
        for file, data in zip(files, data_list):
            generated_id = uuid.uuid4()
            files_id.append(generated_id)
            path = self._generate_photo_path(generated_id, data.subdir, file.filename)
            files_to_upload.append((path, file))
        
        upload_results = await self.file_service.upload_batch(files_to_upload)
        created_files = []

        for i, (is_uploaded, data) in enumerate(zip(upload_results, data_list)):
            if is_uploaded:
                # Берем данные напрямую из UploadFile
                upload_file = files_to_upload[i][1]  # UploadFile объект
                
                file_for_create = FileCreateDBSchema(
                    id=files_id[i],
                    template_name=data.template_name,
                    filename=upload_file.filename,  # Из UploadFile
                    content_type=upload_file.content_type or "application/octet-stream",  # Из UploadFile
                    size=upload_file.size,  # Из UploadFile
                    path=files_to_upload[i][0],
                    creator_user_id=user_id
                )
                created_file = await self.file_repository.create(file_for_create)
                uploaded_file_url = await self.get_file_url(created_file.path)
                
                # Кэшируем URL и данные файла
                # await self._cache_file_url(created_file.path, uploaded_file_url)
                # await self._cache_file_data(created_file.id, created_file)
                
                created_files.append(FileReadSchema(
                    **created_file.model_dump(exclude={"path"}),
                    url=uploaded_file_url
                ))
        
        return FilesListReadSchema(files=created_files)

    async def get_file_url(self: Self, path: str) -> str:
        # Проверяем кэш
        # cache_key = self._make_url_cache_key(path)
        # cached_url = await self.file_repository_cache.get(cache_key)
        
        # if cached_url:
        #     return cached_url
        
        # Если нет в кэше - генерируем новый URL
        url = await self.file_service.get_url(path)
        
        # Сохраняем в кэш на 25 минут (немного меньше срока действия presigned URL)
        # await self.file_repository_cache.set(cache_key, url, ttl=self.ttl)
        
        return url
    
    async def get(self: Self, id: uuid.UUID) -> FileReadSchema:
        # Проверяем кэш
        # cached_file = await self._get_cached_file_data(id)
        # if cached_file:
        #     # Получаем URL из кэша или генерируем новый
        #     url = await self.get_file_url(cached_file.path)
        #     return FileReadSchema(
        #         **cached_file.model_dump(exclude={"path"}),
        #         url=url
        #     )
        
        # Если нет в кэше - берем из БД
        db_file = await self.file_repository.get(id)
        
        # Кэшируем данные файла
        # await self._cache_file_data(id, db_file)
        
        url_file = await self.get_file_url(db_file.path) 
        return FileReadSchema(
            **db_file.model_dump(exclude={"path"}),
            url=url_file
        )
    
    async def get_by_template(self: Self, template: str) -> FileReadSchema:
        db_file = await self.get_by_template_or_none(template)

        if not db_file:
            raise FileNotFound(template)
        
        url_file = await self.get_file_url(db_file.path) 
        return FileReadSchema(
            **db_file.model_dump(exclude={"path"}),
            url=url_file
        )
    
    async def get_by_template_or_none(self: Self, template: str) -> FileReadDBSchema:
        return await self.file_repository.get_by_template(template)
    
    async def delete(self: Self, id: uuid.UUID, creator_user_id: uuid.UUID) -> bool:
        db_file = await self.file_repository.get(id)
        if db_file.creator_user_id != creator_user_id:
            raise FileNotFound(f"File with id {id} not found")
        
        is_deleted = await self.file_service.delete(db_file.path)
        if is_deleted:
            # Удаляем из кэша
            # await self._invalidate_file_cache(db_file.id, db_file.path)
            return await self.file_repository.delete(id)
        return is_deleted
    
    async def update(self: Self, id: uuid.UUID, data: FileUpdateSchema, file: UploadFile) -> FileReadSchema:
        db_file = await self.file_repository.get(id)
        is_upload = await self.file_service.upload(db_file.path, file)
        if not is_upload:
            raise FileUploadError()
        
        file_for_update = FileUpdateDBSchema(
            **data.model_dump(),
            id=db_file.id,
            path=db_file.path
        )
        updated_file = await self.file_repository.update(file_for_update)
        
        # Инвалидируем старый кэш и создаем новый
        # await self._invalidate_file_cache(updated_file.id, updated_file.path)
        # await self._cache_file_data(updated_file.id, updated_file)
        
        updated_file_url = await self.get_file_url(updated_file.path)
        return FileReadSchema(
            **updated_file.model_dump(exclude={"path"}),
            url=updated_file_url
        )

    async def get_by_ids(self: Self, ids: FileIdsSchema) -> FilesListReadSchema:
        if not ids.ids:
            logger.debug("Empty IDs list provided, returning empty result")
            return FilesListReadSchema(files=[])
        
        logger.info(f"Getting files by IDs, total count: {len(ids.ids)}")
        
        # Пытаемся получить файлы из кэша
        # logger.debug(f"Checking cache for {len(ids.ids)} files")
        # cached_files = await self._get_cached_files_data(ids.ids)
        # found_in_cache = {file.id: file for file in cached_files}
        # logger.debug(f"Found {len(cached_files)} files in cache")
        
        # Определяем, какие файлы нужно загрузить из БД
        # missing_ids = [id for id in ids.ids if id not in found_in_cache]
        # logger.debug(f"Missing files to load from DB: {len(missing_ids)}")
        
        # Параллельно загружаем недостающие файлы из БД
        db_files = []
        try:
            db_files = await self.file_repository.get_by_ids(ids.ids)
            logger.debug(f"Successfully loaded {len(db_files)} files from DB")
            
            # Параллельно кэшируем их
            # if db_files:
            #     logger.debug(f"Caching {len(db_files)} files")
            #     cache_tasks = [
            #         self._cache_file_data(db_file.id, db_file) 
            #         for db_file in db_files
            #     ]
            #     asyncio.create_task(self._safe_gather(cache_tasks))
            #     logger.debug("Started background caching task")
                
        except Exception as e:
            logger.error(f"Failed to load files from database: {e}", exc_info=True)
            # Продолжаем работу с тем, что есть в кэше
        
        # Собираем все файлы
        # all_files_data = list(found_in_cache.values()) + db_files
        all_files_data = db_files
        logger.debug(f"Total files to process: {len(all_files_data)} DB: {len(db_files)})")
        
        # Параллельно получаем URL для всех файлов
        logger.debug(f"Generating URLs for {len(all_files_data)} files")
        url_tasks = [self.get_file_url(db_file.path) for db_file in all_files_data]
        
        try:
            urls = await asyncio.gather(*url_tasks, return_exceptions=True)
            logger.debug("Successfully generated all URLs")
        except Exception as e:
            logger.error(f"Failed to generate URLs: {e}", exc_info=True)
            # В случае ошибки генерируем URL по одному
            urls = []
            for db_file in all_files_data:
                try:
                    url = await self.get_file_url(db_file.path)
                    urls.append(url)
                except Exception as url_error:
                    logger.error(f"Failed to generate URL for file {db_file.id}: {url_error}")
                    urls.append("")

        # Создаем результаты
        files_with_urls = []
        errors_count = 0
        
        for i, db_file in enumerate(all_files_data):
            try:
                url = urls[i] if i < len(urls) else ""
                
                if isinstance(url, Exception):
                    logger.warning(f"URL generation error for file {db_file.id}: {url}")
                    # В случае ошибки генерируем URL напрямую
                    url = await self.file_service.get_url(db_file.path)
                    errors_count += 1
                
                files_with_urls.append(FileReadSchema(
                    **db_file.model_dump(exclude={"path"}),
                    url=str(url)
                ))
                
            except Exception as e:
                logger.error(f"Failed to process file {db_file.id}: {e}", exc_info=True)
                errors_count += 1
                # Добавляем файл с пустым URL в случае ошибки
                files_with_urls.append(FileReadSchema(
                    **db_file.model_dump(exclude={"path"}),
                    url=""
                ))
        
        logger.info(f"Successfully processed {len(files_with_urls)} files, errors: {errors_count}")
        return FilesListReadSchema(files=files_with_urls)

    async def _safe_gather(self: Self, tasks: List) -> None:
        """Безопасное выполнение gather в фоне"""
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            # Логируем ошибки в фоновых задачах
            error_count = sum(1 for result in results if isinstance(result, Exception))
            if error_count > 0:
                logger.warning(f"Background caching completed with {error_count} errors")
        except Exception as e:
            logger.error(f"Background caching task failed: {e}", exc_info=True)

    def _generate_photo_path(self: Self, file_id: uuid.UUID, subdir: str, filename: Optional[str]) -> str:
        return f"{self.standart_path}/{subdir}/{file_id}{self._get_extension(filename)}"

    def _get_extension(self: Self, filename: Optional[str]) -> str:
        if not filename:
            return ".jpg"
        
        parts = filename.split('.')
        if len(parts) > 1:
            return f".{parts[-1].lower()}"
        return ".jpg"
    
    # Методы для работы с кэшем
    def _make_url_cache_key(self: Self, path: str) -> str:
        """Создает ключ для кэширования URL"""
        return f"url:{hashlib.md5(path.encode()).hexdigest()}"
    
    def _make_file_cache_key(self: Self, file_id: uuid.UUID) -> str:
        """Создает ключ для кэширования данных файла"""
        return f"file:{str(file_id)}"
    
    async def _cache_file_url(self: Self, path: str, url: str) -> None:
        """Кэширует URL файла"""
        cache_key = self._make_url_cache_key(path)
        await self.file_repository_cache.set(cache_key, url, ttl=self.ttl)  

    async def _cache_file_data(self: Self, file_id: uuid.UUID, file_data: FileReadDBSchema) -> None:
        """Кэширует данные файла"""
        cache_key = self._make_file_cache_key(file_id)
        # Сериализуем данные файла
        serialized_data = json.dumps(file_data.model_dump(), default=str)
        await self.file_repository_cache.set(cache_key, serialized_data, ttl=self.ttl)

    async def _get_cached_file_data(self: Self, file_id: uuid.UUID) -> Optional[FileReadDBSchema]:
        """Получает данные файла из кэша"""
        cache_key = self._make_file_cache_key(file_id)
        cached_data = await self.file_repository_cache.get(cache_key)
        
        if cached_data:
            try:
                data_dict = json.loads(cached_data)
                return FileReadDBSchema(**data_dict)
            except (json.JSONDecodeError, Exception):
                # Если не удалось десериализовать, удаляем из кэша
                await self.file_repository_cache.delete(cache_key)
                return None
        
        return None
    
    async def _get_cached_files_data(self: Self, file_ids: List[uuid.UUID]) -> List[FileReadDBSchema]:
        """Получает данные нескольких файлов из кэша"""
        cache_keys = [self._make_file_cache_key(file_id) for file_id in file_ids]
        cached_data_dict = await self.file_repository_cache.get_many(cache_keys)
        
        files_data = []
        valid_keys = []
        
        for key, cached_data in cached_data_dict.items():
            if cached_data:
                try:
                    data_dict = json.loads(cached_data)
                    file_data = FileReadDBSchema(**data_dict)
                    files_data.append(file_data)
                    valid_keys.append(key)
                except (json.JSONDecodeError, Exception):
                    # Удаляем недействительные записи из кэша
                    await self.file_repository_cache.delete(key)
        
        return files_data
    
    async def _invalidate_file_cache(self: Self, file_id: uuid.UUID, file_path: str) -> None:
        """Инвалидирует кэш файла"""
        # Удаляем данные файла из кэша
        file_cache_key = self._make_file_cache_key(file_id)
        await self.file_repository_cache.delete(file_cache_key)
        
        # Удаляем URL файла из кэша
        url_cache_key = self._make_url_cache_key(file_path)
        await self.file_repository_cache.delete(url_cache_key)
    

    
class DefaultTemplateFilesGeneratorProtocol(Protocol):

    async def create_template_files_if_not_exist(self: Self) -> list[FileReadSchema]:
        ...

    async def create_template_file_if_not_exist(self: Self, file_path: str) -> FileReadSchema:
        ...

class DefaultTemplateFilesGenerator(DefaultTemplateFilesGeneratorProtocol):

    def __init__(self: Self, file_manager: FileManagmentServiceProtocol, file_dir: str):
        self.file_manager = file_manager
        self.file_dir = file_dir

    async def create_template_files_if_not_exist(self: Self) -> list[FileReadSchema]:
        files_path = Path(self.file_dir)
        results = []
        for file_path in files_path.glob("*"):
            created_file = await self.create_template_file_if_not_exist(str(file_path))
            if created_file:
                results.append(created_file)

        return results

    async def create_template_file_if_not_exist(self: Self, file_path: str) -> Optional[FileReadSchema]:
        file_name = Path(file_path).stem  
        random_id = uuid.uuid4()
        
        file = await self.file_manager.get_by_template_or_none(file_name)
        if not file:
            async with aiofiles.open(file_path, "rb") as file:
                content_bytes = await file.read()
                file_name_with_extension = Path(file_path).name
                content_type = self._get_content_type(file_path)
                return await self.file_manager.create_from_content(
                    FileCreateSchema(template_name=file_name,
                                     filename=file_name_with_extension,
                                     content_type=content_type,
                                     size=len(content_bytes)),
                    content_bytes,
                    file_name_with_extension,
                    random_id,
                    content_type,
                )
        return None                             

    def _get_content_type(self, file_path: str) -> str:
        """Определяет content-type по расширению файла"""
        extension = Path(file_path).suffix.lower()
        content_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
            '.html': 'text/html',
            '.txt': 'text/plain',
        }
        return content_types.get(extension, 'application/octet-stream')



