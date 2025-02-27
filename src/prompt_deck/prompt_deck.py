import sys
import json
import time
from pathlib import Path
from typing import Dict, List, Union, Optional
import webbrowser

from appdirs import user_data_dir

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QTextEdit, QLineEdit, QPushButton,
    QLabel, QScrollArea, QFrame, QSizePolicy, QMessageBox,
    QSplitter, QStatusBar, QMenu, QDialog
)
from PyQt6.QtCore import (
    Qt, QSize, QTimer, QPoint, QPropertyAnimation
)


from PyQt6.QtGui import (
    QFont, QIcon, QColor, QPalette, QKeySequence, QAction, QShortcut
)

from .styles import FONT_FAMILY
from .styles import (ui_style, add_context_btn_style, copy_btn_style, main_prompt_style, 
                   get_llm_button_style, delete_button_style, clear_all_style,
                   duplicate_context_style, toast_style, context_section_style)

from .context_input import ContextInput, FileContextInput
from .file_drop_area import FileDropArea



class ToastNotification(QFrame):
    """Toast notification widget for status messages"""
    
    def __init__(self, parent, message, duration=3000):
        super().__init__(parent)
        self.setStyleSheet(toast_style)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.ToolTip)
        
        # Setup layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        
        # Message label
        self.message_label = QLabel(message)
        self.message_label.setStyleSheet("color: white;")
        self.message_label.setFont(QFont(FONT_FAMILY, 10))
        layout.addWidget(self.message_label)
        
        # Position and show
        self.duration = duration
        self.setWindowOpacity(0.0)
        self.timer = QTimer()
        self.timer.timeout.connect(self.hide_animation)
        self.timer.setSingleShot(True)
        
        # Fade in animation
        self.fade_in()
        
    def fade_in(self):
        """Animate fade in"""
        self.show()
        
        # Position at the bottom center of parent
        parent_rect = self.parent().rect()
        x = parent_rect.center().x() - self.width() // 2
        y = parent_rect.bottom() - self.height() - 20  # 20px from bottom
        
        self.move(self.parent().mapToGlobal(QPoint(x, y)))
        
        # Fade in animation
        self.animation = QPropertyAnimation(self, b"windowOpacity")
        self.animation.setDuration(300)
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.start()
        
        # Start timer for auto-hide
        self.timer.start(self.duration)
        
    def hide_animation(self):
        """Animate fade out and hide"""
        self.animation = QPropertyAnimation(self, b"windowOpacity")
        self.animation.setDuration(300)
        self.animation.setStartValue(1.0)
        self.animation.setEndValue(0.0)
        self.animation.finished.connect(self.hide)
        self.animation.start()


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
        
        # Undo/redo stack for text edits
        self.undo_stack = []
        self.redo_stack = []
        self.current_state = None

        # Setup UI
        self.setup_ui()
        self.setup_shortcuts()
        self.load_state()
        
        # Show initial tip
        QTimer.singleShot(500, lambda: self.show_toast("Tip: Drag the contexts by their left handles to reorder them"))

    def setup_ui(self):
        # Set the application style - more elegant, muted color palette
        self.setStyleSheet(ui_style)

        # Main widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)

        # Create a splitter for the main sections
        self.splitter = QSplitter(Qt.Orientation.Vertical)
        self.splitter.setChildrenCollapsible(False)
        
        # Top section: Main prompt
        top_widget = QWidget()
        prompt_layout = QVBoxLayout(top_widget)
        prompt_layout.setContentsMargins(0, 0, 0, 0)
        prompt_layout.setSpacing(4)

        # Improved label styling
        prompt_header = QHBoxLayout()
        prompt_label = QLabel("Main Prompt")
        prompt_label.setFont(QFont(FONT_FAMILY, 11, QFont.Weight.Medium))
        prompt_label.setStyleSheet("color: #2c3e50; margin-bottom: 4px;")
        prompt_header.addWidget(prompt_label)
        
        prompt_header.addStretch()
        
        # Character count for main prompt
        self.main_prompt_char_count = QLabel("Characters: 0")
        self.main_prompt_char_count.setFont(QFont(FONT_FAMILY, 8))
        self.main_prompt_char_count.setStyleSheet("color: #7f8c8d; font-style: italic;")
        prompt_header.addWidget(self.main_prompt_char_count)
        
        prompt_layout.addLayout(prompt_header)

        # Improved text edit styling
        self.main_prompt = QTextEdit()
        self.main_prompt.setMinimumHeight(40)
        self.main_prompt.setPlaceholderText("Enter your main prompt here...")
        self.main_prompt.setFont(QFont(FONT_FAMILY, 10))
        self.main_prompt.setStyleSheet(main_prompt_style)
        self.main_prompt.textChanged.connect(self.update_main_prompt_char_count)
        prompt_layout.addWidget(self.main_prompt)
        
        # Add top widget to splitter
        self.splitter.addWidget(top_widget)
        
        # Bottom section: Context
        bottom_widget = QWidget()
        context_container_layout = QVBoxLayout(bottom_widget)
        context_container_layout.setContentsMargins(0, 0, 0, 0)
        context_container_layout.setSpacing(10)

        # Contexts row
        context_section = QHBoxLayout()
        context_label = QLabel("Context Sections")
        context_label.setFont(QFont(FONT_FAMILY, 11, QFont.Weight.Medium))
        context_label.setStyleSheet("color: #2c3e50;")
        context_section.addWidget(context_label)
        
        # Total character count for all contexts
        self.total_char_count = QLabel("Total: 0 chars")
        self.total_char_count.setFont(QFont(FONT_FAMILY, 8))
        self.total_char_count.setStyleSheet("color: #7f8c8d; font-style: italic;")
        context_section.addWidget(self.total_char_count)
        
        context_section.addStretch()

        # Clear All button
        clear_all_btn = QPushButton("Clear All")
        clear_all_btn.setFixedWidth(80)
        clear_all_btn.setFont(QFont(FONT_FAMILY, 9))
        clear_all_btn.clicked.connect(self.clear_all_contexts)
        clear_all_btn.setStyleSheet(clear_all_style)
        clear_all_btn.setToolTip("Remove all context sections (Ctrl+Shift+X)")
        context_section.addWidget(clear_all_btn)

        # File context button
        add_file_context_btn = QPushButton("Add File")
        add_file_context_btn.setFixedWidth(80)
        add_file_context_btn.setFont(QFont(FONT_FAMILY, 9))
        add_file_context_btn.clicked.connect(self.add_file_context)
        add_file_context_btn.setStyleSheet(add_context_btn_style)
        add_file_context_btn.setToolTip("Add a file reference context (Ctrl+Shift+F)")
        context_section.addWidget(add_file_context_btn)

        # Add Context button
        add_context_btn = QPushButton("Add Context")
        add_context_btn.setFixedWidth(100)
        add_context_btn.setFont(QFont(FONT_FAMILY, 9))
        add_context_btn.clicked.connect(self.add_context)
        add_context_btn.setStyleSheet(add_context_btn_style)
        add_context_btn.setToolTip("Add a text context (Ctrl+Shift+N)")
        context_section.addWidget(add_context_btn)

        context_container_layout.addLayout(context_section)

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
        context_container_layout.addWidget(self.scroll)
        
        # Add bottom widget to splitter
        self.splitter.addWidget(bottom_widget)
        
        # Set initial sizes for splitter sections (40% top, 60% bottom)
        self.splitter.setSizes([200, 300])
        
        # Add splitter to main layout
        main_layout.addWidget(self.splitter)

        # Keep track of contexts
        self.contexts = []

        # Add a separator before buttons
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.Shape.HLine)
        separator2.setFrameShadow(QFrame.Shadow.Sunken)
        separator2.setStyleSheet("background-color: #e8e8e8; margin: 8px 0;")
        main_layout.addWidget(separator2)

        # Button row with better organization
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)  # Add better spacing between buttons

        # Preview button - shows output without copying
        self.preview_btn = QPushButton("Preview")
        self.preview_btn.setFont(QFont(FONT_FAMILY, 10))
        self.preview_btn.clicked.connect(self.preview_formatted_text)
        self.preview_btn.setStyleSheet(duplicate_context_style)
        self.preview_btn.setToolTip("Preview the formatted output (Ctrl+P)")
        button_layout.addWidget(self.preview_btn)

        # Copy to clipboard
        self.copy_btn = QPushButton("Copy to Clipboard")
        self.copy_btn.setFont(QFont(FONT_FAMILY, 10))
        self.copy_btn.clicked.connect(self.copy_to_clipboard)
        self.copy_btn.setStyleSheet(copy_btn_style)
        self.copy_btn.setToolTip("Copy to clipboard (Ctrl+C)")
        button_layout.addWidget(self.copy_btn)

        # LLM site shortcuts with more elegant, muted styling
        self.llm_sites = {
            "ChatGPT": ("https://chat.openai.com", "#34495e"),  # Dark slate
            "Claude":  ("https://claude.ai", "#ec6b2d"),        # Claude orange
            "Grok":    ("https://x.com/i/grok", "#333333")      # Dark gray (not pure black)
        }

        for name, (url, color) in self.llm_sites.items():
            btn = QPushButton(name)
            btn.setFixedWidth(80)
            btn.setFont(QFont(FONT_FAMILY, 10))
            btn.clicked.connect(lambda checked, u=url, n=name: self.launch_site(u, n))
            btn.setStyleSheet(get_llm_button_style(color))
            button_layout.addWidget(btn)

        main_layout.addLayout(button_layout)
        
        # Add status bar
        self.status_bar = QStatusBar()
        self.status_bar.setFont(QFont(FONT_FAMILY, 9))
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

        # More refined window size with better proportions
        self.resize(520, 600)

    def setup_shortcuts(self):
        """Setup keyboard shortcuts for common actions"""
        # Add context (Ctrl+Shift+N)
        self.shortcut_add_context = QShortcut(QKeySequence("Ctrl+Shift+N"), self)
        self.shortcut_add_context.activated.connect(self.add_context)
        
        # Add file context (Ctrl+Shift+F)
        self.shortcut_add_file = QShortcut(QKeySequence("Ctrl+Shift+F"), self)
        self.shortcut_add_file.activated.connect(self.add_file_context)
        
        # Clear all contexts (Ctrl+Shift+X)
        self.shortcut_clear_all = QShortcut(QKeySequence("Ctrl+Shift+X"), self)
        self.shortcut_clear_all.activated.connect(self.clear_all_contexts)
        
        # Copy to clipboard (Ctrl+C)
        self.shortcut_copy = QShortcut(QKeySequence("Ctrl+C"), self)
        self.shortcut_copy.activated.connect(self.copy_to_clipboard)
        
        # Preview (Ctrl+P)
        self.shortcut_preview = QShortcut(QKeySequence("Ctrl+P"), self)
        self.shortcut_preview.activated.connect(self.preview_formatted_text)
        
        # Save (Ctrl+S)
        self.shortcut_save = QShortcut(QKeySequence("Ctrl+S"), self)
        self.shortcut_save.activated.connect(self.save_state)

    def update_main_prompt_char_count(self):
        """Update the character count for main prompt"""
        count = len(self.main_prompt.toPlainText())
        self.main_prompt_char_count.setText(f"Characters: {count}")
        
        # Update the state to enable undo/redo
        self.update_state()
        
    def update_state(self):
        """Store current state for undo/redo"""
        # TODO: Implement full undo/redo functionality later
        pass
        
    def update_total_char_count(self):
        """Update the total character count for all contexts"""
        try:
            total = len(self.main_prompt.toPlainText())
            
            # Add character counts from context sections
            for context in self.contexts:
                if hasattr(context, 'content_input'):
                    total += len(context.content_input.toPlainText())
                elif hasattr(context, 'char_count'):
                    total += context.char_count
            
            self.total_char_count.setText(f"Total: {total} chars")
        except Exception as e:
            print(f"Error updating total char count: {e}")

    def add_context(self):
        """Add a regular text context input"""
        # Check if placeholder exists and remove it
        if hasattr(self, 'placeholder') and self.placeholder is not None:
            self.placeholder.setVisible(False)
            self.placeholder = None
            
        context = ContextInput()
        # Configure the context
        context.id = id(context)  # Store unique ID
        context.delete_button.clicked.connect(self.on_delete_context)
        context.duplicateRequested.connect(self.duplicate_context)
        
        # Add special visual styling
        context.setStyleSheet(context_section_style)
        
        self.contexts.append(context)
        self.context_layout.addWidget(context)
        
        # Update char count
        QTimer.singleShot(100, self.update_total_char_count)
        
        return context

    def add_file_context(self):
        """Add a file context input that uses lazy loading"""
        # Check if placeholder exists and remove it
        if hasattr(self, 'placeholder') and self.placeholder is not None:
            self.placeholder.setVisible(False)
            self.placeholder = None
            
        # Create the file context input
        file_context = FileContextInput()
        file_context.id = id(file_context)
        file_context.delete_button.clicked.connect(self.on_delete_context)
        file_context.duplicateRequested.connect(self.duplicate_context)
        
        # Add special visual styling
        file_context.setStyleSheet(context_section_style)
        
        # Add to context list and layout
        self.contexts.append(file_context)
        self.context_layout.addWidget(file_context)
        
        # Open file dialog immediately
        try:
            from PyQt6.QtWidgets import QFileDialog
            path, _ = QFileDialog.getOpenFileName(self, "Select a File", "", "All Files (*)")
            if path:
                file_context.set_file_path(path)
                
                # Update char count
                QTimer.singleShot(1000, self.update_total_char_count)
            else:
                # If no file selected, remove the context
                self.remove_context(file_context)
                return None
        except Exception as e:
            print(f"Error opening file dialog: {e}")
        
        return file_context

    def duplicate_context(self, context):
        """Duplicate a context with its content"""
        if hasattr(context, 'create_duplicate'):
            try:
                # Create a duplicate
                duplicate = context.create_duplicate()
                duplicate.id = id(duplicate)
                duplicate.delete_button.clicked.connect(self.on_delete_context)
                duplicate.duplicateRequested.connect(self.duplicate_context)
                
                # Add special visual styling
                duplicate.setStyleSheet(context_section_style)
                
                # Insert after the original context
                index = self.contexts.index(context)
                self.contexts.insert(index + 1, duplicate)
                
                # Add to layout at the correct position
                self.context_layout.insertWidget(index + 1, duplicate)
                
                # Show notification
                self.show_toast("Context duplicated")
                
                # Update char count
                QTimer.singleShot(100, self.update_total_char_count)
                
            except Exception as e:
                print(f"Error duplicating context: {e}")
                QMessageBox.critical(self, "Error", f"Failed to duplicate context: {e}")
        else:
            print("Context doesn't support duplication")

    def clear_all_contexts(self):
        """Remove all contexts"""
        try:
            # Ask for confirmation
            reply = QMessageBox.question(
                self, "Confirm", "Remove all context sections?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # Disconnect signals and remove widgets
                for context in list(self.contexts):
                    self.remove_context(context)
                    
                # Show confirmation
                self.show_toast("All contexts cleared")
                
                # Update char count
                QTimer.singleShot(100, self.update_total_char_count)
        except Exception as e:
            print(f"Error clearing contexts: {e}")
            QMessageBox.critical(self, "Error", f"Failed to clear contexts: {e}")

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
            
            # Update char count
            QTimer.singleShot(100, self.update_total_char_count)

    def reorder_contexts(self, source_id, target_id):
        """Reorder contexts when drag-and-drop occurs"""
        try:
            # Find source and target indices
            source_context = None
            target_context = None
            
            for ctx in self.contexts:
                if ctx.id == source_id:
                    source_context = ctx
                elif ctx.id == target_id:
                    target_context = ctx
            
            if not source_context or not target_context:
                return
                
            # Get indices
            source_index = self.contexts.index(source_context)
            target_index = self.contexts.index(target_context)
            
            if source_index == target_index:
                return
                
            # Remove from original position
            self.contexts.remove(source_context)
            
            # Insert at new position (before target)
            insert_index = self.contexts.index(target_context)
            self.contexts.insert(insert_index, source_context)
            
            # Update the UI (remove and re-add widgets in correct order)
            for ctx in self.contexts:
                self.context_layout.removeWidget(ctx)
                
            for ctx in self.contexts:
                self.context_layout.addWidget(ctx)
                
            # Show notification
            self.show_toast("Context order updated")
        except Exception as e:
            print(f"Error reordering contexts: {e}")

    def handle_file_drop(self, filepath):
        """
        Create a new file context and set the file path.
        """
        from pathlib import Path
        
        try:
            # Handle case where an invalid or URL-like path is dropped
            path_obj = Path(filepath)
            
            # Skip if it looks like a URL or invalid path
            if any(proto in str(path_obj) for proto in ['http:', 'https:', 'ftp:', 'file:']):
                print(f"Skipping URL-like path: {filepath}")
                self.show_toast(f"Invalid URL: {filepath}", 2000)
                return
                
            # Skip if file doesn't exist
            if not path_obj.exists():
                print(f"File does not exist: {filepath}")
                self.show_toast(f"File not found: {filepath}", 2000)
                return
                
            # Now create a file context and set the path
            file_context = FileContextInput()
            file_context.id = id(file_context)
            file_context.delete_button.clicked.connect(self.on_delete_context)
            file_context.duplicateRequested.connect(self.duplicate_context)
            
            # Add special visual styling
            file_context.setStyleSheet(context_section_style)
            
            # Check if placeholder exists and remove it
            if hasattr(self, 'placeholder') and self.placeholder is not None:
                self.placeholder.setVisible(False)
                self.placeholder = None
                
            # Add to context list and layout
            self.contexts.append(file_context)
            self.context_layout.addWidget(file_context)
            
            # Set the file path
            file_context.set_file_path(filepath)
            
            # Show confirmation toast
            self.show_toast(f"Added file: {path_obj.name}")
            
            # Update char count
            QTimer.singleShot(1000, self.update_total_char_count)
        except Exception as e:
            print(f"Error handling file drop: {e}")
            # Show error message to user
            QMessageBox.critical(self, "Error", f"Could not load file: {e}")

    def remove_context(self, context):
        if context in self.contexts:
            # Disconnect signals first to prevent callbacks on deleted objects
            try:
                if hasattr(context, 'delete_button') and context.delete_button:
                    context.delete_button.clicked.disconnect()
                if hasattr(context, 'content_input') and hasattr(context.content_input, 'textChanged'):
                    context.content_input.textChanged.disconnect()
                if hasattr(context, 'duplicateRequested'):
                    context.duplicateRequested.disconnect()
                
                # Cancel any running file threads
                if hasattr(context, 'file_thread') and hasattr(context.file_thread, 'isRunning') and context.file_thread.isRunning():
                    context.file_thread.terminate()
                    context.file_thread.wait()
            except Exception as e:
                # Already disconnected or other error
                print(f"Error disconnecting signals: {e}")
                
            self.contexts.remove(context)
            
            # First, remove from layout
            self.context_layout.removeWidget(context)
            
            # Then set parent to None to ensure deletion
            context.setParent(None)
            
            # Finally, schedule for deletion
            context.deleteLater()
            
        # If no contexts left, show placeholder again
        if not self.contexts:
            if not hasattr(self, 'placeholder') or self.placeholder is None:
                from .file_placeholder import FilePlaceholder
                self.placeholder = FilePlaceholder()
                self.context_layout.addWidget(self.placeholder)
                
            # Update status bar
            self.status_bar.showMessage("No contexts added yet")

    def copy_to_clipboard(self):
        try:
            # Update status
            self.status_bar.showMessage("Preparing content...")
            
            # Load latest file content before copying
            self.reload_file_contents()
            
            # Get the formatted text
            formatted_text = self.get_formatted_text()
            
            # Copy to clipboard
            clipboard = QApplication.clipboard()
            clipboard.setText(formatted_text)
            
            # Show success message
            self.status_bar.showMessage(f"Copied {len(formatted_text)} characters to clipboard", 3000)
            
            # Show toast notification
            self.show_toast("Copied to clipboard")
            
            # Update character counts
            self.update_total_char_count()
        except Exception as e:
            print(f"Error copying to clipboard: {e}")
            self.status_bar.showMessage(f"Error: {e}", 3000)
            QMessageBox.critical(self, "Error", f"Failed to copy to clipboard: {e}")

    def preview_formatted_text(self):
        """Show a preview of the formatted text"""
        try:
            # Update status
            self.status_bar.showMessage("Preparing preview...")
            
            # Load latest file content
            self.reload_file_contents()
            
            # Get the formatted text
            formatted_text = self.get_formatted_text()
            
            # Show preview dialog
            preview = QDialog(self)
            preview.setWindowTitle("Preview")
            preview.setMinimumSize(500, 400)
            
            # Layout
            layout = QVBoxLayout(preview)
            
            # Preview text area
            preview_text = QTextEdit()
            preview_text.setReadOnly(True)
            preview_text.setFont(QFont(FONT_FAMILY, 10))
            preview_text.setPlainText(formatted_text)
            layout.addWidget(preview_text)
            
            # Info label
            info_label = QLabel(f"Total: {len(formatted_text)} characters")
            info_label.setFont(QFont(FONT_FAMILY, 9))
            info_label.setAlignment(Qt.AlignmentFlag.AlignRight)
            layout.addWidget(info_label)
            
            # Buttons
            buttons_layout = QHBoxLayout()
            
            # Copy button
            copy_btn = QPushButton("Copy to Clipboard")
            copy_btn.clicked.connect(lambda: (clipboard.setText(formatted_text), 
                                            self.show_toast("Copied to clipboard"),
                                            preview.accept()))
            buttons_layout.addWidget(copy_btn)
            
            # Close button
            close_btn = QPushButton("Close")
            close_btn.clicked.connect(preview.accept)
            buttons_layout.addWidget(close_btn)
            
            layout.addLayout(buttons_layout)
            
            # Get clipboard ready
            clipboard = QApplication.clipboard()
            
            # Show dialog
            preview.exec()
            
            # Update status
            self.status_bar.showMessage("Preview closed", 3000)
            
        except Exception as e:
            print(f"Error showing preview: {e}")
            self.status_bar.showMessage(f"Error: {e}", 3000)
            QMessageBox.critical(self, "Error", f"Failed to generate preview: {e}")

    def reload_file_contents(self):
        """Reload the latest content from all file contexts"""
        try:
            # Update status
            self.status_bar.showMessage("Reading file contents...", 1000)
            
            for context in self.contexts:
                if isinstance(context, FileContextInput) and hasattr(context, 'read_latest_content'):
                    context.read_latest_content()
        except Exception as e:
            print(f"Error reloading file contents: {e}")
            self.status_bar.showMessage(f"Error reading files: {e}", 3000)

    def launch_site(self, url: str, site_name: str):
        try:
            # Update status
            self.status_bar.showMessage(f"Launching {site_name}...")
            
            # Copy to clipboard
            self.copy_to_clipboard()
            
            # Launch the site
            webbrowser.open(url)
            
            # Update status
            self.status_bar.showMessage(f"Launched {site_name}", 3000)
        except Exception as e:
            print(f"Error launching site: {e}")
            self.status_bar.showMessage(f"Error: {e}", 3000)
            QMessageBox.critical(self, "Error", f"Failed to open website: {e}")

    def get_formatted_text(self) -> str:
        parts = [self.main_prompt.toPlainText(), ""]

        try:
            # Process only contexts that are still in the UI and have content
            valid_contexts = [
                c for c in self.contexts
                if c.parent() is not None
            ]
            
            for context in valid_contexts:
                data = context.get_data()
                
                if isinstance(context, FileContextInput):
                    # For file contexts, get the most recent content
                    content, success = context.read_latest_content()
                    if success:
                        parts.extend([
                            f"{data['name']}:",
                            content,
                            ""
                        ])
                else:
                    # Regular context - check if it has content
                    if data.get("name") or data.get("content"):
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
            # Get splitter sizes for proportions
            splitter_sizes = self.splitter.sizes()
            
            valid_contexts = []
            for c in self.contexts:
                if c.parent() is not None:
                    valid_contexts.append(c.get_data())
            
            return {
                "main_prompt": self.main_prompt.toPlainText(),
                "contexts": valid_contexts,
                "splitter_sizes": splitter_sizes,
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
                "splitter_sizes": [200, 300],
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
                self.update_main_prompt_char_count()

                # Remove default contexts and placeholder
                if hasattr(self, 'placeholder') and self.placeholder is not None:
                    self.placeholder.setVisible(False)
                    self.placeholder = None
                
                for c in self.contexts:
                    c.setParent(None)
                self.contexts.clear()

                # Restore splitter sizes if available
                splitter_sizes = state.get("splitter_sizes", [200, 300])
                self.splitter.setSizes(splitter_sizes)

                # Load from file
                contexts_data = state.get("contexts", [])
                if contexts_data:
                    for context_data in contexts_data:
                        # Check if it's a file context
                        if context_data.get("is_file", False):
                            # Create file context
                            file_context = FileContextInput()
                            file_context.id = id(file_context)
                            file_context.delete_button.clicked.connect(self.on_delete_context)
                            file_context.duplicateRequested.connect(self.duplicate_context)
                            file_context.setStyleSheet(context_section_style)
                            file_context.set_data(context_data)
                            self.contexts.append(file_context)
                            self.context_layout.addWidget(file_context)
                        else:
                            # Regular context
                            context = ContextInput()
                            context.id = id(context)
                            context.delete_button.clicked.connect(self.on_delete_context)
                            context.duplicateRequested.connect(self.duplicate_context)
                            context.setStyleSheet(context_section_style)
                            context.set_data(context_data)
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
                    
                # Update char count
                QTimer.singleShot(500, self.update_total_char_count)
                
                # Update status
                self.status_bar.showMessage("State loaded", 3000)
            except Exception as e:
                print(f"Error loading state: {e}")
                self.status_bar.showMessage(f"Error loading state: {e}", 3000)
                QMessageBox.warning(self, "Warning", f"Failed to load previous state: {e}")

    def save_state(self):
        self.status_bar.showMessage("Saving state...")
        
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
                
            # Update status
            self.status_bar.showMessage("State saved", 3000)
            self.show_toast("Settings saved")
        except Exception as e:
            print(f"Error saving state: {e}")
            self.status_bar.showMessage(f"Error saving state: {e}", 3000)
            if temp_file.exists():
                try:
                    temp_file.unlink()  # Clean up temp file
                except:
                    pass

    def show_toast(self, message, duration=2000):
        """Show a toast notification with message"""
        toast = ToastNotification(self, message, duration)
        toast.show()
        
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
        Each valid file will create a new file context.
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

    def contextMenuEvent(self, event):
        """Custom context menu for additional actions"""
        try:
            # Create custom context menu
            menu = QMenu(self)
            
            # Add actions based on where the menu was invoked
            add_context_action = QAction("Add Context", self)
            add_context_action.triggered.connect(self.add_context)
            menu.addAction(add_context_action)
            
            add_file_action = QAction("Add File Context", self)
            add_file_action.triggered.connect(self.add_file_context)
            menu.addAction(add_file_action)
            
            menu.addSeparator()
            
            copy_action = QAction("Copy to Clipboard", self)
            copy_action.triggered.connect(self.copy_to_clipboard)
            menu.addAction(copy_action)
            
            preview_action = QAction("Preview Formatted Text", self)
            preview_action.triggered.connect(self.preview_formatted_text)
            menu.addAction(preview_action)
            
            menu.addSeparator()
            
            save_action = QAction("Save", self)
            save_action.triggered.connect(self.save_state)
            menu.addAction(save_action)
            
            # Show the menu
            menu.exec(event.globalPos())
        except Exception as e:
            print(f"Error showing context menu: {e}")


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