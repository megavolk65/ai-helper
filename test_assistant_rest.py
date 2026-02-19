"""
Тестовый скрипт для проверки Yandex Assistant REST API
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.ai.yandex_assistant_rest import YandexAssistantRestClient

def test_assistant_rest():
    """Тестирование Assistant REST API"""
    print("=== Тест Yandex Assistant REST API ===\n")
    
    try:
        client = YandexAssistantRestClient()
        print("✅ Клиент успешно инициализирован\n")
        
        print("Отправка тестового сообщения...")
        response = client.send_message("Привет! Это тестовое сообщение. Ответь коротко.")
        
        print("\n=== Ответ от Yandex Assistant ===")
        print(response)
        print("\n=== Тест завершён ===")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_assistant_rest()
