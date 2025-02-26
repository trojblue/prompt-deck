# Prompt Deck

A lightweight Windows utility for efficiently structuring LLM prompts. The application provides a convenient interface that stays docked in the upper-right corner of your screen and can be quickly accessed when needed.

## Features

- **Auto-hide Functionality**: Automatically hides when not in use and reappears when you move your cursor to the top-left corner
- **Global Hotkey**: Toggle the application with Ctrl+U
- **Persistent Storage**: All prompts and context inputs are saved between sessions
- **Dynamic Context Fields**: Add multiple labeled context sections as needed
- **One-Click Actions**: Quickly copy formatted prompts and launch popular LLM websites
- **Character Counter**: Track the length of your context inputs

## Installation

1. Ensure you have Python 3.8 or higher installed
2. Clone this repository
3. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

1. Run the application:
```bash
python src/prompt_deck.py
```

2. The application will appear in the top-right corner of your screen

3. Use the following controls:
   - Press Ctrl+U to show/hide the application
   - Move your cursor to the top-left corner to show the application
   - Click "Add Context" to add new context sections
   - Use the "Copy to Clipboard" button to copy your formatted prompt
   - Use the LLM site shortcuts to quickly launch your favorite AI assistants

4. The application will automatically save your prompts and window position between sessions

## Keyboard Shortcuts

- **Ctrl+U**: Show/Hide the application
- **Tab**: Navigate between input fields
- **Esc**: Clear field focus
- **Enter**: Multi-line input in text areas

## LLM Site Shortcuts

The application includes quick-launch buttons for:
- ChatGPT
- Claude
- Grok

Clicking these buttons will copy your prompt and open the respective website.

## Data Storage

Your prompts and application settings are stored in:
- Windows: `%LOCALAPPDATA%\PromptDeck\`

## License

MIT License - See LICENSE file for details
