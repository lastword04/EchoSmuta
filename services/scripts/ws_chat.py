import asyncio
import json
import signal
import sys

import aiohttp
import websockets


class UserSession:
    def __init__(self, name, password, session):
        self.name = name
        self.password = password
        self.session = session  # aiohttp.ClientSession
        self.character_id = None
        self.ws_token = None
        self.ws_url = None
        self.stop_event = asyncio.Event()

    async def login(self):
        login_url = "http://localhost:9090/api/auth/login"
        data = {
            "password": self.password,
            "name": self.name
        }
        try:
            async with self.session.post(login_url, json=data) as response:
                if response.status != 200:
                    print(f"[{self.name}] Ошибка входа: {response.status} - {await response.text()}")
                    return False
                resp_json = await response.json()
                self.character_id = resp_json.get('character', {}).get('id')
                if not self.character_id:
                    print(f"[{self.name}] Не удалось получить character_id")
                    return False
                return True
        except Exception as e:
            print(f"[{self.name}] Исключение при входе: {e}")
            return False

    async def play_character(self):
        url = f"http://localhost:9090/api/auth/characters/{self.character_id}/play"
        try:
            async with self.session.post(url) as response:
                if response.status != 200:
                    print(f"[{self.name}] Ошибка play: {response.status} - {await response.text()}")
                    return False
                return True
        except Exception as e:
            print(f"[{self.name}] Исключение при play: {e}")
            return False

    async def get_jwt_token(self):
        token_url = "http://localhost:9090/api/auth/token"
        try:
            async with self.session.get(token_url) as response:
                if response.status != 200:
                    print(f"[{self.name}] Ошибка получения токена: {response.status} - {await response.text()}")
                    return False
                resp_json = await response.json()
                self.ws_token = resp_json.get('token')
                if not self.ws_token:
                    print(f"[{self.name}] Не удалось получить JWT токен")
                    return False
                self.ws_url = f"ws://localhost:9097/api/messages/ws/chat/global?token={self.ws_token}"
                return True
        except Exception as e:
            print(f"[{self.name}] Исключение при получении токена: {e}")
            return False

    async def run_websocket(self, interval=10):
        if not self.ws_url:
            print(f"[{self.name}] Нет URL вебсокета для запуска.")
            return
        try:
            async with websockets.connect(self.ws_url) as websocket:
                print(f"[{self.name}] Подключен к вебсокету.")

                # --- Создаём задачи для отправки и приёма ---

                async def send_messages():
                    while not self.stop_event.is_set():
                        try:
                            message = {
                                "content": f"test from {self.name}",
                                "is_private": False,
                                "is_trade": False
                            }
                            await websocket.send(json.dumps(message))
                            print(f"[{self.name}] Отправлено: {message['content']}")
                            await asyncio.sleep(interval)  # Таймер *внутри* задачи отправки
                            if self.stop_event.is_set():
                                break
                        except websockets.exceptions.ConnectionClosed:
                            print(f"[{self.name}] Вебсокет отправки закрыт.")
                            break
                        except Exception as e:
                            print(f"[{self.name}] Ошибка вебсокета (отправка): {e}")
                            break

                async def listen_messages():
                    try:
                        async for msg in websocket:
                            # print(f"[{self.name}] Получено сообщение: {msg}")
                            # Игнорируем входящие сообщения, но *читаем* их, чтобы не заблокировать вебсокет
                            pass
                    except websockets.exceptions.ConnectionClosed:
                        print(f"[{self.name}] Вебсокет приёма закрыт.")
                    except Exception as e:
                        print(f"[{self.name}] Ошибка вебсокета (приём): {e}")

                # --- Запускаем обе задачи параллельно ---
                await asyncio.gather(
                    send_messages(),
                    listen_messages(),
                    # return_exceptions=True # Опционально: не останавливать другую задачу при ошибке одной
                )

        except Exception as e:
            print(f"[{self.name}] Ошибка подключения к вебсокету: {e}")


async def run_user_session(name, password, session):
    user = UserSession(name, password, session)
    if not await user.login():
        return
    if not await user.play_character():
        return
    if not await user.get_jwt_token():
        return
    await user.run_websocket(interval=10)


async def main():
    print("Запуск подключений пользователей...")

    # Создаём общую сессию для HTTP-запросов
    connector = aiohttp.TCPConnector(limit=20)  # ограничение на количество соединений
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = []
        for i in range(1, 21):
            name = f"clark{i}"
            password = "1"  # Учтите, что пароль был "1", а не "123456789" как в прошлом скрипте
            task = asyncio.create_task(run_user_session(name, password, session))
            tasks.append(task)

        def signal_handler():
            print("\nПолучен сигнал остановки. Завершаем...")
            for task in tasks:
                task.cancel()

        # Регистрируем обработчик сигнала для корректного завершения
        loop = asyncio.get_running_loop()
        loop.add_signal_handler(signal.SIGINT, signal_handler)

        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            print("\nПрервано пользователем.")
        finally:
            print("Все подключения завершены.")


if __name__ == "__main__":
    asyncio.run(main())