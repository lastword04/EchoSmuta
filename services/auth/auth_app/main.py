
# === ГЛОБАЛЬНЫЙ ЩИТ ОТ ПРОКСИ v2 (Python Isolation) ===
import os
for _proxy_key in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY', 'all_proxy']:
    os.environ.pop(_proxy_key, None)

# Блокируем чтение прокси из реестра Windows (Internet Options)
import urllib.request
urllib.request.getproxies = lambda: {}
# ======================================================

import granian
from .bootstrap import create_app
from granian.utils.proxies import wrap_asgi_with_proxy_headers
from .settings import settings
import os, sys
print("🔥 ALL PROXY VARS:", {k: v for k, v in os.environ.items() if "proxy" in k.lower()})
sys.stdout.flush()

app = create_app()

app = wrap_asgi_with_proxy_headers(
    app,
    trusted_hosts=settings.trusted_hosts
)

if __name__ == "__main__":
    granian.Granian(
        "auth_app.main:app",  # путь к приложению в формате module:variable
        address="::",
        port=8080,
        reload=True,
        interface="asgi"  # или "wsgi", если вы используете WSGI
    ).serve()