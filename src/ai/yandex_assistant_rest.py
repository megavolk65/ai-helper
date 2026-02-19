"""
Yandex Assistant клиент через REST API
Поддерживает работу с агентами, включая все инструменты
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


class YandexAssistantRestClient:
    """Клиент для работы с Yandex AI Studio Assistant через REST API"""
    
    BASE_URL = "https://assistant.api.cloud.yandex.net/ai/v1/assistants"
    
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
        
        # Текущий thread
        self.current_thread_id = None
    
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
        """Отправить сообщение ассистенту"""
        try:
            # Формируем сообщение
            user_message = text
            if screenshot_context:
                user_message = f"[Контекст из скриншота: {screenshot_context}]\\n\\n{text}"
            
            # Создаем новый thread
            thread_response = requests.post(
                f"{self.BASE_URL}/{self.assistant_id}:createThread",
                headers=self._get_headers(),
                json={}
            )
            thread_response.raise_for_status()
            thread_data = thread_response.json()
            thread_id = thread_data['id']
            
            # Отправляем сообщение в thread
            message_response = requests.post(
                f"{self.BASE_URL}/{self.assistant_id}/threads/{thread_id}/messages",
                headers=self._get_headers(),
                json={
                    'content': {
                        'content': [
                            {
                                'text': user_message
                            }
                        ]
                    },
                    'author': {
                        'id': 'user',
                        'role': 'USER'
                    }
                }
            )
            message_response.raise_for_status()
            
            # Запускаем ассистента
            run_response = requests.post(
                f"{self.BASE_URL}/{self.assistant_id}/threads/{thread_id}:run",
                headers=self._get_headers(),
                json={}
            )
            run_response.raise_for_status()
            run_data = run_response.json()
            run_id = run_data['id']
            
            # Ждём завершения
            max_attempts = 60
            for _ in range(max_attempts):
                status_response = requests.get(
                    f"{self.BASE_URL}/{self.assistant_id}/runs/{run_id}",
                    headers=self._get_headers()
                )
                status_response.raise_for_status()
                status_data = status_response.json()
                
                if status_data['state']['status'] == 'COMPLETED':
                    break
                elif status_data['state']['status'] in ['FAILED', 'CANCELLED']:
                    return f"❌ Ошибка выполнения: {status_data['state'].get('error', 'Unknown error')}"
                
                time.sleep(1)
            else:
                return "❌ Превышено время ожидания ответа"
            
            # Получаем сообщения из thread
            messages_response = requests.get(
                f"{self.BASE_URL}/{self.assistant_id}/threads/{thread_id}/messages",
                headers=self._get_headers()
            )
            messages_response.raise_for_status()
            messages_data = messages_response.json()
            
            # Ищем последний ответ ассистента
            for message in reversed(messages_data.get('messages', [])):
                if message['author']['role'] == 'ASSISTANT':
                    content = message.get('content', {}).get('content', [])
                    for part in content:
                        if 'text' in part:
                            return part['text']
            
            return "❌ Ответ от ассистента не найден"
            
        except requests.exceptions.HTTPError as e:
            return f"❌ HTTP ошибка: {e.response.status_code} - {e.response.text}"
        except Exception as e:
            return f"❌ Ошибка: {str(e)}"
    
    def send_request(self, prompt: str, image_data: Optional[bytes] = None) -> str:
        """Отправить запрос (для совместимости с интерфейсом)"""
        if image_data:
            return self.send_message(f"{prompt}\\n\\n[Примечание: изображение было приложено, но пока не обрабатывается]")
        return self.send_message(prompt)
    
    def clear_history(self):
        """Очистить историю чата"""
        self.current_thread_id = None
    
    def update_context(self, game_name: Optional[str] = None, context_info: str = ""):
        """Обновить контекст - для совместимости с интерфейсом"""
        pass
    
    def get_stats(self) -> dict:
        """Получить статистику"""
        return {
            "assistant_id": self.assistant_id,
            "folder_id": self.folder_id,
            "has_iam_token": bool(self.iam_token)
        }
