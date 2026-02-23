"""
Менеджер горячих клавиш

Использует библиотеку keyboard для глобального перехвата клавиш.
"""

import sys
import os
import json
import keyboard
from PyQt6.QtCore import QObject, pyqtSignal

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config


class HotkeyManager(QObject):
    """Менеджер глобальных горячих клавиш"""
    
    # Сигналы
    toggle_overlay = pyqtSignal()
    take_screenshot = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self._enabled = True
        self._hotkey_handles = []
        
        # Загружаем горячие клавиши из настроек
        self.hotkey_overlay_str, self.hotkey_screenshot_str = self._load_hotkeys_from_settings()
    
    def _load_hotkeys_from_settings(self):
        """Загрузить горячие клавиши из settings.json"""
        try:
            if getattr(sys, 'frozen', False):
                base_path = os.path.dirname(sys.executable)
            else:
                base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
            settings_path = os.path.join(base_path, "settings.json")
            with open(settings_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                return (
                    settings.get('hotkey_overlay', 'Insert'),
                    settings.get('hotkey_screenshot', 'Home')
                )
        except:
            return ('Insert', 'Home')
    
    def _on_overlay_hotkey(self):
        """Обработчик горячей клавиши оверлея"""
        if self._enabled:
            self.toggle_overlay.emit()
    
    def _on_screenshot_hotkey(self):
        """Обработчик горячей клавиши скриншота"""
        if self._enabled:
            self.take_screenshot.emit()
    
    def register_hotkeys(self):
        """Зарегистрировать все горячие клавиши"""
        try:
            self.unregister_hotkeys()
            
            # Регистрируем горячие клавиши
            h1 = keyboard.add_hotkey(self.hotkey_overlay_str, self._on_overlay_hotkey, suppress=False)
            h2 = keyboard.add_hotkey(self.hotkey_screenshot_str, self._on_screenshot_hotkey, suppress=False)
            self._hotkey_handles = [h1, h2]
            
            return True
        except Exception as e:
            print(f"Ошибка регистрации горячих клавиш: {e}")
            return False
    
    def unregister_hotkeys(self):
        """Отменить регистрацию всех горячих клавиш"""
        for handle in self._hotkey_handles:
            try:
                keyboard.remove_hotkey(handle)
            except:
                pass
        self._hotkey_handles = []
    
    def update_hotkeys(self, hotkey_overlay: str = None, hotkey_screenshot: str = None):
        """Обновить горячие клавиши"""
        if hotkey_overlay:
            self.hotkey_overlay_str = hotkey_overlay
        if hotkey_screenshot:
            self.hotkey_screenshot_str = hotkey_screenshot
        self.register_hotkeys()
    
    def set_enabled(self, enabled: bool):
        """Включить/выключить обработку горячих клавиш"""
        self._enabled = enabled
    
    @property
    def is_enabled(self) -> bool:
        """Включены ли горячие клавиши"""
        return self._enabled
    
    def get_hotkey_description(self) -> dict:
        """Получить описание горячих клавиш"""
        return {
            "toggle_overlay": self.hotkey_overlay_str,
            "screenshot": self.hotkey_screenshot_str,
        }
