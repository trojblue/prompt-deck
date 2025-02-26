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
from .styles import ui_style, add_context_btn_style, copy_btn_style, main_prompt_style, get_llm_button_style

from .context_input import ContextInput
from .file_drop_area import FileDropArea  # We'll create this class


class PromptDeck(QMainWindow):
    def __init__(self):
        super().__init__(None, Qt.WindowType.Window)
        self.setWindowTitle("Prompt Deck")

        # Use a nicer system icon for a more professional look
        self.setWindowIcon(QIcon(QApplication.style().standardIcon(QApplication.style().StandardPixmap.SP_FileDialogContentsView)))
        
        # Enable drag and drop for the entire window
        self.setAcceptDrops(True)
        
        # Variable to track highlight state
        self.is_drag_active = False
        self.original_stylesheet = ""

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
        self.main_prompt.setMinimumHeight(40)
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

        # Removed file drop area - entire window will be a drop area instead

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
        
        # Add placeholder for empty context (better visual)
        from .file_placeholder import FilePlaceholder
        self.placeholder = FilePlaceholder()
        self.context_layout.addWidget(self.placeholder)

        self.scroll.setWidget(self.context_container)
        main_layout.addWidget(self.scroll)

        # Keep track of contexts
        self.contexts = []

        # Don't add default context - just show placeholder
        # self.add_context()

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
            "ChatGPT": ("https://chat.openai.com", "#34495e"),  # Dark slate
            "Claude":  ("https://claude.ai", "#ec6b2d"),        # Claude orange
            "Grok":    ("https://x.com/i/grok", "#333333")         # Dark gray (not pure black)
        }

        for name, (url, color) in self.llm_sites.items():
            btn = QPushButton(name)
            btn.setFixedWidth(80)
            btn.setFont(QFont(FONT_FAMILY, 10))
            btn.clicked.connect(lambda checked, u=url: self.launch_site(u))
            btn.setStyleSheet(get_llm_button_style(color))
            button_layout.addWidget(btn)

        main_layout.addLayout(button_layout)

        # More refined window size with better proportions
        self.resize(520, 600)

    def add_context(self):
        # Check if placeholder exists and remove it
        if hasattr(self, 'placeholder') and self.placeholder is not None:
            self.placeholder.setVisible(False)
            self.placeholder = None
            
        context = ContextInput()
        context.delete_button.clicked.connect(
            lambda: self.remove_context(context)
        )
        self.contexts.append(context)
        self.context_layout.addWidget(context)
        return context

    def handle_file_drop(self, filepath):
        """
        Create a new context and load the file into it.
        Now handles filepath validation before creating context.
        """
        from pathlib import Path
        
        # Handle case where an invalid or URL-like path is dropped
        path_obj = Path(filepath)
        
        # Skip if it looks like a URL or invalid path
        if not path_obj.exists() or "://" in filepath:
            print(f"Skipping invalid file path: {filepath}")
            return
            
        # Now create the context and load the file
        context = self.add_context()
        context.load_file(filepath)

    def remove_context(self, context):
        if context in self.contexts:
            self.contexts.remove(context)
            
        # If no contexts left, show placeholder again
        if not self.contexts:
            if not hasattr(self, 'placeholder') or self.placeholder is None:
                from .file_placeholder import FilePlaceholder
                self.placeholder = FilePlaceholder()
                self.context_layout.addWidget(self.placeholder)

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

                # Remove default contexts and placeholder
                if hasattr(self, 'placeholder') and self.placeholder is not None:
                    self.placeholder.setVisible(False)
                    self.placeholder = None
                
                for c in self.contexts:
                    c.setParent(None)
                self.contexts.clear()

                # Load from file
                contexts_data = state.get("contexts", [])
                if contexts_data:
                    for context_data in contexts_data:
                        context = ContextInput()
                        context.set_data(context_data)
                        context.delete_button.clicked.connect(
                            lambda: self.remove_context(context)
                        )
                        self.contexts.append(context)
                        self.context_layout.addWidget(context)
                else:
                    # If no contexts in saved state, show placeholder
                    if not hasattr(self, 'placeholder') or self.placeholder is None:
                        from .file_placeholder import FilePlaceholder
                        self.placeholder = FilePlaceholder()
                        self.context_layout.addWidget(self.placeholder)

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

    #
    # Drag and Drop implementation for the entire window
    #
    def dragEnterEvent(self, event):
        """
        Accept the drag event if it has URLs (files).
        Now displays correct information for multi-file drop.
        """
        if event.mimeData().hasUrls():
            # Count how many valid files we have
            valid_file_count = sum(1 for url in event.mimeData().urls() if url.isLocalFile())
            
            if valid_file_count > 0:
                event.acceptProposedAction()
                
                # Store original stylesheet if not already stored
                if not self.is_drag_active:
                    self.original_stylesheet = self.context_container.styleSheet()
                    self.is_drag_active = True
                
                # Check if placeholder is visible and apply special styling
                if hasattr(self, 'placeholder') and self.placeholder and self.placeholder.isVisible():
                    # Update placeholder text to show number of files
                    if valid_file_count > 1:
                        self.placeholder.text_label.setText(f"Drop to add {valid_file_count} files")
                    else:
                        self.placeholder.text_label.setText("Drop to add file")
                    
                    self.placeholder.setStyleSheet("""
                        FilePlaceholder {
                            background-color: rgba(232, 245, 233, 0.7);
                            border: 2px dashed #4CAF50;
                            border-radius: 8px;
                        }
                    """)
                else:
                    # Regular highlight effect for content container
                    self.context_container.setStyleSheet("background-color: rgba(232, 245, 233, 0.5); border: 2px dashed #4CAF50; border-radius: 5px;")
    
    def dragLeaveEvent(self, event):
        """Reset styling when drag leaves."""
        if self.is_drag_active:
            if hasattr(self, 'placeholder') and self.placeholder and self.placeholder.isVisible():
                # Reset placeholder text
                self.placeholder.text_label.setText("Add context or drop files here")
                self.placeholder.setStyleSheet("""
                    FilePlaceholder {
                        background-color: #f8f9fa;
                        border: 2px dashed #e0e0e0;
                        border-radius: 8px;
                    }
                """)
            else:
                self.context_container.setStyleSheet("background-color: #fafafa;")
            self.is_drag_active = False


    def dropEvent(self, event):
        """
        Improved drop event that handles multiple files and validates file paths.
        Each valid file will create a new context.
        """
        urls = event.mimeData().urls()
        if urls:
            # Temporarily flash the confirmation style
            if hasattr(self, 'placeholder') and self.placeholder and self.placeholder.isVisible():
                self.placeholder.setStyleSheet("""
                    FilePlaceholder {
                        background-color: rgba(232, 245, 233, 0.8);
                        border: 2px solid #4CAF50;
                        border-radius: 8px;
                    }
                """)
            else:
                self.context_container.setStyleSheet("background-color: rgba(232, 245, 233, 0.8); border: 2px solid #4CAF50; border-radius: 5px;")
            
            # Process all valid local files in the drop event
            for url in urls:
                if url.isLocalFile():
                    filepath = url.toLocalFile()
                    self.handle_file_drop(filepath)
            
            # Reset after a short delay
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(500, lambda: self.context_container.setStyleSheet("background-color: #fafafa;"))
            self.is_drag_active = False
            
            event.acceptProposedAction()
    
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