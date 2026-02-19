"""
OpenRouter AI клиент
Поддержка множества моделей через единый API
"""

import os
import sys
import json
from typing import Optional
import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config


class OpenRouterClient:
    """Клиент для работы с OpenRouter API"""
    
    def __init__(self):
        # Сначала пробуем загрузить из settings.json
        self.api_key = self._load_api_key_from_settings()
        if not self.api_key:
            self.api_key = getattr(config, 'OPENROUTER_API_KEY', '')
        
        self.model_name = getattr(config, 'OPENROUTER_MODEL', 'google/gemma-3-27b-it:free:online')
        self.base_url = "https://openrouter.ai/api/v1"
        
        # История сообщений
        self.history = []
        self.current_game_name = None
    
    def _load_api_key_from_settings(self) -> str:
        """Загрузить API ключ из settings.json"""
        try:
            settings_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                "settings.json"
            )
            with open(settings_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                return settings.get('api_key', '')
        except:
            return ''
    
    def send_message(self, text: str, screenshot_context: str = "") -> str:
        """
        Отправить текстовое сообщение
        
        Args:
            text: Текст сообщения
            screenshot_context: Контекст из скриншота (OCR)
        
        Returns:
            Ответ от модели
        """
        try:
            # Формируем сообщение
            user_message = text
            if screenshot_context:
                user_message = f"[Контекст с экрана: {screenshot_context}]\n\n{text}"
            
            # Добавляем в историю
            self.history.append({
                "role": "user",
                "content": user_message
            })
            
            # Отправляем запрос
            response = self._make_request(self.history)
            
            # Добавляем ответ в историю
            self.history.append({
                "role": "assistant",
                "content": response
            })
            
            return response
            
        except Exception as e:
            return f"❌ Ошибка OpenRouter: {str(e)}"
    
    def send_request(self, prompt: str, image_data: Optional[bytes] = None) -> str:
        """
        Отправить запрос с возможным изображением
        
        Args:
            prompt: Текст запроса
            image_data: Байты изображения (PNG/JPEG)
        
        Returns:
            Ответ от модели
        """
        try:
            if image_data:
                # Конвертируем изображение в base64
                import base64
                image_base64 = base64.b64encode(image_data).decode('utf-8')
                
                # Формируем сообщение с изображением
                self.history.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_base64}"
                            }
                        }
                    ]
                })
                
                # Отправляем запрос
                response = self._make_request(self.history)
                
                # Добавляем ответ
                self.history.append({
                    "role": "assistant",
                    "content": response
                })
                
                return response
            else:
                # Обычный текстовый запрос
                return self.send_message(prompt)
                
        except Exception as e:
            return f"❌ Ошибка OpenRouter: {str(e)}"
    
    def _make_request(self, messages: list) -> str:
        """
        Выполнить HTTP запрос к OpenRouter API
        
        Args:
            messages: История сообщений
        
        Returns:
            Ответ от модели
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/megavolk65/ai-helper",
            "X-Title": "AI Helper"
        }
        
        payload = {
            "model": self.model_name,
            "messages": messages,
            "plugins": [
                {
                    "id": "web",
                    "max_results": 5
                }
            ]
        }
        
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=60
        )
        
        response.raise_for_status()
        result = response.json()
        
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"]
        else:
            raise Exception(f"Неожиданный ответ API: {result}")
    
    def clear_history(self):
        """Очистить историю чата"""
        self.history = []
    
    def set_model(self, model_id: str):
        """
        Установить модель
        
        Args:
            model_id: ID модели OpenRouter
        """
        self.model_name = model_id
    
    def get_model(self) -> str:
        """Получить текущую модель"""
        return self.model_name
    
    def update_context(self, game_name: Optional[str] = None, context_info: str = ""):
        """
        Обновить контекст (системный промпт)
        
        Args:
            game_name: Название игры
            context_info: Дополнительная информация
        """
        # Сохраняем текущий контекст
        self.current_game_name = game_name
        
        # Если история пуста - добавляем системный промпт
        if len(self.history) == 0:
            if game_name:
                system_text = f"Ты AI-помощник для игры {game_name}. Помогай с прохождением, подсказывай локации, объясняй механики. Используй поиск для актуальной информации."
            else:
                system_text = "Ты универсальный AI-помощник. Отвечай кратко и по делу. Используй поиск для актуальной информации."
            
            if context_info:
                system_text += f"\n\nДополнительный контекст: {context_info}"
            
            # Добавляем системное сообщение
            self.history.append({
                "role": "system",
                "content": system_text
            })
    
    def get_stats(self) -> dict:
        """Получить статистику"""
        return {
            "model": self.model_name,
            "has_search": ":online" in self.model_name,
            "has_vision": "gemma-3" in self.model_name or "vision" in self.model_name,
            "history_length": len(self.history)
        }
