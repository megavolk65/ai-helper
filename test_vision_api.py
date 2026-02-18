"""
Тест Vision API с IAM токеном
"""

import sys
import os
import json
import base64
import requests
from datetime import datetime, timedelta, timezone
import jwt

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config

# Загружаем авторизованный ключ
auth_key_path = os.path.join(os.path.dirname(__file__), "authorized_key.json")
with open(auth_key_path, 'r') as f:
    service_account_key = json.load(f)

# Генерируем JWT
now = datetime.now(timezone.utc)
payload = {
    'aud': 'https://iam.api.cloud.yandex.net/iam/v1/tokens',
    'iss': service_account_key['service_account_id'],
    'iat': int(now.timestamp()),
    'exp': int((now + timedelta(hours=1)).timestamp())
}

signed_token = jwt.encode(
    payload,
    service_account_key['private_key'],
    algorithm='PS256',
    headers={'kid': service_account_key['id']}
)

# Получаем IAM токен
print("1. Генерация IAM токена...")
response = requests.post(
    'https://iam.api.cloud.yandex.net/iam/v1/tokens',
    json={'jwt': signed_token}
)
response.raise_for_status()
iam_token = response.json()['iamToken']
print(f"✅ IAM токен получен: {iam_token[:20]}...")

# Создаём простое тестовое изображение (1x1 белый пиксель в PNG)
test_image_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="

# Тест 1: Vision API с Bearer токеном
print("\n2. Тест Vision API с Bearer токеном...")
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {iam_token}"
}

body = {
    "folderId": config.YANDEX_FOLDER_ID,
    "analyze_specs": [
        {
            "content": test_image_b64,
            "features": [
                {
                    "type": "TEXT_DETECTION",
                    "textDetectionConfig": {
                        "languageCodes": ["*"]
                    }
                }
            ]
        }
    ]
}

response = requests.post(
    "https://vision.api.cloud.yandex.net/vision/v1/batchAnalyze",
    headers=headers,
    json=body,
    timeout=30
)

print(f"Status: {response.status_code}")
print(f"Response: {response.text}")

if response.status_code == 200:
    print("✅ Vision API работает!")
else:
    print(f"❌ Ошибка: {response.status_code}")
