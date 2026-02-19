"""
Yandex Responses API клиент (новый OpenAI-совместимый API для агентов)
Заменяет устаревший Assistant API
"""

import os
import json
import time
import jwt as pyjwt
import requests
from typing import Optional

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config


class YandexResponsesAPIClient:
    """Клиент для работы с Yandex AI Studio через Responses API"""
    
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
    
    def _get_headers(self) -> dict:
        """Получить заголовки для запроса"""
        return {
            'Authorization': f'Bearer {self._get_iam_token()}',
            'x-folder-id': self.folder_id,
            'Content-Type': 'application/json'
        }
    
    def send_message(self, text: str, screenshot_context: str = "") -> str:
        """Отправить сообщение через Responses API"""
        try:
            # Формируем сообщение
            user_message = text
            if screenshot_context:
                user_message = f"[Контекст из скриншота: {screenshot_context}]\n\n{text}"
            
            # Добавляем сообщение в историю
            self.messages.append({
                "role": "user",
                "text": user_message
            })
            
            # Формируем запрос к Responses API
            # Используем agent:// URI для доступа к агенту с WebSearch
            url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
            
            payload = {
                "modelUri": f"agent://{self.folder_id}/{self.assistant_id}",
                "completionOptions": {
                    "stream": False,
                    "temperature": 0.6,
                    "maxTokens": 2000
                },
                "messages": self.messages
            }
            
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                assistant_text = result["result"]["alternatives"][0]["message"]["text"]
                
                # Добавляем ответ в историю
                self.messages.append({
                    "role": "assistant",
                    "text": assistant_text
                })
                
                # Ограничиваем историю (последние 20 сообщений)
                if len(self.messages) > 20:
                    self.messages = self.messages[-20:]
                
                return assistant_text
            else:
                error_text = f"HTTP {response.status_code}: {response.text}"
                return f"❌ Ошибка API: {error_text}"
            
        except requests.exceptions.Timeout:
            return "❌ Превышено время ожидания ответа от сервера"
        except requests.exceptions.RequestException as e:
            return f"❌ Ошибка сети: {str(e)}"
        except Exception as e:
            return f"❌ Ошибка: {str(e)}"
    
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
        # Responses API использует системный промпт через первое сообщение
        if game_name:
            system_text = f"Ты AI-помощник для игры {game_name}. Помогай с прохождением, подсказывай локации, объясняй механики."
        else:
            system_text = "Ты универсальный AI-помощник. Отвечай кратко и по делу."
        
        if context_info:
            system_text += f"\n\nДополнительный контекст: {context_info}"
        
        # Обновляем или добавляем системное сообщение
        if self.messages and self.messages[0].get("role") == "system":
            self.messages[0]["text"] = system_text
        else:
            self.messages.insert(0, {"role": "system", "text": system_text})
    
    def get_stats(self) -> dict:
        """Получить статистику"""
        return {
            "assistant_id": self.assistant_id,
            "folder_id": self.folder_id,
            "has_iam_token": bool(self.iam_token),
            "messages_count": len(self.messages)
        }
