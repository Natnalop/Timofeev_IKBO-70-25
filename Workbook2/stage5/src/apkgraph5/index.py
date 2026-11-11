"""Чтение APKINDEX и ограниченная распаковка подписанных индексов."""

import gzip
import io
import re
import tarfile
from urllib.request import urlopen

from .models import (
    FIELD_PREFIX_SIZE,
    FIELD_SEPARATOR_INDEX,
    MAX_BYTES,
    NETWORK_TIMEOUT,
    AppError,
    Package,
)
from .repository import Repository


def parse_record(record):
    """Разобрать поля одной записи APKINDEX без сторонних библиотек."""
    fields = {}
    for line in record.splitlines():
        if len(line) < FIELD_PREFIX_SIZE:
            raise AppError("Поврежден APKINDEX: ожидается поле X:значение")
        if line[FIELD_SEPARATOR_INDEX] != ":":
            raise AppError("Поврежден APKINDEX: ожидается поле X:значение")
        fields[line[0]] = line[FIELD_PREFIX_SIZE:]
    if not fields.get("P") or not fields.get("V"):
        raise AppError("APKINDEX: отсутствует P или V")
    return Package(
        fields["P"],
        fields["V"],
        tuple(fields.get("D", "").split()),
        tuple(fields.get("p", "").split()),
    )


def parse_index(text):
    """Построить репозиторий из текстовых записей APKINDEX."""
    records = re.split(r"\n\s*\n", text.strip())
    return Repository(parse_record(record) for record in records)


def check_size(size, description):
    """Отклонить архив или индекс, превышающий допустимый размер."""
    if size > MAX_BYTES:
        raise AppError(f"{description} превышает 32 МиБ")


def extract_index(blob):
    """Прочитать APKINDEX из склеенных gzip-потоков подписанного архива."""
    with gzip.GzipFile(fileobj=io.BytesIO(blob)) as zipped:
        unpacked = zipped.read(MAX_BYTES + 1)
    check_size(len(unpacked), "Распакованный архив APKINDEX")
    with tarfile.open(
        fileobj=io.BytesIO(unpacked), mode="r:", ignore_zeros=True
    ) as archive:
        for member in archive:
            if member.name == "APKINDEX" and member.isfile():
                check_size(member.size, "APKINDEX")
                return archive.extractfile(member).read().decode("utf-8")
    raise AppError("В архиве отсутствует APKINDEX")


def download_index(repository, fetcher=urlopen):
    """Загрузить индекс с ограничением размера и тайм-аутом запроса."""
    url = repository.rstrip("/")
    if not url.endswith("APKINDEX.tar.gz"):
        url += "/APKINDEX.tar.gz"
    try:
        with fetcher(url, timeout=NETWORK_TIMEOUT) as response:
            blob = response.read(MAX_BYTES + 1)
        check_size(len(blob), "Архив APKINDEX")
        return parse_index(extract_index(blob))
    except (OSError, tarfile.TarError, UnicodeError, EOFError) as exc:
        raise AppError(f"Ошибка чтения APKINDEX: {exc}") from exc
