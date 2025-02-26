# Prompt Deck 🎴

<div align="center">
  
<img src="https://img.shields.io/badge/platform-windows-blue?style=for-the-badge&logo=windows" alt="Windows">
<img src="https://img.shields.io/badge/python-%3E%3D3.8-green?style=for-the-badge&logo=python" alt="Python">
<img src="https://img.shields.io/badge/license-MIT-orange?style=for-the-badge" alt="License">

<h3>✨ Your Smart Prompt Management Companion ✨</h3>

<p>
  <strong>Prompt Deck</strong> is a lightweight Windows utility that helps you structure and manage your LLM prompts with style.
  Perfect for power users who work with multiple AI assistants!
</p>

</div>

## ✨ Features

<table>
<tr>
  <td>🎯 <strong>Smart Layout</strong></td>
  <td>Clean, modern interface with a main prompt area and expandable context sections</td>
</tr>
<tr>
  <td>🔄 <strong>Context Management</strong></td>
  <td>Add multiple labeled context sections with character counting</td>
</tr>
<tr>
  <td>📁 <strong>File Integration</strong></td>
  <td>Drag & drop files directly into context sections with visual feedback</td>
</tr>
<tr>
  <td>📋 <strong>Quick Copy</strong></td>
  <td>One-click copying of formatted prompts</td>
</tr>
<tr>
  <td>🚀 <strong>AI Integration</strong></td>
  <td>Direct launch buttons for ChatGPT, Claude, and Grok</td>
</tr>
<tr>
  <td>💾 <strong>Persistent Storage</strong></td>
  <td>Your prompts and window position are automatically saved between sessions</td>
</tr>
</table>

## 🎨 Interface

<div align="center">
  <img src="https://via.placeholder.com/600x300?text=Prompt+Deck+Screenshot" alt="Prompt Deck Interface" width="600"/>
  <p><em>Replace this with an actual screenshot of your app</em></p>
</div>

### Main Components:
- **Main Prompt Area**: A spacious text field for your primary prompt
- **Context Sections**: Expandable sections with:
  - Notes field for labeling context
  - Content area with character counter
  - File support with drag & drop
- **Quick Actions**: 
  - Copy to Clipboard
  - Direct launch buttons for popular AI assistants

## 🚀 Installation

```bash
# Install from PyPI
pip install prompt-deck

# Or install from source
git clone https://github.com/yourusername/prompt-deck.git
cd prompt-deck
pip install -e .
```

## 💫 Usage

1. **Launch the app**:
   ```bash
   prompt-deck
   ```

2. **Working with Prompts**:
   - Type your main prompt in the top section
   - Click "Add Context" to create new context sections
   - Drag & drop files directly into the window to create file-based contexts

3. **Managing Contexts**:
   - Add notes to label your contexts
   - Type or paste content directly
   - Drop files to automatically create context sections
   - Remove contexts using the "Remove" button

4. **Using with AI Assistants**:
   - Click "Copy to Clipboard" to copy your formatted prompt
   - Use the quick-launch buttons to open your favorite AI assistant:
     - 🤖 ChatGPT (chat.openai.com)
     - 🎭 Claude (claude.ai)
     - ✨ Grok (x.com/i/grok)

## 💾 Data Storage

Your prompts and settings are automatically saved in:
```
%LOCALAPPDATA%\PromptDeck\state.json
```

## 🎨 Styling

Prompt Deck features a modern, clean interface with:
- Elegant color scheme with muted blues and grays
- Smooth animations for drag & drop
- Visual feedback for all interactions
- Comfortable spacing and typography using system fonts

## 🛠️ Technical Details

- Built with PyQt6 for a native Windows experience
- Uses system font stack for optimal rendering
- Implements efficient file handling with drag & drop support
- Saves state in JSON format for easy backup/restore

## 📜 License

<div align="center">
  
MIT License • Made with 💖 by [yada](mailto:trojblue@gmail.com)

<em>Make your prompts powerful!</em>

</div>
