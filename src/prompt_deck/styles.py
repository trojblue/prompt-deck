FONT_FAMILY = "Inter, Segoe UI, -apple-system, BlinkMacSystemFont, Roboto, Oxygen, Ubuntu, Cantarell, sans-serif"

# Function to adjust colors programmatically for hover/pressed states
def adjust_color(hex_color, percent):
    """
    Adjusts a hex color by percent.
    Negative percent darkens, positive lightens.
    """
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    
    # Adjust colors
    r = max(0, min(255, int(r * (1 + percent/100))))
    g = max(0, min(255, int(g * (1 + percent/100))))
    b = max(0, min(255, int(b * (1 + percent/100))))
    
    return f'#{r:02x}{g:02x}{b:02x}'

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
                background: #c0c0c0;
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

# Base colors
delete_color = "#e74c3c"
add_context_color = "#6c8baf"
copy_color = "#6c8baf"

delete_button_style = f"""
            QPushButton {{
                background-color: {delete_color};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 4px;
                opacity: 0.8;
            }}
            QPushButton:hover {{
                background-color: {adjust_color(delete_color, -10)};
                opacity: 0.9;
            }}
            QPushButton:pressed {{
                background-color: {adjust_color(delete_color, -20)};
            }}
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
add_context_btn_style = f"""
            QPushButton {{
                background-color: {add_context_color};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px;
            }}
            QPushButton:hover {{
                background-color: {adjust_color(add_context_color, -10)};
            }}
            QPushButton:pressed {{
                background-color: {adjust_color(add_context_color, -20)};
            }}
        """
copy_btn_style = f"""
            QPushButton {{
                background-color: {copy_color};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px;
            }}
            QPushButton:hover {{
                background-color: {adjust_color(copy_color, -10)};
            }}
            QPushButton:pressed {{
                background-color: {adjust_color(copy_color, -20)};
            }}
        """

# LLM site shortcuts with updated, more distinctive colors
llm_sites = {
    "ChatGPT": ("https://chat.openai.com", "#34495e"),  # Dark slate
    "Claude":  ("https://claude.ai", "#ec6b2d"),        # Claude orange
    "Grok":    ("https://grok.x.ai", "#333333")         # Dark gray (not pure black)
}

def get_llm_button_style(color):
    """Generate button style for LLM shortcuts with programmatic hover effects"""
    return f"""
        QPushButton {{
            background-color: {color};
            color: white;
            border: none;
            border-radius: 4px;
            padding: 8px;
        }}
        QPushButton:hover {{
            background-color: {adjust_color(color, -10)};
        }}
        QPushButton:pressed {{
            background-color: {adjust_color(color, -20)};
        }}
    """