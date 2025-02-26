import sys
import json
from pathlib import Path
from typing import List, Dict
import webbrowser
from appdirs import user_data_dir

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                            QHBoxLayout, QTextEdit, QLineEdit, QPushButton,
                            QLabel, QScrollArea, QFrame, QSizePolicy)
from PyQt6.QtCore import Qt, QPoint, QRect, QSize, QTimer, QEvent
from PyQt6.QtGui import QScreen, QIcon, QCursor, QKeySequence, QShortcut
import keyboard

class ContextInput(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(2)

        # Context name input
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Context Name")
        layout.addWidget(self.name_input)

        # Context content input
        self.content_input = QTextEdit()
        self.content_input.setFixedHeight(80)
        self.content_input.setPlaceholderText("Context Content")
        self.content_input.textChanged.connect(self.update_char_count)
        layout.addWidget(self.content_input)

        # Bottom row with character count and delete button
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(2)
        
        # Character count label
        self.char_count_label = QLabel("Characters: 0")
        bottom_row.addWidget(self.char_count_label)
        
        bottom_row.addStretch()
        
        # Delete button
        self.delete_button = QPushButton("Remove")
        self.delete_button.setFixedWidth(80)
        self.delete_button.clicked.connect(self.on_delete)
        bottom_row.addWidget(self.delete_button)
        
        layout.addLayout(bottom_row)

    def on_delete(self):
        # This will be connected in the parent widget
        self.setParent(None)
        self.deleteLater()

    def update_char_count(self):
        count = len(self.content_input.toPlainText())
        self.char_count_label.setText(f"Characters: {count}")

    def get_data(self) -> Dict[str, str]:
        return {
            "name": self.name_input.text(),
            "content": self.content_input.toPlainText()
        }

    def set_data(self, data: Dict[str, str]):
        self.name_input.setText(data.get("name", ""))
        self.content_input.setText(data.get("content", ""))
        self.update_char_count()

class PromptDeck(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Prompt Deck")
        self.setup_ui()
        self.setup_shortcuts()
        self.load_state()
        
        # Flags
        self.auto_hide_enabled = True
        self.mouse_in_window = False
        
        # Install event filter for tracking mouse
        self.installEventFilter(self)
        
        # Start the auto-hide timer with a longer interval
        self.auto_hide_timer = QTimer(self)
        self.auto_hide_timer.setInterval(2000)  # Check every 2 seconds
        self.auto_hide_timer.timeout.connect(self.check_mouse_position)
        self.auto_hide_timer.start()

    def setup_ui(self):
        # Main widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        # Main prompt input
        prompt_layout = QVBoxLayout()
        prompt_layout.setSpacing(2)
        prompt_label = QLabel("Main Prompt:")
        prompt_layout.addWidget(prompt_label)
        
        self.main_prompt = QTextEdit()
        self.main_prompt.setFixedHeight(80)
        self.main_prompt.setPlaceholderText("Enter your main prompt here...")
        prompt_layout.addWidget(self.main_prompt)
        
        main_layout.addLayout(prompt_layout)

        # Contexts section
        context_section = QHBoxLayout()
        context_label = QLabel("Context Sections:")
        context_section.addWidget(context_label)
        context_section.addStretch()
        
        add_context_btn = QPushButton("Add Context")
        add_context_btn.setFixedWidth(100)
        add_context_btn.clicked.connect(self.add_context)
        context_section.addWidget(add_context_btn)
        main_layout.addLayout(context_section)

        # Scrollable area for context inputs
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        self.context_container = QWidget()
        self.context_layout = QVBoxLayout(self.context_container)
        self.context_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.context_layout.setContentsMargins(0, 0, 0, 0)
        self.context_layout.setSpacing(5)
        
        self.scroll.setWidget(self.context_container)
        main_layout.addWidget(self.scroll)

        # Context controls
        self.contexts = []
        
        # Add one context by default
        self.add_context()

        # Action buttons
        button_layout = QHBoxLayout()
        
        # Auto-hide toggle
        self.auto_hide_btn = QPushButton("Toggle Auto-hide")
        self.auto_hide_btn.setFixedWidth(120)
        self.auto_hide_btn.clicked.connect(self.toggle_auto_hide)
        button_layout.addWidget(self.auto_hide_btn)
        
        self.copy_btn = QPushButton("Copy to Clipboard")
        self.copy_btn.clicked.connect(self.copy_to_clipboard)
        button_layout.addWidget(self.copy_btn)

        # LLM site shortcuts
        self.llm_sites = {
            "ChatGPT": "https://chat.openai.com",
            "Claude": "https://claude.ai",
            "Grok": "https://grok.x.ai"
        }

        for name, url in self.llm_sites.items():
            btn = QPushButton(name)
            btn.setFixedWidth(70)
            btn.clicked.connect(lambda checked, u=url: self.launch_site(u))
            button_layout.addWidget(btn)

        main_layout.addLayout(button_layout)

        # Set initial size and position
        self.resize(500, 600)
        self.move_to_corner()

    def eventFilter(self, obj, event):
        if obj is self:
            if event.type() == QEvent.Type.Enter:
                self.mouse_in_window = True
                return True
            elif event.type() == QEvent.Type.Leave:
                self.mouse_in_window = False
                return True
        return super().eventFilter(obj, event)

    def toggle_auto_hide(self):
        self.auto_hide_enabled = not self.auto_hide_enabled
        if self.auto_hide_enabled:
            self.auto_hide_btn.setText("Toggle Auto-hide (ON)")
            self.auto_hide_timer.start()
        else:
            self.auto_hide_btn.setText("Toggle Auto-hide (OFF)")
            self.auto_hide_timer.stop()

    def setup_shortcuts(self):
        # Global shortcut for showing/hiding
        try:
            # Change to Ctrl+Shift+U
            keyboard.add_hotkey('ctrl+shift+u', self.toggle_visibility)
        except Exception as e:
            print(f"Could not register global hotkey: {e}")
            # Fallback: Create a local shortcut
            from PyQt6.QtGui import QKeySequence, QShortcut
            self.shortcut = QShortcut(QKeySequence("Ctrl+Shift+U"), self)
            self.shortcut.activated.connect(self.toggle_visibility)

    def check_mouse_position(self):
        if not self.auto_hide_enabled:
            return
            
        cursor_pos = QCursor.pos()
        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()

        # Define hot corner area (top-left 20x20 pixels)
        hot_corner = QRect(0, 0, 20, 20)

        # Show if mouse is in hot corner
        if hot_corner.contains(cursor_pos):
            self.show()
            self.activateWindow()
        # Hide if not in window and not in hot corner
        elif not self.mouse_in_window and not self.geometry().contains(cursor_pos) and self.isVisible():
            self.hide()

    def move_to_corner(self):
        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()
        self.move(screen_geometry.width() - self.width(), 0)  # Top-right corner

    def add_context(self):
        context = ContextInput()
        context.delete_button.clicked.connect(lambda: self.remove_context(context))
        self.contexts.append(context)
        self.context_layout.addWidget(context)

    def remove_context(self, context):
        if context in self.contexts:
            self.contexts.remove(context)

    def copy_to_clipboard(self):
        formatted_text = self.get_formatted_text()
        clipboard = QApplication.clipboard()
        clipboard.setText(formatted_text)

    def launch_site(self, url: str):
        self.copy_to_clipboard()
        webbrowser.open(url)

    def get_formatted_text(self) -> str:
        parts = [self.main_prompt.toPlainText(), ""]

        # Filter out only valid contexts
        valid_contexts = [context for context in self.contexts 
                         if context.parent() is not None and 
                         (context.get_data()["name"] or context.get_data()["content"])]
        
        for context in valid_contexts:
            data = context.get_data()
            parts.extend([
                f"{data['name']}:",
                data["content"],
                ""
            ])

        return "\n".join(parts)

    def toggle_visibility(self):
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.activateWindow()
            self.main_prompt.setFocus()

    def get_state(self) -> Dict:
        # Filter out deleted contexts
        valid_contexts = [context for context in self.contexts if context.parent() is not None]
        
        return {
            "main_prompt": self.main_prompt.toPlainText(),
            "contexts": [context.get_data() for context in valid_contexts],
            "geometry": {
                "x": self.x(),
                "y": self.y(),
                "width": self.width(),
                "height": self.height()
            },
            "auto_hide": self.auto_hide_enabled
        }

    def load_state(self):
        state_file = Path(user_data_dir("PromptDeck")) / "state.json"
        if state_file.exists():
            try:
                with open(state_file) as f:
                    state = json.load(f)
                
                self.main_prompt.setText(state.get("main_prompt", ""))
                
                for context_data in state.get("contexts", []):
                    context = ContextInput()
                    context.set_data(context_data)
                    context.delete_button.clicked.connect(lambda: self.remove_context(context))
                    self.contexts.append(context)
                    self.context_layout.addWidget(context)
                
                geometry = state.get("geometry", {})
                if geometry:
                    self.setGeometry(
                        geometry.get("x", 0),
                        geometry.get("y", 0),
                        geometry.get("width", 500),
                        geometry.get("height", 600)
                    )
                    
                # Load auto-hide state
                self.auto_hide_enabled = state.get("auto_hide", True)
                if not self.auto_hide_enabled:
                    self.auto_hide_btn.setText("Toggle Auto-hide (OFF)")
                    self.auto_hide_timer.stop()
                else:
                    self.auto_hide_btn.setText("Toggle Auto-hide (ON)")
                    
            except Exception as e:
                print(f"Error loading state: {e}")

    def save_state(self):
        state_dir = Path(user_data_dir("PromptDeck"))
        state_dir.mkdir(parents=True, exist_ok=True)
        state_file = state_dir / "state.json"
        
        try:
            with open(state_file, "w") as f:
                json.dump(self.get_state(), f)
        except Exception as e:
            print(f"Error saving state: {e}")

    def closeEvent(self, event):
        self.save_state()
        try:
            keyboard.unhook_all()  # Clean up keyboard hooks
        except Exception as e:
            print(f"Error unhoooking keyboard: {e}")
        super().closeEvent(event)

def main() -> None:
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    window = PromptDeck()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()