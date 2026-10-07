from typing import Protocol, Any
import json

class TextTemplateServiceProtocol(Protocol):
    def get_template(self, key: str, **kwargs) -> str: ...
    def get_template_by_path(self, path: list[str], **kwargs) -> str: ...
    def load_templates(self) -> None: ...
    def reload_templates(self) -> None: ... 


class TextTemplateService(TextTemplateServiceProtocol):
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.templates: dict[str, Any] = {}
        self.load_templates()

    def load_templates(self) -> None:
        with open(self.file_path, encoding="utf-8") as f:
            self.templates = json.load(f)

    def get_template(self, key: str, **kwargs) -> str:
        template = self.templates
        for k in key.split('_'):
            template = template[k]
        return template.format(**kwargs)

    def get_template_by_path(self, path: list[str], **kwargs) -> str:
        template = self.templates
        for key in path:
            template = template[key]
        return template.format(**kwargs)

    def reload_templates(self) -> None:
        self.load_templates()
