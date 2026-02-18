"""
Главное окно оверлея
"""

import re
import sys
import os
from typing import Optional
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextBrowser, QLineEdit, QPushButton, QLabel,
    QApplication, QSizeGrip
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QUrl, QByteArray
from PyQt6.QtGui import QFont, QTextCursor, QDesktopServices, QPixmap

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from .styles import DARK_THEME, CHAT_MESSAGE_CSS
import config


class AIWorker(QThread):
    """Фоновый поток для запросов к AI"""
    response_ready = pyqtSignal(str)
    response_chunk = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, gpt_client, message: str, screenshot_context: str = ""):
        super().__init__()
        self.gpt_client = gpt_client
        self.message = message
        self.screenshot_context = screenshot_context
    
    def run(self):
        try:
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
    
    def __init__(self, gpt_client=None, context_detector=None):
        super().__init__()
        
        self.gpt_client = gpt_client
        self.context_detector = context_detector
        self._current_screenshot_context = ""
        self._current_screenshot_image: Optional[QPixmap] = None
        self._worker: Optional[AIWorker] = None
        self._chat_history_html = ""
        
        self._setup_window()
        self._setup_ui()
        self._apply_styles()
    
    def _setup_window(self):
        """Настройка окна"""
        self.setWindowTitle(config.APP_NAME)
        
        # Флаги окна: поверх всех, без рамки, как инструмент
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        
        # Прозрачность
        self.setWindowOpacity(config.OVERLAY_OPACITY)
        
        # Размеры
        self.resize(config.OVERLAY_WIDTH, config.OVERLAY_HEIGHT)
        
        # Позиционирование
        self._position_window()
    
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
        
        # Название
        title_label = QLabel(config.APP_NAME)
        title_label.setObjectName("titleLabel")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Контекст (игра/приложение)
        self.context_label = QLabel("Не определено")
        self.context_label.setObjectName("contextLabel")
        header_layout.addWidget(self.context_label)
        
        # Кнопка закрытия
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(30, 30)
        close_btn.clicked.connect(self.hide)
        header_layout.addWidget(close_btn)
        
        main_layout.addLayout(header_layout)
        
        # === Область чата ===
        self.chat_display = QTextBrowser()
        self.chat_display.setOpenExternalLinks(False)
        self.chat_display.anchorClicked.connect(self._handle_link_click)
        self.chat_display.setPlaceholderText("Задай вопрос...")
        main_layout.addWidget(self.chat_display, 1)
        
        # === Превью скриншота ===
        self.screenshot_preview_container = QWidget()
        screenshot_preview_layout = QVBoxLayout(self.screenshot_preview_container)
        screenshot_preview_layout.setContentsMargins(0, 5, 0, 5)
        screenshot_preview_layout.setSpacing(5)
        
        preview_header = QHBoxLayout()
        preview_label = QLabel("📷 Превью скриншота:")
        preview_label.setStyleSheet("color: #4fc3f7; font-size: 12px; font-weight: bold;")
        preview_header.addWidget(preview_label)
        
        remove_preview_btn = QPushButton("✕")
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
        self.screenshot_btn.setToolTip("Сделать скриншот (Ctrl+Shift+S)")
        self.screenshot_btn.clicked.connect(self._on_screenshot_click)
        input_layout.addWidget(self.screenshot_btn)
        
        # Поле ввода
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Введите вопрос...")
        self.input_field.returnPressed.connect(self._on_send_message)
        input_layout.addWidget(self.input_field, 1)
        
        # Кнопка отправки
        self.send_btn = QPushButton("Отправить")
        self.send_btn.setObjectName("sendButton")
        self.send_btn.clicked.connect(self._on_send_message)
        input_layout.addWidget(self.send_btn)
        
        main_layout.addLayout(input_layout)
        
        # === Нижняя панель ===
        footer_layout = QHBoxLayout()
        
        # Кнопка очистки
        clear_btn = QPushButton("Очистить чат")
        clear_btn.setObjectName("clearButton")
        clear_btn.clicked.connect(self._clear_chat)
        footer_layout.addWidget(clear_btn)
        
        footer_layout.addStretch()
        
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
        """Обработка клика по ссылке"""
        QDesktopServices.openUrl(url)
    
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
        
        # Обновляем контекст
        self._update_context()
        
        # Блокируем UI
        self._set_input_enabled(False)
        
        # Запускаем запрос в фоне
        if self.gpt_client:
            self._worker = AIWorker(
                self.gpt_client,
                text,
                self._current_screenshot_context
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
            # Создаём превью
            pixmap = QPixmap()
            pixmap.loadFromData(QByteArray(image_data))
            
            # Скейлим до разумного размера
            if pixmap.width() > 400:
                pixmap = pixmap.scaledToWidth(400, Qt.TransformationMode.SmoothTransformation)
            
            self._current_screenshot_image = pixmap
            self.screenshot_preview.setPixmap(pixmap)
            self.screenshot_preview_container.show()
            self.screenshot_indicator.setText("📷 Скриншот прикреплён")
        else:
            self._remove_screenshot()
    
    def _remove_screenshot(self):
        """Удалить скриншот"""
        self._current_screenshot_context = ""
        self._current_screenshot_image = None
        self.screenshot_preview.clear()
        self.screenshot_preview_container.hide()
        self.screenshot_indicator.setText("")
    
    def _update_context(self):
        """Обновить контекст (игра/приложение)"""
        if self.context_detector:
            context = self.context_detector.get_active_window_context()
            if context:
                self.context_label.setText(f"{context.app_name}")
                
                # Обновляем системный промпт
                if self.gpt_client:
                    game_name = context.app_name if context.app_type == "game" else None
                    self.gpt_client.update_context(game_name=game_name)
            else:
                self.context_label.setText("Не определено")
    
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
            self._update_context()
            self.show()
            self.activateWindow()
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
