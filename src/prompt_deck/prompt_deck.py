import sys
import json
from pathlib import Path
from typing import Dict
import webbrowser

from appdirs import user_data_dir

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QTextEdit, QLineEdit, QPushButton,
    QLabel, QScrollArea, QFrame, QSizePolicy, QMessageBox
)
from PyQt6.QtCore import (
    Qt, QSize, QTimer
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
        
        # Store timer for style reset
        self.style_reset_timer = None

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
        # Use a more robust callback approach with unique identifier
        context.id = id(context)  # Store unique ID
        context.delete_button.clicked.connect(self.on_delete_context)
        self.contexts.append(context)
        self.context_layout.addWidget(context)
        return context

    def on_delete_context(self):
        """Handles delete button clicks from context objects"""
        sender = self.sender()
        context_to_remove = None
        
        for context in self.contexts:
            if context.delete_button == sender:
                context_to_remove = context
                break
                
        if context_to_remove:
            self.remove_context(context_to_remove)

    def handle_file_drop(self, filepath):
        """
        Create a new context and load the file into it.
        Now handles filepath validation before creating context.
        """
        from pathlib import Path
        
        try:
            # Handle case where an invalid or URL-like path is dropped
            path_obj = Path(filepath)
            
            # Skip if it looks like a URL or invalid path
            if any(proto in str(path_obj) for proto in ['http:', 'https:', 'ftp:', 'file:']):
                print(f"Skipping URL-like path: {filepath}")
                return
                
            # Skip if file doesn't exist
            if not path_obj.exists():
                print(f"File does not exist: {filepath}")
                return
                
            # Now create the context and load the file
            context = self.add_context()
            context.load_file(filepath)
        except Exception as e:
            print(f"Error handling file drop: {e}")
            # Show error message to user
            QMessageBox.critical(self, "Error", f"Could not load file: {e}")

    def remove_context(self, context):
        if context in self.contexts:
            # Disconnect signals first to prevent callbacks on deleted objects
            try:
                context.delete_button.clicked.disconnect()
                if hasattr(context, 'content_input'):
                    context.content_input.textChanged.disconnect()
                
                # Cancel any running file threads
                if hasattr(context, 'file_thread') and hasattr(context.file_thread, 'isRunning') and context.file_thread.isRunning():
                    context.file_thread.terminate()
                    context.file_thread.wait()
            except Exception as e:
                # Already disconnected or other error
                print(f"Error disconnecting signals: {e}")
                
            self.contexts.remove(context)
            
        # If no contexts left, show placeholder again
        if not self.contexts:
            if not hasattr(self, 'placeholder') or self.placeholder is None:
                from .file_placeholder import FilePlaceholder
                self.placeholder = FilePlaceholder()
                self.context_layout.addWidget(self.placeholder)

    def copy_to_clipboard(self):
        try:
            formatted_text = self.get_formatted_text()
            clipboard = QApplication.clipboard()
            clipboard.setText(formatted_text)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to copy to clipboard: {e}")

    def launch_site(self, url: str):
        try:
            self.copy_to_clipboard()
            webbrowser.open(url)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open website: {e}")

    def get_formatted_text(self) -> str:
        parts = [self.main_prompt.toPlainText(), ""]

        try:
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
        except Exception as e:
            print(f"Error formatting text: {e}")
            parts.append(f"[Error formatting context data: {e}]")

        return "\n".join(parts)

    def get_state(self) -> Dict:
        try:
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
        except Exception as e:
            print(f"Error getting state: {e}")
            # Return minimal valid state
            return {
                "main_prompt": "",
                "contexts": [],
                "geometry": {
                    "x": 100,
                    "y": 100,
                    "width": 520,
                    "height": 600
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
                        context.id = id(context)
                        context.delete_button.clicked.connect(self.on_delete_context)
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
                QMessageBox.warning(self, "Warning", f"Failed to load previous state: {e}")

    def save_state(self):
        state_dir = Path(user_data_dir("PromptDeck"))
        state_dir.mkdir(parents=True, exist_ok=True)
        state_file = state_dir / "state.json"
        temp_file = state_dir / "state.json.tmp"

        try:
            # Write to temp file first
            with open(temp_file, "w") as f:
                json.dump(self.get_state(), f)
            
            # Rename temp file to actual file (atomic operation)
            if sys.platform == 'win32':
                # Windows needs special handling for replacing files
                import os
                if state_file.exists():
                    os.replace(str(temp_file), str(state_file))
                else:
                    temp_file.rename(state_file)
            else:
                # Unix-like platforms
                temp_file.replace(state_file)
        except Exception as e:
            print(f"Error saving state: {e}")
            if temp_file.exists():
                try:
                    temp_file.unlink()  # Clean up temp file
                except:
                    pass

    #
    # Drag and Drop implementation for the entire window
    #
    def dragEnterEvent(self, event):
        """
        Accept the drag event if it has URLs (files).
        Now displays correct information for multi-file drop.
        """
        try:
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
        except Exception as e:
            print(f"Error in dragEnterEvent: {e}")
            event.ignore()
    
    def dragLeaveEvent(self, event):
        """Reset styling when drag leaves."""
        try:
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
        except Exception as e:
            print(f"Error in dragLeaveEvent: {e}")
            # Try to reset to a safe state
            self.context_container.setStyleSheet("background-color: #fafafa;")
            self.is_drag_active = False

    def dropEvent(self, event):
        """
        Improved drop event that handles multiple files and validates file paths.
        Each valid file will create a new context.
        """
        try:
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
                
                # Reset after a short delay using managed timer
                if hasattr(self, 'style_reset_timer') and self.style_reset_timer is not None and self.style_reset_timer.isActive():
                    self.style_reset_timer.stop()
                
                self.style_reset_timer = QTimer()
                self.style_reset_timer.setSingleShot(True)
                self.style_reset_timer.timeout.connect(lambda: self.context_container.setStyleSheet("background-color: #fafafa;"))
                self.style_reset_timer.start(500)
                
                self.is_drag_active = False
                
                event.acceptProposedAction()
        except Exception as e:
            print(f"Error in dropEvent: {e}")
            # Reset to safe state
            self.context_container.setStyleSheet("background-color: #fafafa;")
            self.is_drag_active = False
            event.ignore()
    
    def closeEvent(self, event):
        try:
            # Cancel any running threads
            for context in self.contexts:
                if hasattr(context, 'file_thread') and hasattr(context.file_thread, 'isRunning') and context.file_thread.isRunning():
                    context.file_thread.terminate()
                    context.file_thread.wait()
            
            # Save state before closing
            self.save_state()
        except Exception as e:
            print(f"Error in closeEvent: {e}")
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

    try:
        # Create and show the main window
        window = PromptDeck()
        window.show()
        
        sys.exit(app.exec())
    except Exception as e:
        print(f"Fatal error in application: {e}")
        # Show error dialog
        if QApplication.instance():
            QMessageBox.critical(None, "Fatal Error", f"Application crashed: {e}")
        sys.exit(1)