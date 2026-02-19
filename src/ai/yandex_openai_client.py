"""
Yandex AI Studio клиент через OpenAI SDK
Использует агента с WebSearch
"""

import os
import json
import time
import jwt as pyjwt
import requests
from typing import Optional
from openai import OpenAI

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config


class YandexOpenAIClient:
    """Клиент для работы с Yandex AI Studio через OpenAI SDK"""
    
    def __init__(self):
        self.folder_id = config.YANDEX_FOLDER_ID
        self.assistant_id = config.ASSISTANT_ID
        
        # Путь к авторизованному ключу
        self.auth_key_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "authorized_key.json"
        )
        
        # Загружаем данные авторизованного ключа
        with open(self.auth_key_path, 'r') as f:
            self.auth_key_data = json.load(f)
        
        # IAM токен и его срок действия
        self.iam_token = None
        self.iam_token_expires = None
        
        # История сообщений
        self.messages = []
        
        # Инициализируем OpenAI клиент
        self.client = None
        self._init_openai_client()
    
    def _create_jwt(self) -> str:
        """Создать JWT токен"""
        now = int(time.time())
        payload = {
            'aud': 'https://iam.api.cloud.yandex.net/iam/v1/tokens',
            'iss': self.auth_key_data['service_account_id'],
            'iat': now,
            'exp': now + 3600
        }
        
        # Подписываем JWT
        encoded_token = pyjwt.encode(
            payload,
            self.auth_key_data['private_key'],
            algorithm='PS256',
            headers={'kid': self.auth_key_data['id']}
        )
        
        return encoded_token
    
    def _get_iam_token(self) -> str:
        """Получить IAM токен"""
        # Проверяем, не истёк ли токен
        if self.iam_token and self.iam_token_expires:
            if time.time() < self.iam_token_expires:
                return self.iam_token
        
        # Создаем JWT
        jwt_token = self._create_jwt()
        
        # Обмениваем JWT на IAM токен
        response = requests.post(
            'https://iam.api.cloud.yandex.net/iam/v1/tokens',
            json={'jwt': jwt_token}
        )
        response.raise_for_status()
        
        data = response.json()
        self.iam_token = data['iamToken']
        # Токен живёт 12 часов, обновим через 11
        self.iam_token_expires = time.time() + 11 * 3600
        
        return self.iam_token
    
    def _init_openai_client(self):
        """Инициализировать OpenAI клиент для Yandex"""
        iam_token = self._get_iam_token()
        
        # OpenAI SDK добавляет /chat/completions к base_url
        # Используем /v1 endpoint как в примерах документации
        self.client = OpenAI(
            api_key=iam_token,
            base_url="https://llm.api.cloud.yandex.net/v1",
            default_headers={
                "x-folder-id": self.folder_id
            }
        )
    
    def send_message(self, text: str, screenshot_context: str = "") -> str:
        """Отправить сообщение через OpenAI SDK"""
        try:
            # Обновляем клиента, если токен истёк
            if self.iam_token_expires and time.time() >= self.iam_token_expires:
                self._init_openai_client()
            
            # Формируем сообщение
            user_message = text
            if screenshot_context:
                user_message = f"[Контекст из скриншота: {screenshot_context}]\n\n{text}"
            
            # Добавляем сообщение в историю
            self.messages.append({
                "role": "user",
                "content": user_message
            })
            
            # Отправляем запрос через OpenAI SDK
            # Используем полный URI агента в формате gpt://folder_id/assistant_id
            model_uri = f"gpt://{self.folder_id}/{self.assistant_id}"
            response = self.client.chat.completions.create(
                model=model_uri,
                messages=self.messages,
                temperature=0.6,
                max_tokens=2000
            )
            
            assistant_text = response.choices[0].message.content
            
            # Добавляем ответ в историю
            self.messages.append({
                "role": "assistant",
                "content": assistant_text
            })
            
            # Ограничиваем историю (последние 20 сообщений)
            if len(self.messages) > 20:
                self.messages = self.messages[-20:]
            
            return assistant_text
            
        except Exception as e:
            error_text = str(e)
            if hasattr(e, 'response'):
                error_text = f"HTTP {e.response.status_code}: {e.response.text}"
            return f"❌ Ошибка: {error_text}"
    
    def send_request(self, prompt: str, image_data: Optional[bytes] = None) -> str:
        """Отправить запрос (для совместимости с интерфейсом)"""
        if image_data:
            return self.send_message(f"{prompt}\n\n[Примечание: изображение было приложено, но пока не обрабатывается]")
        return self.send_message(prompt)
    
    def clear_history(self):
        """Очистить историю чата"""
        self.messages = []
    
    def update_context(self, game_name: Optional[str] = None, context_info: str = ""):
        """Обновить контекст (системный промпт)"""
        if game_name:
            system_text = f"Ты AI-помощник для игры {game_name}. Помогай с прохождением, подсказывай локации, объясняй механики."
        else:
            system_text = "Ты универсальный AI-помощник. Отвечай кратко и по делу."
        
        if context_info:
            system_text += f"\n\nДополнительный контекст: {context_info}"
        
        # Обновляем или добавляем системное сообщение
        if self.messages and self.messages[0].get("role") == "system":
            self.messages[0]["content"] = system_text
        else:
            self.messages.insert(0, {"role": "system", "content": system_text})
    
    def get_stats(self) -> dict:
        """Получить статистику"""
        return {
            "assistant_id": self.assistant_id,
            "folder_id": self.folder_id,
            "has_iam_token": bool(self.iam_token),
            "messages_count": len(self.messages)
        }
