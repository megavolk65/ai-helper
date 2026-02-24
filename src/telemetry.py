"""
Телеметрия — анонимный ping при запуске (раз в сутки).
Данные отправляются на Google Apps Script webhook.
"""

import json
import os
import uuid
import threading
from datetime import date
from urllib.request import Request, urlopen
from urllib.error import URLError

import config

SETTINGS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "settings.json")


def _load_settings() -> dict:
    """Загрузить settings.json"""
    try:
        with open(SETTINGS_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def _save_settings(settings: dict):
    """Сохранить settings.json"""
    try:
        with open(SETTINGS_PATH, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _get_or_create_user_id() -> tuple[str, bool]:
    """
    Получить или создать анонимный ID пользователя.
    Возвращает (user_id, is_new) — is_new=True если ID только что создан.
    """
    settings = _load_settings()
    
    existing_id = settings.get("telemetry_id")
    if existing_id:
        return existing_id, False
    
    new_id = str(uuid.uuid4())
    settings["telemetry_id"] = new_id
    _save_settings(settings)
    return new_id, True


def _should_ping_today() -> bool:
    """Проверить, был ли уже ping сегодня"""
    settings = _load_settings()
    last_date = settings.get("last_telemetry_date", "")
    return last_date != date.today().isoformat()


def _mark_ping_sent():
    """Отметить что ping отправлен сегодня"""
    settings = _load_settings()
    settings["last_telemetry_date"] = date.today().isoformat()
    _save_settings(settings)


def _do_ping():
    """Отправить ping на webhook (вызывается в фоновом потоке)"""
    try:
        webhook_url = getattr(config, 'TELEMETRY_WEBHOOK_URL', '')
        if not webhook_url:
            return
        
        user_id, is_new = _get_or_create_user_id()
        
        payload = json.dumps({
            "user_id": user_id,
            "version": config.APP_VERSION,
            "first_launch": is_new,
        }).encode('utf-8')
        
        req = Request(
            webhook_url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        
        urlopen(req, timeout=10)
        
        # Отправка успешна — запоминаем дату
        _mark_ping_sent()
        
    except Exception:
        # Молча игнорируем любые ошибки — телеметрия не должна мешать работе
        pass


def send_startup_ping():
    """
    Отправить ping при запуске (раз в сутки, в фоновом потоке).
    Безопасно вызывать из любого места — ошибки подавляются.
    """
    try:
        if not _should_ping_today():
            return
        
        thread = threading.Thread(target=_do_ping, daemon=True)
        thread.start()
    except Exception:
        pass
