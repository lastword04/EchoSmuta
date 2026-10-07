from .schemas.base import CookieTokenSchema

access_token_schema = CookieTokenSchema(cookie_name="access_token")
refresh_token_schema = CookieTokenSchema(cookie_name="refresh_token")