from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QIcon, QPainter, QPixmap

from .styles import FONT_FAMILY

class FilePlaceholder(QWidget):
    """
    A nicer placeholder widget for the empty context state that shows
    a document icon and instructions for dropping files.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 30, 20, 30)
        layout.setSpacing(15)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Get standard file icon
        self.icon_label = QLabel()
        file_icon = QIcon(QIcon.fromTheme("document", 
                         QIcon.fromTheme("text-x-generic")))
                          
        # If system themes aren't available, try to use Qt's standard icons
        if file_icon.isNull():
            from PyQt6.QtWidgets import QApplication, QStyle
            file_icon = QIcon(QApplication.style().standardIcon(QApplication.style().StandardPixmap.SP_FileIcon))
        
        pixmap = file_icon.pixmap(QSize(48, 48))
        self.icon_label.setPixmap(pixmap)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.icon_label)
        
        # Instruction text - now stored as a class attribute so it can be modified
        self.text_label = QLabel("Add context or drop files here")
        self.text_label.setFont(QFont(FONT_FAMILY, 12))
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text_label.setStyleSheet("color: #95a5a6;")
        layout.addWidget(self.text_label)
        
        # Style the widget with a subtle border
        self.setStyleSheet("""
            FilePlaceholder {
                background-color: #f8f9fa;
                border: 2px dashed #e0e0e0;
                border-radius: 8px;
            }
        """)
        
        # Set fixed size for better appearance
        self.setMinimumHeight(150)