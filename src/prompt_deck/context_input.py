from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QTextEdit, QPushButton, QLabel
from PyQt6.QtGui import QFont
from .styles import FONT_FAMILY, name_input_style, content_input_style

from typing import Dict
from pathlib import Path

from .styles import name_input_style, content_input_style, delete_button_style, add_context_btn_style

class ContextInput(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Track if we have a file loaded
        self.file_name = None
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
        self.delete_button.clicked.connect(self.on_delete)
        self.delete_button.setStyleSheet(delete_button_style)
        bottom_row.addWidget(self.delete_button)

        layout.addLayout(bottom_row)

    #
    # File logic
    #
    def on_add_file_clicked(self):
        """Open a file dialog to load file contents into the text box."""
        from PyQt6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getOpenFileName(self, "Select a File", "", "All Files (*)")
        if path:
            self.load_file(path)

    def load_file(self, filepath: str):
        """
        Read file contents, store them in the text area, and remember the file name.
        Now with improved path validation and better error handling.
        """
        from pathlib import Path
        
        try:
            path_obj = Path(filepath)
            
            # Skip URL-like paths
            if "://" in filepath and not path_obj.exists():
                print(f"Skipping URL-like path: {filepath}")
                return False
                
            # Verify the file exists and is readable
            if not path_obj.exists():
                print(f"File does not exist: {filepath}")
                return False
                
            # Try to read the file, with fallback for binary files
            try:
                file_text = path_obj.read_text(encoding="utf-8", errors="replace")
            except UnicodeDecodeError:
                # For binary files, just note it's a binary file
                file_text = f"[Binary file: {path_obj.name}]"
            
            self.file_name = path_obj.name  # Just the filename
            
            # Update the "notes" section with the filename
            self.name_input.setText(self.file_name)
            
            self.content_input.setPlainText(file_text)
            self.update_char_count()
            return True
            
        except Exception as e:
            print(f"Error reading file: {e}")
            return False

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
        self.setParent(None)
        self.deleteLater()

    def update_char_count(self):
        count = len(self.content_input.toPlainText())
        self.char_count_label.setText(f"Characters: {count}")

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

    def set_data(self, data: Dict[str, str]):
        """
        Load previously saved content.
        If it looks like file-based content, parse it out (optional).
        """
        # We'll do a simple approach: if we detect the pattern with "```",
        # we assume a file was previously loaded. This is optional.
        # You can parse more precisely if needed.

        notes = data.get("name", "")
        content_str = data.get("content", "")

        self.file_name = None  # Reset

        # Optional: if the content pattern matches the file-based approach
        # (filename + ```...), we could parse it. For simplicity, we'll just set the text.
        self.name_input.setText(notes)
        self.content_input.setText(content_str)
        self.update_char_count()