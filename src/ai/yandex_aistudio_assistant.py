"""
Yandex AI Studio Assistant клиент через новый AIStudio SDK
Поддерживает работу с агентами и их инструментами (WebSearch и т.д.)
"""

import os
import json
import time
import jwt as pyjwt
from typing import Optional

from yandex_ai_studio_sdk import AIStudio

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config


class YandexAIStudioAssistantClient:
    """Клиент для работы с Yandex AI Studio агентами через AIStudio SDK"""
    
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
        
        # SDK и Assistant
        self.sdk = None
        self.assistant = None
        self._init_sdk()
    
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
        import requests
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
    
    def _init_sdk(self):
        """Инициализировать SDK"""
        try:
            # Получаем IAM токен
            iam_token = self._get_iam_token()
            
            # Создаем AIStudio SDK с IAM токеном
            self.sdk = AIStudio(
                folder_id=self.folder_id,
                auth=iam_token
            )
            
            # Получаем агента
            self.assistant = self.sdk.assistants.get(self.assistant_id)
            
        except Exception as e:
            raise Exception(f"Ошибка инициализации SDK: {e}")
    
    def send_message(self, text: str, screenshot_context: str = "") -> str:
        """Отправить сообщение агенту"""
        try:
            # Обновляем IAM токен если нужно
            iam_token = self._get_iam_token()
            
            # Пересоздаем SDK с новым токеном
            self.sdk = AIStudio(
                folder_id=self.folder_id,
                auth=iam_token
            )
            self.assistant = self.sdk.assistants.get(self.assistant_id)
            
            # Формируем сообщение
            user_message = text
            if screenshot_context:
                user_message = f"[Контекст из скриншота: {screenshot_context}]\n\n{text}"
            
            # Создаём новый thread (сессию разговора)
            thread = self.assistant.create_thread()
            
            # Отправляем сообщение в thread
            thread.write(user_message)
            
            # Запускаем assistant для обработки
            run = self.assistant.run(thread)
            
            # Ждём завершения и получаем результат
            result = run.wait()
            
            # Извлекаем текст ответа
            if hasattr(result, 'text'):
                return result.text
            elif hasattr(result, 'content'):
                if isinstance(result.content, str):
                    return result.content
                elif isinstance(result.content, list):
                    # Попытаемся извлечь текст из списка контента
                    texts = []
                    for item in result.content:
                        if hasattr(item, 'text'):
                            texts.append(item.text)
                        elif isinstance(item, dict) and 'text' in item:
                            texts.append(item['text'])
                    if texts:
                        return '\n'.join(texts)
                return str(result.content)
            else:
                # Попробуем получить последнее сообщение из thread
                messages = list(thread.get_messages())
                for message in reversed(messages):
                    if message.author.role == 'ASSISTANT':
                        if hasattr(message, 'text'):
                            return message.text
                        elif hasattr(message, 'content'):
                            # Извлекаем текст из content
                            content_parts = []
                            for part in message.content.content:
                                if hasattr(part, 'text'):
                                    content_parts.append(part.text)
                            if content_parts:
                                return '\n'.join(content_parts)
                
                return "❌ Не удалось извлечь ответ от агента"
                
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            return f"❌ Ошибка: {str(e)}\n\nДетали:\n{error_details}"
    
    def send_request(self, prompt: str, image_data: Optional[bytes] = None) -> str:
        """Отправить запрос (для совместимости с интерфейсом)"""
        if image_data:
            return self.send_message(f"{prompt}\n\n[Примечание: изображение было приложено, но пока не обрабатывается]")
        return self.send_message(prompt)
    
    def clear_history(self):
        """Очистить историю чата (каждый запрос создает новый thread)"""
        pass
    
    def update_context(self, game_name: Optional[str] = None, context_info: str = ""):
        """Обновить контекст - для совместимости с интерфейсом"""
        # Agent использует свой системный промпт из AI Studio
        pass
    
    def get_stats(self) -> dict:
        """Получить статистику"""
        return {
            "assistant_id": self.assistant_id,
            "sdk_initialized": bool(self.sdk),
            "assistant_initialized": bool(self.assistant),
            "folder_id": self.folder_id
        }
