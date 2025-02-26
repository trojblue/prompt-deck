FONT_FAMILY = "Inter, Segoe UI, -apple-system, BlinkMacSystemFont, Roboto, Oxygen, Ubuntu, Cantarell, sans-serif"


ui_style = """
            QMainWindow {
                background-color: #fafafa;
            }
            QScrollArea {
                background-color: #fafafa;
                border: none;
            }
            QScrollBar:vertical {
                border: none;
                background: #f5f5f5;
                width: 6px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #d0d0d0;
                min-height: 20px;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical:hover {
                background: #b0b0b0;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """

name_input_style = """
            QLineEdit {
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 6px;
                background-color: white;
            }
            QLineEdit:focus {
                border: 1px solid #6c8baf;
                background-color: white;
            }
        """

content_input_style = """
            QTextEdit {
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 6px;
                background-color: white;
            }
            QTextEdit:focus {
                border: 1px solid #6c8baf;
                background-color: white;
            }
        """

delete_button_style = """
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 4px;
                opacity: 0.8;
            }
            QPushButton:hover {
                background-color: #c0392b;
                opacity: 1.0;
            }
            QPushButton:pressed {
                background-color: #a93226;
            }
        """

main_prompt_style = """
            QTextEdit {
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                padding: 10px;
                background-color: white;
            }
            QTextEdit:focus {
                border: 1px solid #6c8baf;
                background-color: white;
                box-shadow: 0 0 4px rgba(108, 139, 175, 0.25);
            }
        """


add_context_btn_style = """
            QPushButton {
                background-color: #6c8baf;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px;
            }
            QPushButton:hover {
                background-color: #7c9bbf;
            }
            QPushButton:pressed {
                background-color: #5c7b9f;
            }
        """

copy_btn_style = """
            QPushButton {
                background-color: #6c8baf;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #7c9bbf;
            }
            QPushButton:pressed {
                background-color: #5c7b9f;
            }
        """
