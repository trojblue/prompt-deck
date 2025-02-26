import sys
import json
from pathlib import Path
from typing import Dict
import webbrowser

from appdirs import user_data_dir

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QTextEdit, QLineEdit, QPushButton,
    QLabel, QScrollArea, QFrame, QSizePolicy
)
from PyQt6.QtCore import (
    Qt, QSize
)
from PyQt6.QtGui import (
    QFont, QIcon, QColor, QPalette
)

from .styles import FONT_FAMILY
from .styles import ui_style, delete_button_style, name_input_style, content_input_style, add_context_btn_style, copy_btn_style, main_prompt_style

# Use more elegant fonts that are likely bundled with Windows
# Try to use system fonts in fallback order for better cross-platform compatibility


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
        self.name_input.setFont(QFont(FONT_FAMILY, 10))
        self.name_input.setStyleSheet(name_input_style)
        layout.addWidget(self.name_input)

        # Context content input
        self.content_input = QTextEdit()
        self.content_input.setFixedHeight(80)
        self.content_input.setPlaceholderText("Context Content")
        self.content_input.setFont(QFont(FONT_FAMILY, 10))
        self.content_input.textChanged.connect(self.update_char_count)
        self.content_input.setStyleSheet(content_input_style)
        layout.addWidget(self.content_input)

        # Bottom row
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(2)

        # Character count label
        self.char_count_label = QLabel("Characters: 0")
        self.char_count_label.setFont(QFont(FONT_FAMILY, 8))
        self.char_count_label.setStyleSheet("color: #7f8c8d; font-style: italic;")
        bottom_row.addWidget(self.char_count_label)

        bottom_row.addStretch()

        # Delete button
        self.delete_button = QPushButton("Remove")
        self.delete_button.setFixedWidth(80)
        self.delete_button.setFont(QFont(FONT_FAMILY, 9))
        self.delete_button.clicked.connect(self.on_delete)
        self.delete_button.setStyleSheet(delete_button_style)
        bottom_row.addWidget(self.delete_button)

        layout.addLayout(bottom_row)

    def on_delete(self):
        # Removes itself from its layout and the main list
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
        super().__init__(None, Qt.WindowType.Window)
        self.setWindowTitle("Prompt Deck")

        # Use a nicer system icon for a more professional look
        self.setWindowIcon(QIcon(QApplication.style().standardIcon(QApplication.style().StandardPixmap.SP_FileDialogContentsView)))

        # Setup UI
        self.setup_ui()
        self.load_state()

    def setup_ui(self):
        # Set the application style - more elegant, muted color palette
        self.setStyleSheet(ui_style)

        # Main widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)

        # Main prompt
        prompt_layout = QVBoxLayout()
        prompt_layout.setSpacing(4)

        # Improved label styling
        prompt_label = QLabel("Main Prompt")
        prompt_label.setFont(QFont(FONT_FAMILY, 11, QFont.Weight.Medium))
        prompt_label.setStyleSheet("color: #2c3e50; margin-bottom: 4px;")
        prompt_layout.addWidget(prompt_label)

        # Improved text edit styling
        self.main_prompt = QTextEdit()
        self.main_prompt.setMinimumHeight(100)
        self.main_prompt.setPlaceholderText("Enter your main prompt here...")
        self.main_prompt.setFont(QFont(FONT_FAMILY, 10))
        self.main_prompt.setStyleSheet(main_prompt_style)
        prompt_layout.addWidget(self.main_prompt)

        main_layout.addLayout(prompt_layout)

        # Add a subtle separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("background-color: #e8e8e8; margin: 8px 0;")
        main_layout.addWidget(separator)

        # Contexts row
        context_section = QHBoxLayout()
        context_label = QLabel("Context Sections")
        context_label.setFont(QFont(FONT_FAMILY, 11, QFont.Weight.Medium))
        context_label.setStyleSheet("color: #2c3e50;")
        context_section.addWidget(context_label)
        context_section.addStretch()

        # Improved button styling
        add_context_btn = QPushButton("Add Context")
        add_context_btn.setFixedWidth(100)
        add_context_btn.setFont(QFont(FONT_FAMILY, 9))
        add_context_btn.clicked.connect(self.add_context)
        add_context_btn.setStyleSheet(add_context_btn_style)
        context_section.addWidget(add_context_btn)

        main_layout.addLayout(context_section)

        # Scroll area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )

        self.context_container = QWidget()
        self.context_container.setStyleSheet("background-color: #fafafa;")
        self.context_layout = QVBoxLayout(self.context_container)
        self.context_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.context_layout.setContentsMargins(0, 0, 0, 0)
        self.context_layout.setSpacing(10)

        self.scroll.setWidget(self.context_container)
        main_layout.addWidget(self.scroll)

        # Keep track of contexts
        self.contexts = []

        # Add one context by default
        self.add_context()

        # Add a separator before buttons
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.Shape.HLine)
        separator2.setFrameShadow(QFrame.Shadow.Sunken)
        separator2.setStyleSheet("background-color: #e8e8e8; margin: 8px 0;")
        main_layout.addWidget(separator2)

        # Button row with better organization
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)  # Add better spacing between buttons

        # Copy to clipboard
        self.copy_btn = QPushButton("Copy to Clipboard")
        self.copy_btn.setFont(QFont(FONT_FAMILY, 10))
        self.copy_btn.clicked.connect(self.copy_to_clipboard)
        self.copy_btn.setStyleSheet(copy_btn_style)
        button_layout.addWidget(self.copy_btn)

        # LLM site shortcuts with more elegant, muted styling
        self.llm_sites = {
            "ChatGPT": ("https://chat.openai.com", "#34495e"),  # Darker slate
            "Claude":  ("https://claude.ai", "#7f8c8d"),        # Muted gray
            "Grok":    ("https://grok.x.ai", "#95a5a6")         # Light gray
        }

        for name, (url, color) in self.llm_sites.items():
            btn = QPushButton(name)
            btn.setFixedWidth(80)
            btn.setFont(QFont(FONT_FAMILY, 10))
            btn.clicked.connect(lambda checked, u=url: self.launch_site(u))
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 8px;
                }}
                QPushButton:hover {{
                    background-color: {color}dd;
                }}
                QPushButton:pressed {{
                    background-color: {color}aa;
                }}
            """)
            button_layout.addWidget(btn)

        main_layout.addLayout(button_layout)

        # More refined window size with better proportions
        self.resize(520, 600)

    def add_context(self):
        context = ContextInput()
        context.delete_button.clicked.connect(
            lambda: self.remove_context(context)
        )
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

        valid_contexts = [
            c for c in self.contexts
            if c.parent() is not None and
               (c.get_data()["name"] or c.get_data()["content"])
        ]
        for context in valid_contexts:
            data = context.get_data()
            parts.extend([
                f"{data['name']}:",
                data["content"],
                ""
            ])

        return "\n".join(parts)

    def get_state(self) -> Dict:
        valid_contexts = [
            c for c in self.contexts
            if c.parent() is not None
        ]
        return {
            "main_prompt": self.main_prompt.toPlainText(),
            "contexts": [c.get_data() for c in valid_contexts],
            "geometry": {
                "x": self.x(),
                "y": self.y(),
                "width": self.width(),
                "height": self.height()
            }
        }

    def load_state(self):
        state_file = Path(user_data_dir("PromptDeck")) / "state.json"
        if state_file.exists():
            try:
                with open(state_file) as f:
                    state = json.load(f)
                # Main prompt
                self.main_prompt.setText(state.get("main_prompt", ""))

                # Remove default contexts
                for c in self.contexts:
                    c.setParent(None)
                self.contexts.clear()

                # Load from file
                for context_data in state.get("contexts", []):
                    context = ContextInput()
                    context.set_data(context_data)
                    context.delete_button.clicked.connect(
                        lambda: self.remove_context(context)
                    )
                    self.contexts.append(context)
                    self.context_layout.addWidget(context)

                # Geometry
                geometry = state.get("geometry", {})
                if geometry:
                    self.setGeometry(
                        geometry.get("x", 0),
                        geometry.get("y", 0),
                        geometry.get("width", 500),
                        geometry.get("height", 600)
                    )
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
        # Save state before closing
        self.save_state()
        event.accept()


def main() -> None:
    app = QApplication(sys.argv)
    # Apply a clean modern style for the whole application
    app.setStyle("Fusion")

    # Create a custom palette for a refined, elegant look
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(250, 250, 250))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(44, 62, 80))  # Darker slate blue
    palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(248, 248, 248))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(44, 62, 80))
    palette.setColor(QPalette.ColorRole.Text, QColor(44, 62, 80))
    palette.setColor(QPalette.ColorRole.Button, QColor(245, 245, 245))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(44, 62, 80))
    palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.Link, QColor(108, 139, 175))  # Muted blue
    palette.setColor(QPalette.ColorRole.Highlight, QColor(108, 139, 175))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    app.setPalette(palette)

    # Create and show the main window
    window = PromptDeck()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()