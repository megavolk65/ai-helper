"""
Менеджер горячих клавиш
"""

import sys
import os
import json
from typing import Callable, Optional
from pynput import keyboard
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
        self._listener = None
        self._current_keys = set()
        
        # Загружаем горячие клавиши из настроек
        hotkey_overlay_str, hotkey_screenshot_str = self._load_hotkeys_from_settings()
        
        # Сохраняем строковые значения
        self.hotkey_overlay = hotkey_overlay_str
        self.hotkey_screenshot = hotkey_screenshot_str
        
        # Комбинации клавиш
        self._hotkey_toggle = self._parse_hotkey(hotkey_overlay_str)
        self._hotkey_screenshot = self._parse_hotkey(hotkey_screenshot_str)
    
    def _load_hotkeys_from_settings(self):
        """Загрузить горячие клавиши из settings.json"""
        try:
            settings_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                "settings.json"
            )
            with open(settings_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                return (
                    settings.get('hotkey_overlay', 'Insert'),
                    settings.get('hotkey_screenshot', 'Home')
                )
        except:
            return ('Insert', 'Home')
    
    def _parse_hotkey(self, hotkey_str: str) -> set:
        """Преобразовать строку горячей клавиши в набор клавиш"""
        key_map = {
            'insert': keyboard.Key.insert,
            'ins': keyboard.Key.insert,
            'home': keyboard.Key.home,
            'end': keyboard.Key.end,
            'delete': keyboard.Key.delete,
            'del': keyboard.Key.delete,
            'pageup': keyboard.Key.page_up,
            'page_up': keyboard.Key.page_up,
            'pagedown': keyboard.Key.page_down,
            'page_down': keyboard.Key.page_down,
            'f1': keyboard.Key.f1,
            'f2': keyboard.Key.f2,
            'f3': keyboard.Key.f3,
            'f4': keyboard.Key.f4,
            'f5': keyboard.Key.f5,
            'f6': keyboard.Key.f6,
            'f7': keyboard.Key.f7,
            'f8': keyboard.Key.f8,
            'f9': keyboard.Key.f9,
            'f10': keyboard.Key.f10,
            'f11': keyboard.Key.f11,
            'f12': keyboard.Key.f12,
            'pause': keyboard.Key.pause,
            'scroll_lock': keyboard.Key.scroll_lock,
            'print_screen': keyboard.Key.print_screen,
        }
        
        key_lower = hotkey_str.lower().strip()
        if key_lower in key_map:
            return {key_map[key_lower]}
        
        # По умолчанию Insert
        return {keyboard.Key.insert}
    
    def register_hotkeys(self):
        """Зарегистрировать все горячие клавиши"""
        try:
            # Создаём глобальный слушатель клавиатуры
            self._listener = keyboard.Listener(
                on_press=self._on_press,
                on_release=self._on_release
            )
            self._listener.start()
            return True
            
        except Exception as e:
            print(f"Ошибка регистрации горячих клавиш: {e}")
            return False
    
    def unregister_hotkeys(self):
        """Отменить регистрацию всех горячих клавиш"""
        if self._listener:
            self._listener.stop()
            self._listener = None
    
    def _on_press(self, key):
        """Обработчик нажатия клавиши"""
        # Нормализуем клавишу
        if hasattr(key, 'char') and key.char:
            normalized_key = keyboard.KeyCode.from_char(key.char.lower())
        else:
            normalized_key = key
        
        self._current_keys.add(normalized_key)
        
        # Проверяем комбинации
        if self._enabled:
            if self._current_keys >= self._hotkey_toggle:
                self.toggle_overlay.emit()
                self._current_keys.clear()  # Сбрасываем чтобы не срабатывало повторно
            elif self._current_keys >= self._hotkey_screenshot:
                self.take_screenshot.emit()
                self._current_keys.clear()
    
    def _on_release(self, key):
        """Обработчик отпускания клавиши"""
        # Нормализуем клавишу
        if hasattr(key, 'char') and key.char:
            normalized_key = keyboard.KeyCode.from_char(key.char.lower())
        else:
            normalized_key = key
        
        # Удаляем из нажатых
        self._current_keys.discard(normalized_key)
    
    def update_hotkeys(self, hotkey_overlay: str = None, hotkey_screenshot: str = None):
        """Обновить горячие клавиши без перезапуска"""
        if hotkey_overlay:
            self.hotkey_overlay = hotkey_overlay
            self._hotkey_toggle = self._parse_hotkey(hotkey_overlay)
        if hotkey_screenshot:
            self.hotkey_screenshot = hotkey_screenshot
            self._hotkey_screenshot = self._parse_hotkey(hotkey_screenshot)
    
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
            "toggle_overlay": config.HOTKEY_TOGGLE_OVERLAY,
            "screenshot": config.HOTKEY_SCREENSHOT,
        }
