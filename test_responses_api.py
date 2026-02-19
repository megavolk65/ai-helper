"""
Тестовый скрипт для проверки Yandex Responses API
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.ai.yandex_responses_api import YandexResponsesAPIClient

def test_responses_api():
    """Тестирование Responses API"""
    print("=== Тест Yandex Responses API ===\n")
    
    try:
        client = YandexResponsesAPIClient()
        print("✅ Клиент успешно инициализирован\n")
        
        print("Отправка тестового сообщения...")
        response = client.send_message("Привет! Ответь коротко.")
        
        print("\n=== Ответ от Yandex AI ===")
        print(response)
        print("\n=== Тест завершён ===")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_responses_api()
