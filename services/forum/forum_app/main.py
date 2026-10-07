
# === ГЛОБАЛЬНЫЙ ЩИТ ОТ ПРОКСИ v2 (Python Isolation) ===
import os
for _proxy_key in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY', 'all_proxy']:
    os.environ.pop(_proxy_key, None)

# Блокируем чтение прокси из реестра Windows (Internet Options)
import urllib.request
urllib.request.getproxies = lambda: {}
# ======================================================

import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import granian
from .bootstrap import create_app

app = create_app()

if __name__ == "__main__":
    granian.Granian(
        "forum_app.main:app", 
        address="::",
        port=8086,
        reload=True,
        interface="asgi"
    ).serve()