import asyncio, asyncpg
from users_app.settings import settings

async def main():
    dsn = settings.db.dsn.replace('+asyncpg', '').replace('+psycopg_async', '')
    conn = await asyncpg.connect(dsn)
    
    target_email = 'lastword04@yandex.ru'
    
    # 1. Сначала удаляем зависимые записи (чтобы не было ошибок внешних ключей)
    await conn.execute("DELETE FROM refresh_tokens WHERE user_id = (SELECT id FROM users WHERE email = $1)", target_email)
    await conn.execute("DELETE FROM auth_logs WHERE user_id = (SELECT id FROM users WHERE email = $1)", target_email)
    
    # 2. Удаляем самого пользователя
    result = await conn.execute("DELETE FROM users WHERE email = $1", target_email)
    print(f'Удалено пользователей: {result}')
    
    # 3. Проверка: пытаемся найти его
    check = await conn.fetchval("SELECT email FROM users WHERE email = $1", target_email)
    if check is None:
        print(" Пользователь успешно и полностью удален из базы!")
    else:
        print(" Пользователь все еще в базе!")
    
    await conn.close()

asyncio.run(main())
