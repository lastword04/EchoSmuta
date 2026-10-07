import base64
import random
import string
from captcha.image import ImageCaptcha
from typing import Protocol
from ..schemas import GeneratedCaptcha

class CaptchaGeneratorProtocol(Protocol):
    """Протокол для генератора капчи"""
    
    def generate_captcha(self) -> GeneratedCaptcha:
        ...

class CaptchaGenerator(CaptchaGeneratorProtocol):
    """Простая и удобная обёртка для captcha"""

    def __init__(self, generator: ImageCaptcha):
    
            
        self.generator = generator

    def generate_captcha(self) -> GeneratedCaptcha:
        """
        Генерирует текстовую капчу
        
            
        Returns:
            GeneratedCaptcha
        """
        # Генерируем капчу
        text = self.generate_text()
        captcha = self.generator.generate(text)

        # Конвертируем в байты
        image_bytes = captcha.getvalue()
        
        # Конвертируем в base64 для веба
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        
        return GeneratedCaptcha(
            text=text,
            image_bytes=image_bytes,
            base64_image=base64_image,
            data_url=f"data:image/png;base64,{base64_image}"
        ) 



    def generate_text(self, chars: str = string.digits, length: int = 3) -> str:
        """
        Генерирует текст капчи из 3 случайных цифр

        Returns:
            str: Текст капчи
        """
        return ''.join(random.choices(chars, k=length))
    