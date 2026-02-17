"""
Стили и темы для оверлея
"""

# Тёмная тема для PyQt6
DARK_THEME = """
QWidget {
    background-color: #1a1a2e;
    color: #eaeaea;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 14px;
}

QMainWindow {
    background-color: #1a1a2e;
}

/* Область чата */
QTextBrowser {
    background-color: #16213e;
    border: 1px solid #0f3460;
    border-radius: 8px;
    padding: 10px;
    color: #eaeaea;
    selection-background-color: #e94560;
}

QTextBrowser a {
    color: #4fc3f7;
}

/* Поле ввода */
QLineEdit {
    background-color: #16213e;
    border: 2px solid #0f3460;
    border-radius: 8px;
    padding: 12px 15px;
    color: #eaeaea;
    font-size: 14px;
}

QLineEdit:focus {
    border-color: #e94560;
}

QLineEdit::placeholder {
    color: #6c757d;
}

/* Кнопки */
QPushButton {
    background-color: #e94560;
    border: none;
    border-radius: 6px;
    padding: 10px 20px;
    color: white;
    font-weight: bold;
    font-size: 13px;
}

QPushButton:hover {
    background-color: #ff6b6b;
}

QPushButton:pressed {
    background-color: #c73e54;
}

QPushButton:disabled {
    background-color: #4a4a4a;
    color: #8a8a8a;
}

/* Кнопка отправки */
QPushButton#sendButton {
    background-color: #e94560;
    min-width: 80px;
}

/* Кнопка скриншота */
QPushButton#screenshotButton {
    background-color: #0f3460;
    min-width: 40px;
    padding: 10px;
}

QPushButton#screenshotButton:hover {
    background-color: #1a4a7a;
}

/* Кнопка очистки */
QPushButton#clearButton {
    background-color: transparent;
    color: #6c757d;
    font-size: 12px;
    padding: 5px 10px;
}

QPushButton#clearButton:hover {
    color: #e94560;
}

/* Метка контекста (название игры) */
QLabel#contextLabel {
    background-color: #0f3460;
    border-radius: 4px;
    padding: 5px 10px;
    color: #4fc3f7;
    font-size: 12px;
}

/* Заголовок */
QLabel#titleLabel {
    font-size: 18px;
    font-weight: bold;
    color: #e94560;
}

/* Скроллбар */
QScrollBar:vertical {
    background-color: #16213e;
    width: 10px;
    border-radius: 5px;
}

QScrollBar::handle:vertical {
    background-color: #0f3460;
    border-radius: 5px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: #e94560;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {
    background: none;
}

/* Статусбар */
QStatusBar {
    background-color: #0f3460;
    color: #6c757d;
    font-size: 11px;
}

/* Меню */
QMenu {
    background-color: #1a1a2e;
    border: 1px solid #0f3460;
    border-radius: 4px;
    padding: 5px;
}

QMenu::item {
    padding: 8px 25px;
    border-radius: 4px;
}

QMenu::item:selected {
    background-color: #e94560;
}

/* Системный трей меню */
QMenu::separator {
    height: 1px;
    background-color: #0f3460;
    margin: 5px 10px;
}

/* Tooltip */
QToolTip {
    background-color: #16213e;
    color: #eaeaea;
    border: 1px solid #0f3460;
    border-radius: 4px;
    padding: 5px;
}
"""

# CSS для отображения сообщений в чате (HTML)
CHAT_MESSAGE_CSS = """
<style>
    .message {
        margin: 10px 0;
        padding: 10px;
        border-radius: 8px;
        line-height: 1.5;
    }
    .user-message {
        background-color: #0f3460;
        margin-left: 20px;
    }
    .assistant-message {
        background-color: #1a1a2e;
        border-left: 3px solid #e94560;
    }
    .message-header {
        font-size: 12px;
        color: #6c757d;
        margin-bottom: 5px;
    }
    .message-content {
        color: #eaeaea;
    }
    .error-message {
        color: #ff6b6b;
    }
    img {
        max-width: 100%;
        border-radius: 8px;
        margin: 10px 0;
    }
    code {
        background-color: #0f3460;
        padding: 2px 6px;
        border-radius: 4px;
        font-family: 'Consolas', monospace;
    }
    pre {
        background-color: #0f3460;
        padding: 10px;
        border-radius: 8px;
        overflow-x: auto;
    }
    pre code {
        padding: 0;
        background: none;
    }
    a {
        color: #4fc3f7;
    }
    ul, ol {
        margin: 5px 0;
        padding-left: 20px;
    }
    li {
        margin: 3px 0;
    }
    blockquote {
        border-left: 3px solid #e94560;
        margin: 10px 0;
        padding-left: 15px;
        color: #aaa;
    }
</style>
"""
