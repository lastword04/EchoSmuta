
# === ГЛОБАЛЬНЫЙ ЩИТ ОТ ПРОКСИ v2 (Python Isolation) ===
import os

for _proxy_key in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY', 'all_proxy']:
    os.environ.pop(_proxy_key, None)

# Блокируем чтение прокси из реестра Windows (Internet Options)
import urllib.request

urllib.request.getproxies = dict
# ======================================================

import granian

from .bootstrap import create_app

app = create_app()

if __name__ == "__main__":
    granian.Granian(
        "mining_app.main:app", 
        address="::",
        port=8088,
        reload=True,
        interface="asgi"  # или "wsgi", если вы используете WSGI
    ).serve()