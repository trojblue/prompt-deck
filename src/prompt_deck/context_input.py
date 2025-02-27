from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QTextEdit, QPushButton, QLabel, QMessageBox
from PyQt6.QtGui import QFont, QTextCursor
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from .styles import FONT_FAMILY, name_input_style, content_input_style

from typing import Dict
from pathlib import Path

from .styles import name_input_style, content_input_style, delete_button_style, add_context_btn_style

# New thread class for file loading
class FileReaderThread(QThread):
    file_read = pyqtSignal(str, str)  # path, content
    error_occurred = pyqtSignal(str, str)  # path, error message
    
    def __init__(self, path):
        super().__init__()
        self.path = path
        
    def run(self):
        try:
            # Safely read the file
            path_obj = Path(self.path)
            if not path_obj.exists():
                self.error_occurred.emit(self.path, "File does not exist")
                return
                
            # Check file size and handle large files
            if path_obj.stat().st_size > 5 * 1024 * 1024:  # 5MB limit
                with path_obj.open(encoding="utf-8", errors="replace") as f:
                    file_text = f.read(1024 * 1024)  # First MB
                    file_text += "\n\n[File truncated due to size...]"
            else:
                try:
                    file_text = path_obj.read_text(encoding="utf-8", errors="replace")
                except UnicodeDecodeError:
                    # For binary files
                    self.file_read.emit(self.path, f"[Binary file: {path_obj.name}]")
                    return
                
            self.file_read.emit(self.path, file_text)
        except Exception as e:
            self.error_occurred.emit(self.path, str(e))

class ContextInput(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Track if we have a file loaded
        self.file_name = None
        # Unique ID for this context (used for callbacks)
        self.id = id(self)
        # File loading thread
        self.file_thread = None
        
        self.setup_ui()

        # Enable drag-and-drop on this widget
        self.setAcceptDrops(True)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 2, 10, 2)  # Added 10px right margin
        layout.setSpacing(2)

        # "Notes" input (was "Context Name")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Context Notes")
        self.name_input.setFont(QFont(FONT_FAMILY, 10))
        self.name_input.setStyleSheet(name_input_style)
        layout.addWidget(self.name_input)

        # Content input / text area
        self.content_input = QTextEdit()
        self.content_input.setFixedHeight(150)  # Increased from 80 to 150
        self.content_input.setPlaceholderText("Content")
        self.content_input.setFont(QFont(FONT_FAMILY, 10))
        self.content_input.textChanged.connect(self.update_char_count)
        modified_content_style = content_input_style + "padding-right: 5px;"
        self.content_input.setStyleSheet(modified_content_style)
        layout.addWidget(self.content_input)

        # Bottom row (unchanged)
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(5)

        # Character count label
        self.char_count_label = QLabel("Characters: 0")
        self.char_count_label.setFont(QFont(FONT_FAMILY, 8))
        self.char_count_label.setStyleSheet("color: #7f8c8d; font-style: italic;")
        bottom_row.addWidget(self.char_count_label)

        bottom_row.addStretch()

        # "Add File" button
        self.file_button = QPushButton("Add File")
        self.file_button.setFixedWidth(80)
        self.file_button.setFont(QFont(FONT_FAMILY, 9))
        self.file_button.clicked.connect(self.on_add_file_clicked)
        # You can reuse or alter any style you prefer
        self.file_button.setStyleSheet(add_context_btn_style)
        bottom_row.addWidget(self.file_button)

        # Delete button
        self.delete_button = QPushButton("Remove")
        self.delete_button.setFixedWidth(80)
        self.delete_button.setFont(QFont(FONT_FAMILY, 9))
        # on_delete is now called from parent via callback in prompt_deck.py
        self.delete_button.clicked.connect(self.on_delete)
        self.delete_button.setStyleSheet(delete_button_style)
        bottom_row.addWidget(self.delete_button)

        layout.addLayout(bottom_row)

    #
    # File logic
    #
    def on_add_file_clicked(self):
        """Open a file dialog to load file contents into the text box."""
        try:
            from PyQt6.QtWidgets import QFileDialog
            path, _ = QFileDialog.getOpenFileName(self, "Select a File", "", "All Files (*)")
            if path:
                self.load_file(path)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open file dialog: {e}")

    def load_file(self, filepath: str):
        """
        Read file contents, store them in the text area, and remember the file name.
        Now with improved path validation, error handling, and threading.
        """
        try:
            path_obj = Path(filepath)
            
            # Skip URL-like paths
            if any(proto in str(path_obj) for proto in ['http:', 'https:', 'ftp:', 'file:']):
                print(f"Skipping URL-like path: {filepath}")
                return False
                
            # Verify the file exists
            if not path_obj.exists():
                print(f"File does not exist: {filepath}")
                QMessageBox.warning(self, "Warning", f"File does not exist: {filepath}")
                return False
            
            # Set loading indicator
            self.content_input.setPlainText("Loading file...")
            
            # Start file reading in background thread
            self.file_thread = FileReaderThread(filepath)
            self.file_thread.file_read.connect(self.on_file_read)
            self.file_thread.error_occurred.connect(self.on_file_error)
            self.file_thread.start()
            
            return True
        except Exception as e:
            print(f"Error starting file load: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load file: {e}")
            return False
    
    def on_file_read(self, path, content):
        """Handle successful file read"""
        try:
            path_obj = Path(path)
            self.file_name = path_obj.name
            self.name_input.setText(self.file_name)
            self.content_input.setPlainText(content)
            self.update_char_count()
        except Exception as e:
            print(f"Error processing file content: {e}")
            self.content_input.setPlainText(f"Error processing file: {e}")
    
    def on_file_error(self, path, error_msg):
        """Handle file read error"""
        self.content_input.setPlainText("")
        QMessageBox.critical(self, "Error", f"Error reading file: {error_msg}")

    #
    # Drag-and-drop overrides
    #
    def dragEnterEvent(self, event):
        """Accept file drags, but never let files be dropped directly into contexts."""
        # We want to prevent files from being dropped directly into existing contexts
        # Instead, we'll propagate the event up to the main window
        event.ignore()

    def dropEvent(self, event):
        """Prevent dropping directly into contexts - pass to parent window."""
        event.ignore()
            
    def dragLeaveEvent(self, event):
        """Reset styling when drag leaves."""
        # Restore original styling
        self.setStyleSheet("")
        super().dragLeaveEvent(event)
    #
    # Existing methods
    #
    def on_delete(self):
        """Removes itself from the layout and the main list."""
        try:
            # Cancel any file loading thread that might be running
            if self.file_thread and self.file_thread.isRunning():
                self.file_thread.terminate()
                self.file_thread.wait()
                
            # Remove from parent
            self.setParent(None)
            self.deleteLater()
        except Exception as e:
            print(f"Error in context deletion: {e}")

    def update_char_count(self):
        try:
            # Define maximum character limit
            MAX_CHARS = 100000  # 100K character limit
            
            text = self.content_input.toPlainText()
            count = len(text)
            
            if count > MAX_CHARS:
                # Truncate text and set cursor at end
                cursor = self.content_input.textCursor()
                cursor_pos = cursor.position()
                
                # Only truncate if we're at the end to avoid disrupting editing in the middle
                if cursor_pos > MAX_CHARS:
                    self.content_input.setPlainText(text[:MAX_CHARS])
                    cursor = self.content_input.textCursor()
                    cursor.movePosition(QTextCursor.MoveOperation.End)
                    self.content_input.setTextCursor(cursor)
                    count = MAX_CHARS
                
            # Update the label with warning if needed
            self.char_count_label.setText(f"Characters: {count}" + 
                                     (" (limit reached)" if count >= MAX_CHARS else ""))
            
            # Visual indicator when approaching limit
            if count > MAX_CHARS * 0.9:  # Over 90% of limit
                self.char_count_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
            else:
                self.char_count_label.setStyleSheet("color: #7f8c8d; font-style: italic;")
        except Exception as e:
            print(f"Error updating character count: {e}")
            self.char_count_label.setText("Characters: Error")

    def get_data(self) -> Dict[str, str]:
        """
        Return the "notes" in `name`
        and the final content in `content`.

        If a file was loaded, format it as:

            {file_name}
            ```text
            {file_contents}
            ```
        Otherwise, just return whatever is in the text box.
        """
        try:
            notes = self.name_input.text()
            raw_text = self.content_input.toPlainText()

            if self.file_name:
                # Construct the special format for file-based context
                content = f"{self.file_name}\n```text\n{raw_text}\n```"
            else:
                # Manual text mode
                content = raw_text

            return {
                "name": notes,      # "Context Notes"
                "content": content  # Possibly file-based
            }
        except Exception as e:
            print(f"Error getting data: {e}")
            return {
                "name": "Error",
                "content": f"Error retrieving content: {e}"
            }

    def set_data(self, data: Dict[str, str]):
        """
        Load previously saved content.
        If it looks like file-based content, parse it out (optional).
        """
        try:
            # We'll do a simple approach: if we detect the pattern with "```",
            # we assume a file was previously loaded. This is optional.
            # You can parse more precisely if needed.

            notes = str(data.get("name", "")) if data.get("name") is not None else ""
            content_str = str(data.get("content", "")) if data.get("content") is not None else ""

            self.file_name = None  # Reset

            # Optional: if the content pattern matches the file-based approach
            # (filename + ```...), we could parse it. For simplicity, we'll just set the text.
            self.name_input.setText(notes)
            self.content_input.setText(content_str)
            self.update_char_count()
        except Exception as e:
            print(f"Error setting data: {e}")
            self.name_input.setText("Error")
            self.content_input.setText(f"Error loading content: {e}")