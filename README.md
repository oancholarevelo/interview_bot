# AI Interview Assistant (v1.0)

This is a desktop application that acts as an AI-powered interview assistant. It's designed to help you practice for interviews by generating answers based on a specific persona ("Oliver Revelo") that you can now fully customize.

The application features a modern graphical user interface (GUI), supports speech-to-text, and includes a powerful **Answer Evaluation Mode** to provide feedback on your own answers. All your customizations are automatically saved and reloaded, making it a persistent and personalized practice tool.

## ✨ Features

  - **Modern Graphical User Interface**: A clean and responsive UI built with `ttkbootstrap` for a modern look and feel.
  - **Answer Evaluation Mode**: Toggle a switch to get constructive AI feedback on *your own* interview answers.
  - **Editable & Persistent Persona**: The AI's core personal context is fully editable within the app and is saved automatically for future sessions.
  - **Customizable Questions**: Add, edit, and delete the list of predefined interview questions directly from the settings menu.
  - **Conversation History**: Save your practice sessions to a JSON file and load them later to review your progress.
  - **Model Selection**: Easily switch between different AI models from OpenRouter and Google AI.
  - **Voice Input**: Ask questions using your voice with built-in speech recognition.
  - **Streaming Responses**: AI responses are streamed in real-time as they are generated.
  - **Utility Features**: Includes a splash screen on startup and a "Copy Last Response" button for convenience.
  - **Global Hotkey**: Toggle the visibility of the application window with a global hotkey (**F9**).

## 📋 Requirements

  - Python 3.x
  - The following Python libraries:
      - `speechrecognition`
      - `pyaudio`
      - `keyboard`
      - `python-dotenv`
      - `requests`
      - `google-generativeai`
      - `ttkbootstrap`
      - `Pillow`

## 🚀 Setup

1.  **Clone the repository or download the script.**

2.  **Install the required libraries:**
    Open your terminal or command prompt and run the following command:

    ```bash
    pip install speechrecognition pyaudio keyboard python-dotenv requests google-generativeai ttkbootstrap Pillow
    ```

3.  **Create a `.env` file:**
    In the same directory as the script, create a file named `.env`. This file will store your secret API keys.

4.  **Add your API keys to the `.env` file:**
    You will need API keys for the services you want to use (OpenRouter and/or Google AI).

    ```env
    # For OpenRouter models (Sonoma Sky, Sonoma Dusk, etc.)
    OPENROUTER_API_KEY="your_openrouter_api_key"

    # For Google AI models (Gemini 1.5 Flash)
    GOOGLE_API_KEY="your_google_ai_api_key"
    ```

    **Note:** You only need to provide keys for the models you intend to use.

## 💻 Usage

1.  **Run the script:**

    ```bash
    python interview_assistant.py
    ```

    On the first run, a `config.json` file will be created automatically to store your settings.

2.  **Using the Application:**

      - **Ask a Question**:
          - Type your question into the input box and press `Enter` or click **"Send"**.
          - Select a predefined question from the dropdown menu.
          - Click the **"🎤 Voice"** button to ask your question using your microphone.
      - **Get Feedback on Your Answers**:
        1.  Ask a question or select one from the dropdown. Let the AI answer so the question is set.
        2.  Click the **"Answer Evaluation Mode"** switch to turn it on.
        3.  Type *your own answer* to that same question in the input box and click **"Send"**.
        4.  The AI will provide feedback on your answer instead of generating one itself.
      - **Manage Conversations**:
          - Click **"💾 Save"** to save the current conversation to a file.
          - Click **"📂 Load"** to open a previously saved conversation.
          - Click **"🗑️ Clear"** to reset the conversation area.
      - **⚙️ Settings**: Click the **"Settings"** button to open a new window where you can:
          - **Change the AI model.**
          - **(👤 Personal Profile Tab)**: **Edit the entire persona** that the AI uses to answer questions.
          - **(🏢 Company Context Tab)**: Add temporary context about a specific company or job description to tailor responses.
          - **(❓ Manage Questions Tab)**: **Add, update, or delete** the questions in the dropdown menu.

## ⌨️ Hotkeys

  - **F9**: Press `F9` at any time to hide or show the application window.

## ⚙️ Configuration

The application uses two main configuration files:

  - **`.env`**: Stores your secret API keys. You must create and manage this file yourself.
  - **`config.json`**: Stores your custom persona and question list. This file is **created and managed automatically** by the application. You can also edit it manually if you prefer.

## 🤖 Available Models

The application is pre-configured to use the following models, but you can add more by editing the `MODELS` dictionary in the script.

  - **OpenRouter:**
      - Sonoma Sky
      - Sonoma Dusk
      - Gemini 2.0 Flash
  - **Google AI:**
      - Gemini 1.5 Flash
