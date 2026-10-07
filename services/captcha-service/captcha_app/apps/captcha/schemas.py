from pydantic import BaseModel, Field

class GeneratedCaptcha(BaseModel):
    """
    Schema for the generated captcha details.
    """
    text: str = Field(..., description="Text contained in the captcha image")
    image_bytes: bytes = Field(..., description="Image data in bytes format")
    base64_image: str = Field(..., description="Base64 encoded string of the captcha image")
    data_url: str = Field(..., description="Data URL for embedding the captcha image in HTML")


