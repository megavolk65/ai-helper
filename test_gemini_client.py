#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Тест для GeminiClient
"""

import os
import sys

# Добавляем родительскую директорию в путь поиска
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.ai.gemini_client import GeminiClient

def main():
    print("=== Тест Google Gemini Client ===\n")
    
    try:
        # Создаём клиента
        client = GeminiClient()
        print("✅ Клиент успешно инициализирован")
        
        # Выводим статистику
        stats = client.get_stats()
        print(f"\nСтатистика:")
        print(f"  Модель: {stats['model']}")
        print(f"  Google Search: {'✅' if stats['has_search'] else '❌'}")
        print(f"  Vision: {'✅' if stats['has_vision'] else '❌'}")
        
        # Тест 1: Простой вопрос
        print("\n" + "="*50)
        print("Тест 1: Простой вопрос")
        print("="*50)
        response = client.send_message("Привет! Как тебя зовут?")
        print(f"\nОтвет: {response}")
        
        # Тест 2: Вопрос требующий поиска (актуальная информация)
        print("\n" + "="*50)
        print("Тест 2: Вопрос с поиском (актуальная информация)")
        print("="*50)
        response = client.send_message("Какие новые обновления вышли для игры Elden Ring в 2025 году?")
        print(f"\nОтвет: {response}")
        
        # Тест 3: Игровой вопрос
        print("\n" + "="*50)
        print("Тест 3: Игровой вопрос")
        print("="*50)
        client.update_context(game_name="Dark Souls 3")
        response = client.send_message("Где найти Estus Flask Shard в High Wall of Lothric?")
        print(f"\nОтвет: {response}")
        
    except Exception as e:
        print(f"❌ Ошибка: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n=== Тест завершён ===")

if __name__ == "__main__":
    main()
