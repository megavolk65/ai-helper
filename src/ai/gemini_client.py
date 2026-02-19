"""
Google Gemini AI клиент
Поддержка Google Search и анализа изображений
"""

import os
import sys
from typing import Optional
from google import genai
from google.genai import types

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config


class GeminiClient:
    """Клиент для работы с Google Gemini"""
    
    def __init__(self):
        # Клиент с API версией v1alpha (для Google Search)
        self.client = genai.Client(
            api_key=config.GEMINI_API_KEY,
            http_options=types.HttpOptions(api_version='v1alpha')
        )
        
        # Модель
        self.model_name = getattr(config, 'GEMINI_MODEL', 'gemini-2.5-flash')
        
        # Конфиг с Google Search
        self.config_with_search = types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())],
            temperature=0.7,
        )
        
        # История
        self.history = []
        self.current_game_name = None
    
    def send_message(self, text: str, screenshot_context: str = "") -> str:
        """
        Отправить текстовое сообщение
        
        Args:
            text: Текст сообщения
            screenshot_context: Контекст из скриншота (OCR)
        
        Returns:
            Ответ от Gemini
        """
        try:
            # Формируем сообщение
            user_message = text
            if screenshot_context:
                user_message = f"[Контекст с экрана: {screenshot_context}]\n\n{text}"
            
            # Добавляем в историю
            self.history.append(
                types.Content(role="user", parts=[types.Part(text=user_message)])
            )
            
            # Отправляем с Google Search
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=self.history,
                config=self.config_with_search,
            )
            
            # Добавляем ответ в историю
            assistant_text = response.text
            self.history.append(
                types.Content(role="model", parts=[types.Part(text=assistant_text)])
            )
            
            return assistant_text
            
        except Exception as e:
            return f"❌ Ошибка Gemini: {str(e)}"
    
    def send_request(self, prompt: str, image_data: Optional[bytes] = None) -> str:
        """
        Отправить запрос с возможным изображением
        
        Args:
            prompt: Текст запроса
            image_data: Байты изображения (PNG/JPEG)
        
        Returns:
            Ответ от Gemini
        """
        try:
            if image_data:
                # Добавляем изображение в историю
                parts = [
                    types.Part(text=prompt),
                    types.Part(inline_data=types.Blob(mime_type="image/png", data=image_data))
                ]
                self.history.append(types.Content(role="user", parts=parts))
                
                # Отправляем запрос
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=self.history,
                    config=self.config_with_search,
                )
                
                # Добавляем ответ
                assistant_text = response.text
                self.history.append(
                    types.Content(role="model", parts=[types.Part(text=assistant_text)])
                )
                return assistant_text
            else:
                # Обычный текстовый запрос
                return self.send_message(prompt)
                
        except Exception as e:
            return f"❌ Ошибка Gemini: {str(e)}"
    
    def clear_history(self):
        """Очистить историю чата"""
        self.history = []
    
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
            
            # Добавляем системное сообщение в историю
            self.history.append(
                types.Content(role="user", parts=[types.Part(text=system_text)])
            )
            self.history.append(
                types.Content(role="model", parts=[types.Part(text="Понял, готов помогать!")])
            )
    
    def get_stats(self) -> dict:
        """Получить статистику"""
        return {
            "model": self.model_name,
            "has_search": True,
            "has_vision": True,
            "history_length": len(self.history)
        }
