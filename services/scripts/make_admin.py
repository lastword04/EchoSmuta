cd D:\Newgame\EchoSmyta\services\users
mkdir scripts 2>$null
@"
import asyncio
import asyncpg
import sys
from users_app.settings import settings


async def make_admin(email: str) -> None:
    dsn = settings.db.dsn.replace('+asyncpg', '').replace('+psycopg_async', '')
    conn = await asyncpg.connect(dsn)
    
    try:
        # Проверяем что пользователь существует
        user = await conn.fetchrow(
            "SELECT id, email, role FROM users WHERE email = $1",
            email
        )
        
        if user is None:
            print(f"❌ Пользователь с email '{email}' не найден")
            print("   Зарегистрируйся через игру, затем запусти скрипт снова")
            return
        
        if user['role'] == 'ADMIN':
            print(f"✅ Пользователь {email} уже ADMIN")
            return
        
        # Повышаем роль
        await conn.execute(
            "UPDATE users SET role = 'ADMIN' WHERE email = $1",
            email
        )
        
        print(f"✅ Роль обновлена: {email} → ADMIN")
        print("   Перелогинься в игре чтобы получить новый токен")
        
    finally:
        await conn.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: uv run python scripts/make_admin.py <email>")
        print("Пример: uv run python scripts/make_admin.py testadmin@mail.com")
        sys.exit(1)
    
    email = sys.argv[1]
    asyncio.run(make_admin(email))
"@ | Out-File -Encoding utf8 scripts\make_admin.py