
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

app = create_app()

if __name__ == "__main__":
    granian.Granian(
        "captcha_app.main:app", 
        address="::",
        port=8089,
        reload=True,
        interface="asgi"
    ).serve()