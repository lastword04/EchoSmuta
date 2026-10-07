from pydantic import BaseModel, Field


class GeneratedCaptchaResponse(BaseModel):
    """
    Schema for the response after generating a captcha.
    """
    captcha_id: str = Field(..., description="Unique identifier for the generated captcha")
    image_url: str = Field(..., description="URL to access the generated captcha image")


class CaptchaVerificationRequest(BaseModel):
    """
    Schema for the request to verify a captcha.
    """
    captcha_id: str = Field(..., description="Unique identifier of the captcha to verify")
    user_input: str = Field(..., description="Text input provided by the user for verification")