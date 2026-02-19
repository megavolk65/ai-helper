#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Тест для YandexOpenAIClient
"""

import os
import sys

# Добавляем родительскую директорию в путь поиска
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.ai.yandex_openai_client import YandexOpenAIClient

def main():
    print("=== Тест Yandex OpenAI Client ===\n")
    
    try:
        # Создаём клиента
        client = YandexOpenAIClient()
        print("✅ Клиент успешно инициализирован")
        
        # Выводим статистику
        stats = client.get_stats()
        print(f"\nСтатистика:")
        print(f"  Folder ID: {stats['folder_id']}")
        print(f"  Assistant ID: {stats['assistant_id']}")
        print(f"  IAM Token: {'✅' if stats['has_iam_token'] else '❌'}")
        
        # Отправляем тестовое сообщение
        print("\nОтправка тестового сообщения...")
        response = client.send_message("Привет! Расскажи мне про поиск в интернете")
        
        print("\n=== Ответ от Yandex AI ===")
        print(response)
        
    except Exception as e:
        print(f"❌ Ошибка: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n=== Тест завершён ===")

if __name__ == "__main__":
    main()
