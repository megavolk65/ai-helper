"""
Yandex Vision API - анализ изображений
"""

import sys
import os
import base64
import requests
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config
from src.ai.yandex_gpt_rest import YandexGPTRestClient


class YandexVisionClient:
    """Клиент для работы с Yandex Vision API"""
    
    API_URL = "https://vision.api.cloud.yandex.net/vision/v1/batchAnalyze"
    
    def __init__(self):
        self.folder_id = config.YANDEX_FOLDER_ID
        # Используем shared IAM token manager из YandexGPTRestClient
        self._gpt_client = YandexGPTRestClient()
        self._initialized = False
        self._error_message: Optional[str] = None
    
    def initialize(self) -> bool:
        """Инициализировать клиент"""
        if not self.folder_id:
            self._error_message = "Не указан YANDEX_FOLDER_ID в config.py"
            return False
        
        # Проверяем что GPT клиент может получить IAM токен
        try:
            token = self._gpt_client._get_iam_token()
            if not token:
                self._error_message = "Не удалось получить IAM токен"
                return False
        except Exception as e:
            self._error_message = f"Ошибка при получении IAM токена: {str(e)}"
            return False
        
        self._initialized = True
        return True
    
    @property
    def is_ready(self) -> bool:
        """Готов ли клиент"""
        return self._initialized or self.initialize()
    
    def analyze_image(self, image_base64: str, features: list = None) -> Optional[str]:
        """
        Анализировать изображение
        
        Args:
            image_base64: Изображение в формате base64
            features: Список features для анализа
        
        Returns:
            Описание изображения или None при ошибке
        """
        if not self.is_ready:
            return None
        
        if features is None:
            features = [
                {
                    "type": "TEXT_DETECTION",
                    "textDetectionConfig": {
                        "languageCodes": ["*"]
                    }
                }
            ]
        
        try:
            # Получаем токен авторизации (уже с префиксом Bearer/Api-Key)
            auth_header = self._gpt_client._get_iam_token()
            if not auth_header:
                self._error_message = "Не удалось получить токен авторизации"
                return None
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": auth_header
            }
            
            body = {
                "folderId": self.folder_id,
                "analyze_specs": [
                    {
                        "content": image_base64,
                        "features": features
                    }
                ]
            }
            
            response = requests.post(
                self.API_URL,
                headers=headers,
                json=body,
                timeout=30
            )
            
            if response.status_code != 200:
                self._error_message = f"Vision API error: {response.status_code} - {response.text}"
                
                # Логируем в файл
                log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "vision_debug.log")
                with open(log_path, 'a', encoding='utf-8') as log:
                    log.write(f"\n=== Vision API Error ===\n")
                    log.write(f"Time: {__import__('datetime').datetime.now()}\n")
                    log.write(f"Status: {response.status_code}\n")
                    log.write(f"Auth header: {headers.get('Authorization', 'None')[:50]}...\n")
                    log.write(f"Response: {response.text}\n")
                
                return None
            
            result = response.json()
            
            # Извлекаем текст из результата
            text_parts = []
            
            if "results" in result:
                for res in result["results"]:
                    if "results" in res:
                        for r in res["results"]:
                            if "textDetection" in r:
                                pages = r["textDetection"].get("pages", [])
                                for page in pages:
                                    blocks = page.get("blocks", [])
                                    for block in blocks:
                                        lines = block.get("lines", [])
                                        for line in lines:
                                            words = line.get("words", [])
                                            line_text = " ".join(
                                                w.get("text", "") for w in words
                                            )
                                            if line_text.strip():
                                                text_parts.append(line_text.strip())
            
            if text_parts:
                return "\n".join(text_parts)
            
            return "Текст на изображении не обнаружен"
            
        except requests.exceptions.Timeout:
            self._error_message = "Timeout при запросе к Vision API"
            return None
        except Exception as e:
            self._error_message = f"Ошибка Vision API: {str(e)}"
            return None
    
    def analyze_screenshot(self, screenshot_base64: str) -> str:
        """
        Анализировать скриншот для игрового контекста
        
        Args:
            screenshot_base64: Скриншот в base64
        
        Returns:
            Описание контекста скриншота
        """
        # Получаем текст с изображения
        text = self.analyze_image(screenshot_base64)
        
        if text:
            return f"Текст на экране: {text}"
        
        return "Не удалось распознать содержимое экрана"
    
    @property
    def error_message(self) -> Optional[str]:
        """Сообщение об ошибке"""
        return self._error_message
