"""
Тестовый скрипт для проверки Yandex AIStudio Assistant SDK
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.ai.yandex_aistudio_assistant import YandexAIStudioAssistantClient

def test_aistudio_assistant():
    """Тестирование AIStudio Assistant SDK"""
    print("=== Тест Yandex AIStudio Assistant SDK ===\n")
    
    try:
        client = YandexAIStudioAssistantClient()
        print("✅ Клиент успешно инициализирован\n")
        
        print("Отправка тестового сообщения...")
        response = client.send_message("Привет! Найди информацию про погоду в Москве сегодня.")
        
        print("\n=== Ответ от агента ===")
        print(response)
        print("\n=== Тест завершён ===")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_aistudio_assistant()
