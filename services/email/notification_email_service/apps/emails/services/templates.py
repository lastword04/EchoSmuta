from typing import Protocol
from typing_extensions import Self
import aiofiles
from jinja2 import Template
from ..schemas import PasswordTemplateSchema

class TemplateServiceProtocol(Protocol):

    async def render_template(self: Self, template_name: str, context: dict) -> str:
        ...


class TemplateService(TemplateServiceProtocol):

    def __init__(self: Self, template_dir: str = "templates"):
        self.template_dir = template_dir

    async def render_template(self: Self, template_name: str, **context) -> str:
        """Асинхронно читает и рендерит шаблон"""
        try:
            async with aiofiles.open(f"{self.template_dir}/{template_name}.html", "r", encoding="utf-8") as file:
                content = await file.read()
                template = Template(content)
                return template.render(**context)
        except FileNotFoundError:
            raise Exception(f"Template {template_name} not found")
        
    async def render_password_reset_template(self: Self, password_template: PasswordTemplateSchema) -> str:
        return await self.render_template("password_reset", **password_template.model_dump())
    

class PasswordTemplateServiceProtocol(TemplateServiceProtocol):
    
    async def render_password_reset_template(self: Self, password_template: PasswordTemplateSchema) -> str:
        ...

class PasswordTemplateService(TemplateService):

    def __init__(self: Self, template_dir: str = "templates", template_name: str = "password_reset"):
        super().__init__(template_dir)
        self.template_name = template_name

    async def render_password_reset_template(self: Self, password_template: PasswordTemplateSchema) -> str:
        return await self.render_template(self.template_name, **password_template.model_dump())