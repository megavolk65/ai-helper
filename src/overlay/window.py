"""
Главное окно оверлея
"""

import re
import sys
import os
import ctypes
from typing import Optional
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextBrowser, QLineEdit, QPushButton, QLabel,
    QApplication, QSizeGrip, QComboBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QUrl, QByteArray, QTimer
import json
from PyQt6.QtGui import QFont, QTextCursor, QDesktopServices, QPixmap

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from .styles import DARK_THEME, CHAT_MESSAGE_CSS
from .settings_dialog import SettingsDialog
from .web_dialog import WebDialog
import config

from src.localization import Localization, t


class AIWorker(QThread):
    """Фоновый поток для запросов к AI"""
    response_ready = pyqtSignal(str)
    response_chunk = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, gpt_client, message: str, screenshot_context: str = "", image_data: bytes = None):
        super().__init__()
        self.gpt_client = gpt_client
        self.message = message
        self.screenshot_context = screenshot_context
        self.image_data = image_data
    
    def run(self):
        try:
            # Если есть изображение - используем send_request
            if self.image_data:
                response = self.gpt_client.send_request(
                    self.message,
                    image_data=self.image_data
                )
            else:
                # Иначе обычный текстовый запрос
                response = self.gpt_client.send_message(
                    self.message,
                    screenshot_context=self.screenshot_context
                )
            self.response_ready.emit(response)
        except Exception as e:
            self.error_occurred.emit(str(e))


class OverlayWindow(QMainWindow):
    """Главное окно оверлея"""
    
    # Сигналы
    screenshot_requested = pyqtSignal()
    hide_requested = pyqtSignal()
    hotkeys_changed = pyqtSignal(str, str)  # hotkey_overlay, hotkey_screenshot
    autostart_changed = pyqtSignal(bool)  # Изменение автозапуска
    
    def __init__(self, gpt_client=None, context_detector=None):
        super().__init__()
        
        self.gpt_client = gpt_client
        self.context_detector = context_detector
        self._current_screenshot_context = ""
        self._current_screenshot_image: Optional[QPixmap] = None
        self._current_screenshot_bytes: Optional[bytes] = None  # Байты изображения
        self._worker: Optional[AIWorker] = None
        self._chat_history_html = ""
        self.autostart_checker = None  # Функция для проверки состояния автозапуска
        
        # Загружаем язык из настроек
        self._load_language()
        
        self._setup_window()
        self._setup_ui()
        self._apply_styles()
        self._update_context()  # Устанавливаем контекст один раз при старте
        
        # Подписываемся на смену языка
        Localization.add_listener(self._update_ui_texts)
    
    def _setup_window(self):
        """Настройка окна"""
        self.setWindowTitle(t("app_name"))
        
        # Флаги окна для работы поверх полноэкранных игр
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        
        # Атрибуты для оверлея
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, False)  # Активируем окно
        
        # Прозрачность
        self.setWindowOpacity(config.OVERLAY_OPACITY)
        
        # Применяем Windows-специфичные флаги после показа окна
        self._apply_windows_overlay_flags()
        
        # Размеры
        self.resize(config.OVERLAY_WIDTH, config.OVERLAY_HEIGHT)
        
        # Позиционирование
        self._position_window()
    
    def _apply_windows_overlay_flags(self):
        """Применить Windows-специфичные флаги для работы поверх игр"""
        try:
            import ctypes
            from ctypes import wintypes
            
            # Константы Windows API
            GWL_EXSTYLE = -20
            WS_EX_TOPMOST = 0x00000008
            WS_EX_LAYERED = 0x00080000
            WS_EX_TRANSPARENT = 0x00000020
            HWND_TOPMOST = -1
            SWP_NOMOVE = 0x0002
            SWP_NOSIZE = 0x0001
            SWP_NOACTIVATE = 0x0010
            
            # Получаем HWND окна
            hwnd = int(self.winId())
            
            # Получаем текущие флаги
            user32 = ctypes.windll.user32
            ex_style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            
            # Добавляем флаги для оверлея
            ex_style |= WS_EX_LAYERED | WS_EX_TOPMOST
            user32.SetWindowLongW(hwnd, GWL_EXSTYLE, ex_style)
            
            # Устанавливаем окно поверх всех
            user32.SetWindowPos(
                hwnd, HWND_TOPMOST,
                0, 0, 0, 0,
                SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE
            )
            
        except Exception as e:
            print(f"Warning: Failed to apply Windows overlay flags: {e}")
    
    def _force_focus_from_game(self):
        """Принудительно забрать фокус у игры через AttachThreadInput"""
        try:
            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32
            
            # Получаем HWND нашего окна
            our_hwnd = int(self.winId())
            
            # Получаем HWND окна на переднем плане (игра)
            foreground_hwnd = user32.GetForegroundWindow()
            
            if foreground_hwnd == 0 or foreground_hwnd == our_hwnd:
                # Если мы уже в фокусе или нет окна на переднем плане
                return
            
            # Получаем ID потоков
            foreground_thread = user32.GetWindowThreadProcessId(foreground_hwnd, None)
            our_thread = kernel32.GetCurrentThreadId()
            
            if foreground_thread == 0 or our_thread == 0:
                return
            
            # Подключаемся к потоку ввода игры
            user32.AttachThreadInput(foreground_thread, our_thread, True)
            
            try:
                # Забираем фокус
                user32.SetForegroundWindow(our_hwnd)
                user32.SetFocus(our_hwnd)
                self.activateWindow()
                self.raise_()
            finally:
                # Отключаемся от потока ввода
                user32.AttachThreadInput(foreground_thread, our_thread, False)
            
        except Exception as e:
            print(f"Warning: Failed to force focus: {e}")
            # Fallback на стандартные методы
            self.activateWindow()
            self.raise_()
    
    def _position_window(self):
        """Позиционирование окна на экране"""
        screen = QApplication.primaryScreen()
        if not screen:
            return
        
        screen_geometry = screen.availableGeometry()
        
        if config.OVERLAY_POSITION == "center":
            x = (screen_geometry.width() - self.width()) // 2
            y = (screen_geometry.height() - self.height()) // 2
        elif config.OVERLAY_POSITION == "top-right":
            x = screen_geometry.width() - self.width() - 20
            y = 20
        elif config.OVERLAY_POSITION == "bottom-right":
            x = screen_geometry.width() - self.width() - 20
            y = screen_geometry.height() - self.height() - 20
        else:
            x = (screen_geometry.width() - self.width()) // 2
            y = (screen_geometry.height() - self.height()) // 2
        
        self.move(x, y)
    
    def _setup_ui(self):
        """Создание UI"""
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Основной layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)
        
        # === Заголовок ===
        header_layout = QHBoxLayout()
        
        # Кнопка переключения языка
        self.lang_btn = QPushButton()
        self.lang_btn.setObjectName("langButton")
        self.lang_btn.setFixedSize(50, 24)
        self.lang_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.lang_btn.clicked.connect(self._toggle_language)
        self._update_lang_button()
        header_layout.addWidget(self.lang_btn)
        
        # Название
        self.title_label = QLabel(t("app_name"))
        self.title_label.setObjectName("titleLabel")
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch()
        
        # Кнопка обновления контекста
        self.refresh_context_btn = QPushButton("↻")
        self.refresh_context_btn.setObjectName("refreshContextButton")
        self.refresh_context_btn.setFixedSize(28, 28)
        self.refresh_context_btn.setToolTip(t("refresh_context"))
        self.refresh_context_btn.clicked.connect(self._update_context)
        header_layout.addWidget(self.refresh_context_btn)
        
        # Контекст (игра/приложение)
        self.context_label = QLabel(t("not_detected"))
        self.context_label.setObjectName("contextLabel")
        header_layout.addWidget(self.context_label)
        
        # Кнопка закрытия
        self.close_btn = QPushButton("X")
        self.close_btn.setObjectName("closeButton")
        self.close_btn.setFixedSize(30, 30)
        self.close_btn.clicked.connect(self.hide)
        header_layout.addWidget(self.close_btn)
        
        main_layout.addLayout(header_layout)
        
        # === Область чата ===
        self.chat_display = QTextBrowser()
        self.chat_display.setOpenExternalLinks(False)
        self.chat_display.setOpenLinks(False)  # Предотвращаем сброс содержимого при клике
        self.chat_display.anchorClicked.connect(self._handle_link_click)
        self.chat_display.setPlaceholderText(t("ask_question"))
        main_layout.addWidget(self.chat_display, 1)
        
        # === Превью скриншота ===
        self.screenshot_preview_container = QWidget()
        screenshot_preview_layout = QVBoxLayout(self.screenshot_preview_container)
        screenshot_preview_layout.setContentsMargins(0, 5, 0, 5)
        screenshot_preview_layout.setSpacing(5)
        
        preview_header = QHBoxLayout()
        self.preview_label = QLabel(t("screenshot_preview"))
        self.preview_label.setStyleSheet("color: #4fc3f7; font-size: 12px; font-weight: bold;")
        preview_header.addWidget(self.preview_label)
        
        remove_preview_btn = QPushButton("X")
        remove_preview_btn.setFixedSize(20, 20)
        remove_preview_btn.setObjectName("removePreviewButton")
        remove_preview_btn.clicked.connect(self._remove_screenshot)
        preview_header.addWidget(remove_preview_btn)
        preview_header.addStretch()
        
        screenshot_preview_layout.addLayout(preview_header)
        
        self.screenshot_preview = QLabel()
        self.screenshot_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.screenshot_preview.setStyleSheet("""
            QLabel {
                background-color: #263238;
                border: 2px solid #37474f;
                border-radius: 4px;
                padding: 5px;
            }
        """)
        self.screenshot_preview.setMaximumHeight(150)
        self.screenshot_preview.setScaledContents(False)
        screenshot_preview_layout.addWidget(self.screenshot_preview)
        
        self.screenshot_preview_container.hide()
        main_layout.addWidget(self.screenshot_preview_container)
        
        # === Панель ввода ===
        input_layout = QHBoxLayout()
        input_layout.setSpacing(8)
        
        # Кнопка скриншота
        self.screenshot_btn = QPushButton("📷")
        self.screenshot_btn.setObjectName("screenshotButton")
        self.screenshot_btn.setToolTip(t("take_screenshot"))
        self.screenshot_btn.clicked.connect(self._on_screenshot_click)
        input_layout.addWidget(self.screenshot_btn)
        
        # Поле ввода
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText(t("enter_question"))
        self.input_field.returnPressed.connect(self._on_send_message)
        input_layout.addWidget(self.input_field, 1)
        
        # Кнопка отправки
        self.send_btn = QPushButton(t("send"))
        self.send_btn.setObjectName("sendButton")
        self.send_btn.clicked.connect(self._on_send_message)
        input_layout.addWidget(self.send_btn)
        
        main_layout.addLayout(input_layout)
        
        # === Нижняя панель ===
        footer_layout = QHBoxLayout()
        
        # Кнопка очистки
        self.clear_btn = QPushButton(t("clear_chat"))
        self.clear_btn.setObjectName("clearButton")
        self.clear_btn.clicked.connect(self._clear_chat)
        footer_layout.addWidget(self.clear_btn)
        
        footer_layout.addStretch()
        
        # Выбор модели
        self.model_label = QLabel(t("model"))
        self.model_label.setStyleSheet("color: #6c757d; font-size: 12px;")
        footer_layout.addWidget(self.model_label)
        
        self.model_combo = QComboBox()
        self.model_combo.setObjectName("modelCombo")
        self.model_combo.setMinimumWidth(200)
        self._populate_models()
        self.model_combo.currentIndexChanged.connect(self._on_model_changed)
        footer_layout.addWidget(self.model_combo)
        
        # Кнопка настроек
        self.settings_btn = QPushButton("⚙")
        self.settings_btn.setObjectName("settingsButton")
        self.settings_btn.setFixedSize(30, 30)
        self.settings_btn.setToolTip(t("settings"))
        self.settings_btn.clicked.connect(self._open_settings)
        footer_layout.addWidget(self.settings_btn)
        
        # Индикатор скриншота
        self.screenshot_indicator = QLabel("")
        self.screenshot_indicator.setStyleSheet("color: #4fc3f7; font-size: 12px;")
        footer_layout.addWidget(self.screenshot_indicator)
        
        # Грип для изменения размера
        size_grip = QSizeGrip(self)
        footer_layout.addWidget(size_grip)
        
        main_layout.addLayout(footer_layout)
    
    def _apply_styles(self):
        """Применение стилей"""
        self.setStyleSheet(DARK_THEME)
        
        # Инициализация чата с CSS
        self._update_chat_display()
    
    def _update_chat_display(self):
        """Обновить отображение чата"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            {CHAT_MESSAGE_CSS}
        </head>
        <body>
            {self._chat_history_html}
        </body>
        </html>
        """
        self.chat_display.setHtml(html)
        
        # Прокрутка вниз
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.chat_display.setTextCursor(cursor)
    
    def _add_message(self, role: str, text: str):
        """Добавить сообщение в чат"""
        # Конвертируем markdown в HTML
        html_text = self._markdown_to_html(text)
        
        if role == "user":
            message_html = f'''
            <div class="message user-message">
                <div class="message-header">Вы</div>
                <div class="message-content">{html_text}</div>
            </div>
            '''
        else:
            message_html = f'''
            <div class="message assistant-message">
                <div class="message-header">AI Helper</div>
                <div class="message-content">{html_text}</div>
            </div>
            '''
        
        self._chat_history_html += message_html
        self._update_chat_display()
    
    def _markdown_to_html(self, text: str) -> str:
        """Простая конвертация markdown в HTML"""
        # Экранируем HTML
        text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        
        # Изображения ![alt](url)
        text = re.sub(
            r'!\[([^\]]*)\]\(([^)]+)\)',
            r'<img src="\2" alt="\1" />',
            text
        )
        
        # Ссылки [text](url)
        text = re.sub(
            r'\[([^\]]+)\]\(([^)]+)\)',
            r'<a href="\2">\1</a>',
            text
        )
        
        # Жирный текст **text**
        text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
        
        # Курсив *text*
        text = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', text)
        
        # Код ```code```
        text = re.sub(
            r'```(\w*)\n?([\s\S]*?)```',
            r'<pre><code>\2</code></pre>',
            text
        )
        
        # Инлайн код `code`
        text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
        
        # Переносы строк
        text = text.replace("\n", "<br>")
        
        return text
    
    def _handle_link_click(self, url: QUrl):
        """Обработка клика по ссылке - открыть во встроенном браузере"""
        url_str = url.toString()
        dialog = WebDialog(self, url_str)
        dialog.exec()
    
    def _on_send_message(self):
        """Отправка сообщения"""
        text = self.input_field.text().strip()
        if not text:
            return
        
        # Очищаем поле ввода
        self.input_field.clear()
        
        # Показываем сообщение пользователя
        display_text = text
        if self._current_screenshot_context:
            display_text = f"📷 [Со скриншотом]\n{text}"
        self._add_message("user", display_text)
        
        # Блокируем UI
        self._set_input_enabled(False)
        
        # Запускаем запрос в фоне
        if self.gpt_client:
            self._worker = AIWorker(
                self.gpt_client,
                text,
                self._current_screenshot_context,
                self._current_screenshot_bytes  # Передаём байты изображения
            )
            self._worker.response_ready.connect(self._on_response)
            self._worker.error_occurred.connect(self._on_error)
            self._worker.start()
        else:
            self._add_message("assistant", "❌ AI клиент не инициализирован. Проверьте config.py")
            self._set_input_enabled(True)
        
        # Сбрасываем контекст скриншота
        self._remove_screenshot()
    
    def _on_response(self, response: str):
        """Получен ответ от AI"""
        self._add_message("assistant", response)
        self._set_input_enabled(True)
    
    def _on_error(self, error: str):
        """Произошла ошибка"""
        self._add_message("assistant", f"❌ Ошибка: {error}")
        self._set_input_enabled(True)
    
    def _set_input_enabled(self, enabled: bool):
        """Включить/выключить UI"""
        self.input_field.setEnabled(enabled)
        self.send_btn.setEnabled(enabled)
        self.screenshot_btn.setEnabled(enabled)
        
        if not enabled:
            self.send_btn.setText("⏳")
        else:
            self.send_btn.setText("Отправить")
    
    def _on_screenshot_click(self):
        """Клик по кнопке скриншота"""
        self.screenshot_requested.emit()
    
    def set_screenshot_context(self, context: str, image_data: bytes = None):
        """Установить контекст скриншота"""
        self._current_screenshot_context = context
        
        if context and image_data:
            # Сохраняем байты изображения
            self._current_screenshot_bytes = image_data
            
            # Создаём превью
            pixmap = QPixmap()
            pixmap.loadFromData(QByteArray(image_data))
            
            # Скейлим до разумного размера
            if pixmap.width() > 400:
                pixmap = pixmap.scaledToWidth(400, Qt.TransformationMode.SmoothTransformation)
            
            self._current_screenshot_image = pixmap
            self.screenshot_preview.setPixmap(pixmap)
            self.screenshot_preview_container.show()
            self.screenshot_indicator.setText(t("screenshot_attached"))
        else:
            self._remove_screenshot()
    
    def _remove_screenshot(self):
        """Удалить скриншот"""
        self._current_screenshot_context = ""
        self._current_screenshot_image = None
        self._current_screenshot_bytes = None
        self.screenshot_preview.clear()
        self.screenshot_preview_container.hide()
        self.screenshot_indicator.setText("")
    
    def _update_context(self):
        """Обновить контекст (игра/приложение)"""
        if not self.context_detector:
            return
        
        # Если окно видимо - скрываем, определяем контекст, показываем
        if self.isVisible():
            self.hide()
            QTimer.singleShot(150, self._do_update_context)
        else:
            self._do_update_context()
    
    def _do_update_context(self):
        """Фактически обновить контекст"""
        context = self.context_detector.get_active_window_context()
        if context:
            self.context_label.setText(f"{context.app_name}")
            
            # Обновляем системный промпт
            if self.gpt_client:
                game_name = context.app_name if context.app_type == "game" else None
                self.gpt_client.update_context(game_name=game_name)
        else:
            self.context_label.setText(t("not_detected"))
        
        # Показываем окно обратно
        if not self.isVisible():
            self.show()
            self._force_focus_from_game()
            self.input_field.setFocus()
    
    def _clear_chat(self):
        """Очистить чат"""
        self._chat_history_html = ""
        self._update_chat_display()
        
        if self.gpt_client:
            self.gpt_client.clear_history()
            self._update_context()  # Восстанавливаем системный промпт
    
    def toggle_visibility(self):
        """Переключить видимость окна"""
        if self.isVisible():
            self.hide()
        else:
            self.show()
            
            # Принудительно забираем фокус у игры
            self._force_focus_from_game()
            
            # Устанавливаем фокус на поле ввода
            self.input_field.setFocus()
    
    def keyPressEvent(self, event):
        """Обработка нажатий клавиш"""
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
        else:
            super().keyPressEvent(event)
    
    # === Перетаскивание окна ===
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and hasattr(self, '_drag_pos'):
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
    
    # === Выбор модели ===
    
    def _get_settings_path(self):
        """Получить путь к файлу настроек"""
        return os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "settings.json")
    
    def _load_settings(self):
        """Загрузить настройки"""
        try:
            with open(self._get_settings_path(), 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    
    def _save_settings(self, settings):
        """Сохранить настройки"""
        try:
            with open(self._get_settings_path(), 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2)
        except:
            pass
    
    def _get_models_list(self):
        """Получить список моделей (из settings или config)"""
        settings = self._load_settings()
        models = settings.get("models", [])
        
        # Если в настройках пусто - используем дефолтные из config
        if not models:
            models = getattr(config, 'OPENROUTER_MODELS', [])
        
        return models
    
    def _populate_models(self):
        """Заполнить список моделей"""
        models = self._get_models_list()
        
        # Загружаем сохранённую модель
        settings = self._load_settings()
        saved_model = settings.get("selected_model", "")
        
        for model_id, display_name in models:
            self.model_combo.addItem(display_name, model_id)
        
        # Устанавливаем сохранённую модель
        if saved_model:
            for i in range(self.model_combo.count()):
                if self.model_combo.itemData(i) == saved_model:
                    self.model_combo.setCurrentIndex(i)
                    if self.gpt_client:
                        self.gpt_client.set_model(saved_model)
                    break
    
    def _refresh_models_combo(self):
        """Обновить комбобокс моделей"""
        # Сохраняем текущую модель
        current_model = self.model_combo.currentData()
        
        # Очищаем и заполняем заново
        self.model_combo.clear()
        models = self._get_models_list()
        
        for model_id, display_name in models:
            self.model_combo.addItem(display_name, model_id)
        
        # Восстанавливаем выбор
        if current_model:
            for i in range(self.model_combo.count()):
                if self.model_combo.itemData(i) == current_model:
                    self.model_combo.setCurrentIndex(i)
                    break
    
    def _on_model_changed(self, index: int):
        """Обработчик смены модели"""
        if index < 0:
            return
        
        model_id = self.model_combo.itemData(index)
        if model_id and self.gpt_client:
            self.gpt_client.set_model(model_id)
            # Сохраняем выбор
            settings = self._load_settings()
            settings["selected_model"] = model_id
            self._save_settings(settings)
    
    def _open_settings(self):
        """Открыть диалог настроек"""
        current_settings = self._load_settings()
        
        # Добавляем текущие горячие клавиши из config если их нет в settings
        if "hotkey_overlay" not in current_settings:
            current_settings["hotkey_overlay"] = getattr(config, 'HOTKEY_TOGGLE_OVERLAY', 'Insert')
        if "hotkey_screenshot" not in current_settings:
            current_settings["hotkey_screenshot"] = getattr(config, 'HOTKEY_SCREENSHOT', 'Home')
        if "api_key" not in current_settings:
            current_settings["api_key"] = getattr(config, 'OPENROUTER_API_KEY', '')
        
        # Добавляем текущие модели
        if "models" not in current_settings:
            current_settings["models"] = getattr(config, 'OPENROUTER_MODELS', [])
        
        # Добавляем текущее состояние автозапуска
        if self.autostart_checker:
            current_settings["autostart"] = self.autostart_checker()
        
        dialog = SettingsDialog(self, current_settings)
        dialog.settings_saved.connect(self._on_settings_saved)
        dialog.exec()
    
    def _on_settings_saved(self, new_settings: dict):
        """Обработчик сохранения настроек"""
        self._save_settings(new_settings)
        
        # Обновляем API ключ в клиенте
        if self.gpt_client and "api_key" in new_settings:
            api_key = new_settings["api_key"]
            if api_key:
                self.gpt_client.api_key = api_key
        
        # Обновляем список моделей
        if "models" in new_settings:
            self._refresh_models_combo()
        
        # Обновляем горячие клавиши
        hotkey_overlay = new_settings.get("hotkey_overlay", "Insert")
        hotkey_screenshot = new_settings.get("hotkey_screenshot", "Home")
        self.hotkeys_changed.emit(hotkey_overlay, hotkey_screenshot)
        
        # Обновляем автозапуск
        if "autostart" in new_settings:
            self.autostart_changed.emit(new_settings["autostart"])
    
    # === Локализация ===
    
    def _load_language(self):
        """Загрузить язык из настроек"""
        settings = self._load_settings()
        lang = settings.get("language", "ru")
        Localization.set_language(lang)
    
    def _toggle_language(self):
        """Переключить язык"""
        Localization.toggle_language()
        self._update_lang_button()
        
        # Сохраняем выбор
        settings = self._load_settings()
        settings["language"] = Localization.get_language()
        self._save_settings(settings)
    
    def _update_lang_button(self):
        """Обновить текст кнопки языка"""
        lang = Localization.get_language()
        if lang == "ru":
            self.lang_btn.setText("RU|en")
        else:
            self.lang_btn.setText("ru|EN")
    
    def _update_ui_texts(self):
        """Обновить все тексты UI при смене языка"""
        self._update_lang_button()
        
        # Обновляем название
        self.title_label.setText(t("app_name"))
        self.setWindowTitle(t("app_name"))
        
        # Обновляем тексты
        self.refresh_context_btn.setToolTip(t("refresh_context"))
        self.chat_display.setPlaceholderText(t("ask_question"))
        self.preview_label.setText(t("screenshot_preview"))
        self.screenshot_btn.setToolTip(t("take_screenshot"))
        self.input_field.setPlaceholderText(t("enter_question"))
        self.send_btn.setText(t("send"))
        self.clear_btn.setText(t("clear_chat"))
        self.model_label.setText(t("model"))
        self.settings_btn.setToolTip(t("settings"))
        
        # Обновляем контекст если не определён
        if self.context_label.text() in ("Не определено", "Not detected"):
            self.context_label.setText(t("not_detected"))
        
        # Обновляем индикатор скриншота
        if self._current_screenshot_bytes:
            self.screenshot_indicator.setText(t("screenshot_attached"))
