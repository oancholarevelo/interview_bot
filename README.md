# AI Interview Assistant

This is a desktop application that acts as an AI-powered interview assistant. It's designed to help users practice for interviews by answering questions as a specific persona (in this case, "Oliver Revelo"). The application features a graphical user interface (GUI) built with Tkinter, supports speech-to-text for asking questions, and allows for the selection of different large language models (LLMs) to generate answers.

## Features

- **Graphical User Interface**: A clean and modern UI built with Tkinter.
- **Model Selection**: Easily switch between different AI models from OpenRouter and Google AI.
- **Voice Input**: Ask questions using your voice with speech recognition.
- **Predefined Questions**: A dropdown of common interview questions to get started quickly.
- **Personalized Context**: The AI's answers are based on a predefined personal context, which can be customized.
- **Company-Specific Context**: Add context about a specific company or job description to tailor the AI's answers.
- **Streaming Responses**: AI responses are streamed in real-time as they are generated.
- **Global Hotkey**: Toggle the visibility of the application window with a global hotkey (F9).

## Requirements

- Python 3.x
- The following Python libraries:
  - `speechrecognition`
  - `pyaudio`
  - `keyboard`
  - `python-dotenv`
  - `requests`
  - `google-generativeai`

## Setup

1.  **Clone the repository or download the script.**

2.  **Install the required libraries:**
    Open your terminal or command prompt and run the following command:
    ```bash
    pip install speechrecognition pyaudio keyboard python-dotenv requests google-generativeai
    ```

3.  **Create a `.env` file:**
    In the same directory as the script, create a file named `.env`. This file will store your API keys.

4.  **Add your API keys to the `.env` file:**
    You will need API keys for the services you want to use (OpenRouter and/or Google AI).

    ```env
    # For OpenRouter models (Sonoma Sky, Sonoma Dusk, etc.)
    OPENROUTER_API_KEY="your_openrouter_api_key"

    # For Google AI models (Gemini 1.5 Flash)
    GOOGLE_API_KEY="your_google_ai_api_key"
    ```
    **Note:** `OPENROUTER_API_KEY` is your OpenRouter API key.

## Usage

1.  **Run the script:**
    ```bash
    python interview_assistant.py
    ```

2.  **Using the Application:**
    - **Select a Model**: Use the "Settings" menu to choose your preferred AI model.
    - **Ask a Question**:
        - Type your question into the input box and press `Enter` or click "Send".
        - Select a predefined question from the dropdown menu.
        - Click the "Voice" button to ask your question using your microphone.
    - **Clear Conversation**: Click the "Clear" button to reset the conversation.
    - **Settings**: Click the "Settings" button to:
        - Change the AI model.
        - Add company-specific context to tailor the AI's responses.

## Hotkeys

-   **F9**: Press `F9` to hide or show the application window.

## Available Models

The application is pre-configured to use the following models:

-   **OpenRouter:**
    -   Sonoma Sky
    -   Sonoma Dusk
    -   Gemini 2.0 Flash
-   **Google AI:**
    -   Gemini 1.5 Flash

You can add more models by editing the `MODELS` dictionary in the `interview_assistant.py` script.
