"""
YandexGPT Assistant клиент через YandexCloud ML SDK
Поддерживает работу с агентами, включая WebSearch и другие инструменты
"""

import os
import json
import time
import jwt as pyjwt
from typing import Optional

# Используем yandex_cloud_ml_sdk (хотя deprecated, но доступен)
from yandex_cloud_ml_sdk import YCloudML
from yandex_cloud_ml_sdk.auth import IAMTokenAuth
import yandexcloud
from yandex.cloud.iam.v1.iam_token_service_pb2 import CreateIamTokenRequest
from yandex.cloud.iam.v1.iam_token_service_pb2_grpc import IamTokenServiceStub

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config


class YandexAssistantClient:
    """Клиент для работы с Yandex AI Studio Assistant"""
    
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
        
        # Инициализируем SDK
        self.yc_sdk = None
        self.sdk = None
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
        """Получить IAM токен через yandexcloud SDK"""
        # Создаем JWT
        jwt_token = self._create_jwt()
        
        # Создаем SDK
        sdk = yandexcloud.SDK(service_account_key=self.auth_key_data)
        
        # Обмениваем JWT на IAM токен
        iam_service = sdk.client(IamTokenServiceStub)
        response = iam_service.Create(CreateIamTokenRequest(jwt=jwt_token))
        
        return response.iam_token
    
    def _init_sdk(self):
        """Инициализировать SDK с авторизацией через сервисный аккаунт"""
        try:
            # Получаем IAM токен
            iam_token = self._get_iam_token()
            
            # Создаем объект авторизации с IAM токеном
            auth = IAMTokenAuth(iam_token)
            
            # Создаем YCloudML SDK
            self.sdk = YCloudML(
                folder_id=self.folder_id,
                auth=auth
            )
            
        except Exception as e:
            raise Exception(f"Ошибка инициализации SDK: {e}")
    
    def send_message(self, text: str, screenshot_context: str = "") -> str:
        """Отправить сообщение ассистенту"""
        try:
            if not self.sdk:
                return "❌ SDK не инициализирован"
            
            # Формируем сообщение
            user_message = text
            if screenshot_context:
                user_message = f"[Контекст из скриншота: {screenshot_context}]\n\n{text}"
            
            # Получаем ассистента через SDK
            assistant = self.sdk.assistants.get(self.assistant_id)
            
            # Создаём новый thread (сессию разговора)
            thread = assistant.create_thread()
            
            # Отправляем сообщение в thread
            thread.write(user_message)
            
            # Запускаем assistant для обработки
            run = assistant.run(thread)
            
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
                    for item in result.content:
                        if hasattr(item, 'text'):
                            return item.text
                        elif isinstance(item, dict) and 'text' in item:
                            return item['text']
                return str(result.content)
            else:
                return "❌ Не удалось извлечь ответ от ассистента"
                
        except Exception as e:
            return f"❌ Ошибка: {str(e)}"
    
    def send_request(self, prompt: str, image_data: Optional[bytes] = None) -> str:
        """Отправить запрос (для совместимости с интерфейсом)"""
        # TODO: добавить поддержку изображений если SDK это позволяет
        if image_data:
            # Пока игнорируем изображения, так как нужно разобраться с API
            return self.send_message(f"{prompt}\n\n[Примечание: изображение было приложено, но пока не обрабатывается]")
        return self.send_message(prompt)
    
    def clear_history(self):
        """Очистить историю чата (каждый запрос создает новый thread, так что не нужно)"""
        pass
    
    def update_context(self, game_name: Optional[str] = None, context_info: str = ""):
        """Обновить контекст - для совместимости с интерфейсом"""
        # Assistant использует свой системный промпт из AI Studio
        pass
    
    def get_stats(self) -> dict:
        """Получить статистику"""
        return {
            "assistant_id": self.assistant_id,
            "sdk_initialized": bool(self.sdk),
            "folder_id": self.folder_id
        }
