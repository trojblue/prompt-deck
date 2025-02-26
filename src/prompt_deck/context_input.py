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
        """Read file contents, store them in the text area, and remember the file name."""
        try:
            file_text = Path(filepath).read_text(encoding="utf-8", errors="replace")
            self.file_name = Path(filepath).name  # Just the filename
            
            # Update the "notes" section with the filename
            self.name_input.setText(self.file_name)
            
            self.content_input.setPlainText(file_text)
            self.update_char_count()
        except Exception as e:
            print(f"Error reading file: {e}")

    #
    # Drag-and-drop overrides
    #
    def dragEnterEvent(self, event):
        """Accept a file if dragged into the widget."""
        if event.mimeData().hasUrls():
            # Check if at least one of them is a local file
            urls = event.mimeData().urls()
            if len(urls) > 0 and urls[0].isLocalFile():
                event.acceptProposedAction()
                
                # Highlight effect for this context input
                current_style = self.styleSheet()
                self.setStyleSheet(current_style + """
                    ContextInput {
                        background-color: rgba(232, 245, 233, 0.5);
                        border: 2px dashed #4CAF50;
                        border-radius: 5px;
                    }
                """)
        else:
            super().dragEnterEvent(event)
            
    def dragLeaveEvent(self, event):
        """Reset styling when drag leaves."""
        # Restore original styling
        self.setStyleSheet("")
        super().dragLeaveEvent(event)

    def dropEvent(self, event):
        """When a file is dropped, load its contents."""
        urls = event.mimeData().urls()
        if urls and urls[0].isLocalFile():
            filepath = urls[0].toLocalFile()
            
            # Flash a confirmation style briefly
            self.setStyleSheet("""
                ContextInput {
                    background-color: rgba(232, 245, 233, 0.8);
                    border: 2px solid #4CAF50;
                    border-radius: 5px;
                }
            """)
            
            # Reset after a short delay
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(500, lambda: self.setStyleSheet(""))
            
            self.load_file(filepath)
            event.acceptProposedAction()
        else:
            super().dropEvent(event)

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