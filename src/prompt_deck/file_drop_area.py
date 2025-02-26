from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPalette, QColor, QDragEnterEvent, QDropEvent

from .styles import FONT_FAMILY

class FileDropArea(QWidget):
    """A drop area that accepts files and emits a signal with the file path"""
    
    # Signal emitted when a file is dropped
    fileDropped = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Create a label with instructions
        self.label = QLabel("Drop Files")
        self.label.setFont(QFont(FONT_FAMILY, 9))
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Style the widget to look like a button
        self.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
                border: 1px dashed #95a5a6;
                border-radius: 4px;
            }
            QWidget:hover {
                background-color: #e0e0e0;
                border: 1px dashed #7f8c8d;
            }
        """)
        
        layout.addWidget(self.label)
        
    def dragEnterEvent(self, event: QDragEnterEvent):
        # Accept the drag event if it has URLs (files)
        if event.mimeData().hasUrls() and len(event.mimeData().urls()) > 0:
            if event.mimeData().urls()[0].isLocalFile():
                event.acceptProposedAction()
                # Highlight the drop area
                self.setStyleSheet("""
                    QWidget {
                        background-color: #e8f5e9;
                        border: 1px dashed #66bb6a;
                        border-radius: 4px;
                    }
                """)
        
    def dragLeaveEvent(self, event):
        # Reset styling when drag leaves
        self.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
                border: 1px dashed #95a5a6;
                border-radius: 4px;
            }
            QWidget:hover {
                background-color: #e0e0e0;
                border: 1px dashed #7f8c8d;
            }
        """)
        
    def dropEvent(self, event: QDropEvent):
        # When a file is dropped, emit a signal with the file path
        urls = event.mimeData().urls()
        if urls and urls[0].isLocalFile():
            filepath = urls[0].toLocalFile()
            self.fileDropped.emit(filepath)
            
            # Flash a confirmation style briefly
            self.setStyleSheet("""
                QWidget {
                    background-color: #e8f5e9;
                    border: 1px solid #66bb6a;
                    border-radius: 4px;
                }
            """)
            
            # Reset after a short delay
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(500, lambda: self.setStyleSheet("""
                QWidget {
                    background-color: #f0f0f0;
                    border: 1px dashed #95a5a6;
                    border-radius: 4px;
                }
                QWidget:hover {
                    background-color: #e0e0e0;
                    border: 1px dashed #7f8c8d;
                }
            """))
            
            event.acceptProposedAction()