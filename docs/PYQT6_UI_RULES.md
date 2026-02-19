# PyQt6 UI Rules - Правила отображения элементов

## Кнопки с текстом/иконками

### ❌ НЕ работает:
```python
# Unicode символы часто не отображаются
QPushButton("−")  # Unicode minus
QPushButton("✕")  # Unicode X
QPushButton("×")  # Multiplication sign

# Цвет "white" может не применяться
color: white;

# Текст в конструкторе может не отобразиться
QPushButton("X")
```

### ✅ Работает:
```python
# Используй setText() отдельно
btn = QPushButton()
btn.setText("X")  # Обычные ASCII символы

# Цвета только в hex формате
color: #ffffff;

# Всегда указывай padding и margin
padding: 0px;
margin: 0px;

# Явно указывай font-size
font-size: 14px;
```

### Полный рабочий пример кнопки удаления:
```python
remove_btn = QPushButton()
remove_btn.setText("X")
remove_btn.setFixedSize(26, 26)
remove_btn.setCursor(Qt.CursorShape.PointingHandCursor)
remove_btn.setStyleSheet("""
    QPushButton {
        background-color: #5a5a7a;
        color: #ffffff;
        border: none;
        border-radius: 4px;
        font-size: 14px;
        font-weight: bold;
        padding: 0px;
        margin: 0px;
    }
    QPushButton:hover {
        background-color: #ff6b6b;
        color: #ffffff;
    }
""")
```

## Эмодзи в кнопках

### ✅ Работает (но нужен большой размер):
```python
btn = QPushButton("👁")
btn.setFixedSize(40, 36)
btn.setStyleSheet("font-size: 18px; padding: 0px;")
```

## Списки с кастомными элементами

### ❌ НЕ работает:
```python
# QListWidget + setItemWidget() - виджеты внутри не отображаются корректно
list_widget = QListWidget()
item = QListWidgetItem()
list_widget.addItem(item)
list_widget.setItemWidget(item, custom_widget)  # Проблемы с рендерингом
```

### ✅ Работает:
```python
# Используй QScrollArea + QVBoxLayout + QFrame для каждого элемента
scroll = QScrollArea()
scroll.setWidgetResizable(True)

container = QWidget()
layout = QVBoxLayout(container)
layout.addStretch()  # Прижимает элементы вверх

scroll.setWidget(container)

# Добавление элемента:
row = QFrame()
row.setProperty("data_key", value)  # Хранение данных
row_layout = QHBoxLayout(row)
# ... добавляем виджеты в row_layout

count = layout.count()
layout.insertWidget(count - 1, row)  # Вставляем перед stretch
```

## Общие правила стилей

1. **Цвета** - только hex: `#ffffff`, `#ff6b6b`, `#5a5a7a`
2. **Фон** - явно указывай `background-color` или `background: transparent`
3. **Размеры** - используй `setFixedSize()` для кнопок-иконок
4. **Курсор** - добавляй `setCursor(Qt.CursorShape.PointingHandCursor)` для кликабельных элементов
5. **Hover** - дублируй `color` в `:hover` если он должен сохраняться
