import requests
import uuid

base_url = "http://localhost:9090/api/auth/register"

for i in range(1, 1001):
    user_data = {
        "email": f"neclark{i}@example.com",  # Уникальный email
        "password": "1",
        "source_of_knowledge": "test",
        "name": f"neclark{i}",  # Уникальный ник
        "race": "orc",
        "is_male": True,
        "captcha_id": str(uuid.uuid4()),  # Уникальный UUID для капчи
        "user_input": "316",
        "fingerprint": "ccc",
        "visit_id": str(uuid.uuid4()),
    }

    try:
        response = requests.post(base_url, json=user_data, timeout=120)
        if response.status_code == 200 or response.status_code == 201:
            print(f"Пользователь {i} зарегистрирован: {user_data['email']}")
        else:
            print(f"Ошибка при регистрации пользователя {i}: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Исключение при регистрации пользователя {i}: {e}")

print("Регистрация завершена.")
