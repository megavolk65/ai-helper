"""
Менеджер горячих клавиш
"""

import sys
import os
from typing import Callable, Optional
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
        self._registered_hotkeys = []
        self._enabled = True
    
    def register_hotkeys(self):
        """Зарегистрировать все горячие клавиши"""
        try:
            # Открыть/скрыть оверлей
            keyboard.add_hotkey(
                config.HOTKEY_TOGGLE_OVERLAY,
                self._on_toggle_overlay,
                suppress=True
            )
            self._registered_hotkeys.append(config.HOTKEY_TOGGLE_OVERLAY)
            
            # Скриншот
            keyboard.add_hotkey(
                config.HOTKEY_SCREENSHOT,
                self._on_screenshot,
                suppress=True
            )
            self._registered_hotkeys.append(config.HOTKEY_SCREENSHOT)
            
            return True
            
        except Exception as e:
            print(f"Ошибка регистрации горячих клавиш: {e}")
            return False
    
    def unregister_hotkeys(self):
        """Отменить регистрацию всех горячих клавиш"""
        for hotkey in self._registered_hotkeys:
            try:
                keyboard.remove_hotkey(hotkey)
            except:
                pass
        self._registered_hotkeys = []
    
    def _on_toggle_overlay(self):
        """Обработчик переключения оверлея"""
        if self._enabled:
            self.toggle_overlay.emit()
    
    def _on_screenshot(self):
        """Обработчик скриншота"""
        if self._enabled:
            self.take_screenshot.emit()
    
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
