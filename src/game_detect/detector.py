"""
Context Detector - определяет активное окно и тип приложения
"""

import win32gui
import win32process
import psutil
from dataclasses import dataclass
from typing import Optional, List


@dataclass
class AppContext:
    """Контекст текущего приложения"""
    window_title: str
    process_name: str
    app_name: str
    app_type: str  # "game", "browser", "ide", "other"
    

# Маппинг известных процессов на понятные названия и типы
KNOWN_APPS = {
    # Игры
    "eldenring.exe": ("Elden Ring", "game"),
    "darksoulsiii.exe": ("Dark Souls III", "game"),
    "sekiro.exe": ("Sekiro: Shadows Die Twice", "game"),
    "witcher3.exe": ("The Witcher 3", "game"),
    "cyberpunk2077.exe": ("Cyberpunk 2077", "game"),
    "baldursgate3.exe": ("Baldur's Gate 3", "game"),
    "bg3.exe": ("Baldur's Gate 3", "game"),
    "starfield.exe": ("Starfield", "game"),
    "gta5.exe": ("GTA V", "game"),
    "rdr2.exe": ("Red Dead Redemption 2", "game"),
    "hogwartslegacy.exe": ("Hogwarts Legacy", "game"),
    "diablo iv.exe": ("Diablo IV", "game"),
    "poe.exe": ("Path of Exile", "game"),
    "pathofexile.exe": ("Path of Exile", "game"),
    "wow.exe": ("World of Warcraft", "game"),
    "dota2.exe": ("Dota 2", "game"),
    "cs2.exe": ("Counter-Strike 2", "game"),
    "csgo.exe": ("CS:GO", "game"),
    "valorant.exe": ("Valorant", "game"),
    "leagueoflegends.exe": ("League of Legends", "game"),
    "overwatch.exe": ("Overwatch 2", "game"),
    "minecraft.exe": ("Minecraft", "game"),
    "javaw.exe": ("Minecraft", "game"),  # Minecraft Java
    "terraria.exe": ("Terraria", "game"),
    "factorio.exe": ("Factorio", "game"),
    "stellaris.exe": ("Stellaris", "game"),
    "eu4.exe": ("Europa Universalis IV", "game"),
    "ck3.exe": ("Crusader Kings III", "game"),
    "hoi4.exe": ("Hearts of Iron IV", "game"),
    "cities.exe": ("Cities: Skylines", "game"),
    "subnautica.exe": ("Subnautica", "game"),
    "satisfactory.exe": ("Satisfactory", "game"),
    "palworld.exe": ("Palworld", "game"),
    "enshrouded.exe": ("Enshrouded", "game"),
    "lethalcompany.exe": ("Lethal Company", "game"),
    
    # Steam
    "steam.exe": ("Steam", "other"),
    "steamwebhelper.exe": ("Steam", "other"),
    
    # Браузеры
    "chrome.exe": ("Google Chrome", "browser"),
    "firefox.exe": ("Firefox", "browser"),
    "msedge.exe": ("Microsoft Edge", "browser"),
    "opera.exe": ("Opera", "browser"),
    "brave.exe": ("Brave", "browser"),
    "yandex.exe": ("Яндекс Браузер", "browser"),
    
    # IDE
    "code.exe": ("VS Code", "ide"),
    "devenv.exe": ("Visual Studio", "ide"),
    "idea64.exe": ("IntelliJ IDEA", "ide"),
    "pycharm64.exe": ("PyCharm", "ide"),
    "webstorm64.exe": ("WebStorm", "ide"),
    "rider64.exe": ("Rider", "ide"),
    "sublime_text.exe": ("Sublime Text", "ide"),
    "notepad++.exe": ("Notepad++", "ide"),
    
    # Коммуникации
    "discord.exe": ("Discord", "other"),
    "telegram.exe": ("Telegram", "other"),
    "slack.exe": ("Slack", "other"),
    
    # Медиа
    "spotify.exe": ("Spotify", "other"),
    "vlc.exe": ("VLC", "other"),
}


class ContextDetector:
    """Определяет контекст активного окна"""
    
    # Заголовки окон, которые нужно игнорировать
    IGNORED_TITLES = ["AI Helper", "AI-Helper", "Настройки"]
    
    def __init__(self):
        self._last_context: Optional[AppContext] = None
    
    def _get_all_windows(self) -> List[tuple]:
        """Получить список всех видимых окон"""
        windows = []
        
        def enum_callback(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title:
                    windows.append((hwnd, title))
            return True
        
        win32gui.EnumWindows(enum_callback, None)
        return windows
    
    def get_active_window_context(self) -> Optional[AppContext]:
        """Получить контекст активного окна (игнорируя AI Helper)"""
        try:
            # Получаем handle активного окна
            hwnd = win32gui.GetForegroundWindow()
            if not hwnd:
                return self._last_context
            
            # Получаем заголовок окна
            window_title = win32gui.GetWindowText(hwnd)
            
            # Если это наше окно - возвращаем последний контекст
            if any(ignored in window_title for ignored in self.IGNORED_TITLES):
                return self._last_context
            
            if not window_title:
                return self._last_context
            
            # Получаем PID процесса
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            
            # Получаем имя процесса
            try:
                process = psutil.Process(pid)
                process_name = process.name().lower()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                process_name = "unknown"
            
            # Определяем приложение
            app_name, app_type = self._identify_app(process_name, window_title)
            
            context = AppContext(
                window_title=window_title,
                process_name=process_name,
                app_name=app_name,
                app_type=app_type
            )
            
            self._last_context = context
            return context
            
        except Exception:
            return self._last_context
    
    def _identify_app(self, process_name: str, window_title: str) -> tuple[str, str]:
        """Определить приложение по имени процесса и заголовку окна"""
        
        # Проверяем известные процессы
        if process_name in KNOWN_APPS:
            return KNOWN_APPS[process_name]
        
        # Эвристика для игр (полноэкранные приложения обычно игры)
        # Проверяем по заголовку окна
        title_lower = window_title.lower()
        
        # Проверяем наличие названий известных игр в заголовке
        game_keywords = [
            "elden ring", "dark souls", "sekiro", "witcher", "cyberpunk",
            "baldur", "starfield", "diablo", "warcraft", "dota", "counter-strike",
            "valorant", "league of legends", "overwatch", "minecraft", "terraria",
            "factorio", "stellaris", "europa universalis", "crusader kings",
            "hearts of iron", "cities", "subnautica", "satisfactory", "palworld"
        ]
        
        for keyword in game_keywords:
            if keyword in title_lower:
                return (window_title.split(" - ")[0].strip(), "game")
        
        # Браузеры часто имеют URL или название сайта в заголовке
        browser_indicators = ["- google chrome", "- mozilla firefox", "- microsoft edge", "- opera", "- brave"]
        for indicator in browser_indicators:
            if indicator in title_lower:
                return (window_title, "browser")
        
        # IDE обычно показывают путь к файлу
        if any(x in title_lower for x in [".py", ".js", ".ts", ".cpp", ".java", ".cs", "visual studio"]):
            return (window_title.split(" - ")[-1].strip() if " - " in window_title else window_title, "ide")
        
        # По умолчанию - просто используем заголовок окна
        return (window_title, "other")
    
    def get_context_for_prompt(self) -> str:
        """Получить строку контекста для системного промпта"""
        context = self.get_active_window_context()
        
        if not context:
            return ""
        
        if context.app_type == "game":
            return f"Текущая игра: {context.app_name}"
        elif context.app_type == "browser":
            return f"Пользователь в браузере: {context.app_name}"
        elif context.app_type == "ide":
            return f"Пользователь в IDE: {context.app_name}"
        else:
            return f"Текущее приложение: {context.app_name}"
    
    def is_game_active(self) -> bool:
        """Проверить, активна ли игра"""
        context = self.get_active_window_context()
        return context is not None and context.app_type == "game"
    
    def get_game_name(self) -> Optional[str]:
        """Получить название игры, если активна"""
        context = self.get_active_window_context()
        if context and context.app_type == "game":
            return context.app_name
        return None
