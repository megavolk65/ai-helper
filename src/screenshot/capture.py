"""
Модуль захвата скриншотов
"""

import io
import base64
from typing import Optional, Tuple
import mss
from PIL import Image


class ScreenCapture:
    """Класс для захвата скриншотов"""
    
    def __init__(self):
        self._last_screenshot: Optional[Image.Image] = None
        self._last_screenshot_base64: Optional[str] = None
    
    def capture_screen(self, monitor: int = 0) -> Optional[Image.Image]:
        """
        Захватить экран
        
        Args:
            monitor: Номер монитора (0 = все мониторы, 1 = первый и т.д.)
        
        Returns:
            PIL Image или None при ошибке
        """
        try:
            with mss.mss() as sct:
                # Получаем информацию о мониторах
                monitors = sct.monitors
                
                if monitor >= len(monitors):
                    monitor = 0
                
                # Захватываем экран
                screenshot = sct.grab(monitors[monitor])
                
                # Конвертируем в PIL Image
                img = Image.frombytes(
                    "RGB",
                    screenshot.size,
                    screenshot.bgra,
                    "raw",
                    "BGRX"
                )
                
                self._last_screenshot = img
                return img
                
        except Exception as e:
            print(f"Ошибка захвата экрана: {e}")
            return None
    
    def capture_primary_monitor(self) -> Optional[Image.Image]:
        """Захватить основной монитор"""
        return self.capture_screen(monitor=1)
    
    def capture_all_monitors(self) -> Optional[Image.Image]:
        """Захватить все мониторы"""
        return self.capture_screen(monitor=0)
    
    def get_screenshot_base64(self, image: Optional[Image.Image] = None, 
                               max_size: Tuple[int, int] = (1920, 1080),
                               quality: int = 85) -> Optional[str]:
        """
        Получить скриншот в формате base64
        
        Args:
            image: PIL Image (если None, используется последний скриншот)
            max_size: Максимальный размер (ширина, высота)
            quality: Качество JPEG (1-100)
        
        Returns:
            Base64 строка или None
        """
        img = image or self._last_screenshot
        if img is None:
            return None
        
        try:
            # Уменьшаем если нужно
            if img.width > max_size[0] or img.height > max_size[1]:
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Конвертируем в JPEG и base64
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=quality)
            buffer.seek(0)
            
            base64_str = base64.b64encode(buffer.getvalue()).decode("utf-8")
            self._last_screenshot_base64 = base64_str
            
            return base64_str
            
        except Exception as e:
            print(f"Ошибка конвертации в base64: {e}")
            return None
    
    def save_screenshot(self, path: str, image: Optional[Image.Image] = None) -> bool:
        """
        Сохранить скриншот в файл
        
        Args:
            path: Путь к файлу
            image: PIL Image (если None, используется последний скриншот)
        
        Returns:
            True если успешно
        """
        img = image or self._last_screenshot
        if img is None:
            return False
        
        try:
            img.save(path)
            return True
        except Exception as e:
            print(f"Ошибка сохранения скриншота: {e}")
            return False
    
    @property
    def last_screenshot(self) -> Optional[Image.Image]:
        """Последний захваченный скриншот"""
        return self._last_screenshot
    
    @property
    def last_screenshot_base64(self) -> Optional[str]:
        """Последний скриншот в base64"""
        return self._last_screenshot_base64
    
    def capture_and_encode(self, monitor: int = 1) -> Optional[str]:
        """
        Захватить экран и сразу конвертировать в base64
        
        Args:
            monitor: Номер монитора
        
        Returns:
            Base64 строка или None
        """
        img = self.capture_screen(monitor)
        if img:
            return self.get_screenshot_base64(img)
        return None
