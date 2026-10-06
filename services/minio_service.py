import json
import uuid
from functools import lru_cache
from typing import BinaryIO

from fastapi import HTTPException
from minio import Minio

from core.config import settings

# Допустимые типы файлов и расширения для генерируемых имён (имена всегда на латинице)
ALLOWED_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "video/mp4": ".mp4",
    "video/webm": ".webm",
}


class MinioService:
    def __init__(self) -> None:
        self.bucket = settings.MINIO_BUCKET
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
        )
        self._bucket_ready = False

    def _ensure_bucket(self) -> None:
        """Создаёт бакет и открывает файлы на чтение, чтобы браузер мог их показывать."""
        if self._bucket_ready:
            return
        if not self.client.bucket_exists(self.bucket):
            self.client.make_bucket(self.bucket)
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": ["*"]},
                    "Action": ["s3:GetObject"],
                    "Resource": [f"arn:aws:s3:::{self.bucket}/*"],
                }
            ],
        }
        self.client.set_bucket_policy(self.bucket, json.dumps(policy))
        self._bucket_ready = True

    def upload(self, file: BinaryIO, content_type: str, expected: str) -> str:
        """Загружает файл в MinIO и возвращает сгенерированное имя (его кладём в БД).

        expected — 'image' или 'video': какого типа файл ждём в этом поле.
        """
        extension = ALLOWED_TYPES.get(content_type or "")
        if extension is None or not content_type.startswith(f"{expected}/"):
            raise HTTPException(
                status_code=400,
                detail=f"Ожидается файл типа {expected} ({', '.join(ALLOWED_TYPES)})",
            )

        file.seek(0, 2)
        size = file.tell()
        file.seek(0)
        if size == 0:
            raise HTTPException(status_code=400, detail="Файл пустой")

        self._ensure_bucket()
        name = f"{uuid.uuid4().hex}{extension}"
        self.client.put_object(
            self.bucket, name, file, length=size, content_type=content_type
        )
        return name

    def build_url(self, name: str | None) -> str | None:
        """Полный адрес файла для ответа клиенту. Старые записи с готовым URL отдаём как есть."""
        if not name:
            return None
        if name.startswith(("http", "/")):
            return name
        return f"{settings.MINIO_BASE_URL}/{self.bucket}/{name}"


@lru_cache(maxsize=1)
def get_minio_service() -> MinioService:
    return MinioService()
