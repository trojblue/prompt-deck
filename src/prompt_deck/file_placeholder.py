from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QApplication
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QFont, QIcon, QPainter, QPixmap, QColor

from .styles import FONT_FAMILY, add_context_btn_style

class FilePlaceholder(QWidget):
    """
    A nicer placeholder widget for the empty context state that shows
    a document icon and instructions for dropping files.
    
    Includes buttons for quick actions.
    """
    
    # Signals for button actions
    addContextClicked = pyqtSignal()
    addFileClicked = pyqtSignal()
    
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
            file_icon = QIcon(QApplication.style().standardIcon(QApplication.style().StandardPixmap.SP_FileIcon))
        
        pixmap = file_icon.pixmap(QSize(64, 64))  # Larger icon
        
        # Create a colorized version
        colorized_pixmap = QPixmap(pixmap.size())
        colorized_pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(colorized_pixmap)
        painter.setOpacity(0.8)
        painter.drawPixmap(0, 0, pixmap)
        painter.end()
        
        self.icon_label.setPixmap(colorized_pixmap)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.icon_label)
        
        # Title text
        title_label = QLabel("No Contexts Added")
        title_label.setFont(QFont(FONT_FAMILY, 14, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #34495e;")
        layout.addWidget(title_label)
        
        # Instruction text - now stored as a class attribute so it can be modified
        self.text_label = QLabel("Add context sections or drop files here")
        self.text_label.setFont(QFont(FONT_FAMILY, 12))
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text_label.setStyleSheet("color: #95a5a6;")
        layout.addWidget(self.text_label)
        
        # Quick actions buttons
        actions_layout = QHBoxLayout()
        actions_layout.setContentsMargins(0, 10, 0, 0)
        actions_layout.setSpacing(10)
        actions_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Add context button
        add_context_btn = QPushButton("Add Context")
        add_context_btn.setFixedWidth(120)
        add_context_btn.setFont(QFont(FONT_FAMILY, 10))
        add_context_btn.setStyleSheet(add_context_btn_style)
        add_context_btn.clicked.connect(self.addContextClicked.emit)
        actions_layout.addWidget(add_context_btn)
        
        # Add file button
        add_file_btn = QPushButton("Add File")
        add_file_btn.setFixedWidth(120)
        add_file_btn.setFont(QFont(FONT_FAMILY, 10))
        add_file_btn.setStyleSheet(add_context_btn_style)
        add_file_btn.clicked.connect(self.addFileClicked.emit)
        actions_layout.addWidget(add_file_btn)
        
        layout.addLayout(actions_layout)
        
        # Add keyboard shortcut hint
        shortcut_hint = QLabel("Tip: You can also drag & drop files here")
        shortcut_hint.setFont(QFont(FONT_FAMILY, 9, QFont.Weight.Normal, True))  # Italic
        shortcut_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        shortcut_hint.setStyleSheet("color: #95a5a6; margin-top: 10px;")
        layout.addWidget(shortcut_hint)
        
        # Style the widget with a subtle border
        self.setStyleSheet("""
            FilePlaceholder {
                background-color: #f8f9fa;
                border: 2px dashed #e0e0e0;
                border-radius: 8px;
            }
        """)
        
        # Set fixed size for better appearance
        self.setMinimumHeight(250)