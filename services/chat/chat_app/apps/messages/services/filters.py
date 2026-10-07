import re
from urllib.parse import urlparse
from typing import Protocol
from typing_extensions import Self


class FilterProtocol(Protocol):
    def filter_text(self: Self, text: str) -> str:
        ...

class FilterSmylies(FilterProtocol):
    def __init__(self: Self, max_smiles: int):
        self.max_smiles = max_smiles

    def filter_text(self: Self, text: str) -> str:
        pattern = r'\|\d+\|'
        matches = re.findall(pattern, text)
        
        if len(matches) <= self.max_smiles:
            return text  # если self.max_smiles или меньше — возвращаем как есть

        # Найдём первые нужные совпадения
        first = matches[:self.max_smiles]
        
        # Заменим первые нужные вхождения на временные токены, чтобы не тронуть их
        temp_text = text
        for i, match in enumerate(first):
            placeholder = f"__TEMP_PLACEHOLDER_{i}__"
            temp_text = temp_text.replace(match, placeholder, 1)

        # Удалим оставшиеся вхождения |число|
        temp_text = re.sub(pattern, '', temp_text)

        # Вернём обратно первые self.max_smiles
        result = temp_text
        for i, match in enumerate(first):
            placeholder = f"__TEMP_PLACEHOLDER_{i}__"
            result = result.replace(placeholder, match)

        return result
    

class FilterLinks(FilterProtocol):
    def __init__(self: Self, const_allowed_hosts: set, frontend_url: str):
        self.allowed_hosts = {urlparse(frontend_url).hostname, *const_allowed_hosts}

    def filter_text(self: Self, text: str) -> str:


        # Склеиваем только явные попытки обойти ссылки, а не обычные предложения.
        # То есть, только если вокруг точки нет заглавных букв и пробелов выглядят подозрительно.
        text_fixed = text

        # 1. Склеиваем "h t t p s : / /" и "w w w ."
        text_fixed = re.sub(
            r'(h\s*t\s*t\s*p\s*s?\s*:\s*/\s*/)',
            lambda m: m.group(1).replace(" ", ""),
            text_fixed,
            flags=re.IGNORECASE,
        )
        text_fixed = re.sub(
            r'(w\s*w\s*w\s*\.)',
            lambda m: m.group(1).replace(" ", ""),
            text_fixed,
            flags=re.IGNORECASE,
        )

        # 2. Склеиваем "twitch . ru", но не "спал. Потом"
        #   Условие: точка окружена буквами/цифрами без заглавных после точки.
        text_fixed = re.sub(
            r'(?<=[a-z0-9])\s*\.\s*(?=[a-z0-9])',
            '.',
            text_fixed,
            flags=re.IGNORECASE,
        )

        # 3. Основной шаблон ссылки
        url_pattern = re.compile(
            r"""
            (?:
                (?:https?|ftp):\/\/     # протокол
                | www\.                 # или www.
                | (?=\S+\.\S+)          # или просто domain.tld
            )
            [a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}   # основной домен
            (?:[^\s]*)                    # путь, параметры и т.д.
            """,
            re.VERBOSE | re.IGNORECASE,
        )

        censored_text = url_pattern.sub(self._replace_if_invalid, text_fixed)

        # 4. Чистим хвосты типа "https://[заблокированная ссылка]"
        censored_text = re.sub(
            r'\bhttps?:\s*/\s*/\s*\[заблокированная ссылка\]',
            '[заблокированная ссылка]',
            censored_text,
            flags=re.IGNORECASE,
        )

        return censored_text
    
    def _replace_if_invalid(self: Self, match: re.Match) -> str:
            url = match.group(0)
            parsed = urlparse(url if url.startswith(("http", "ftp")) else f"http://{url}")
            host = parsed.hostname
            if not host:
                return "[заблокированная ссылка]"
            host = host.lower()

            if any(host == allowed or host.endswith(f".{allowed}") for allowed in self.allowed_hosts if allowed):
                return url
            return "[заблокированная ссылка]"

