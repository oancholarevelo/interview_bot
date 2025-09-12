# GUI AI Interview Assistant for Oliver Revelo (Improved UI/UX with Model Selection)
#
# This script creates a desktop application with a user interface
# for the interview assistant, using Python's built-in Tkinter library.
#
# Before running, please install the necessary libraries:
# pip install speechrecognition pyaudio keyboard python-dotenv requests google-generativeai

import tkinter as tk
from tkinter import scrolledtext, ttk, messagebox
import speech_recognition as sr
import google.generativeai as genai
import os
from dotenv import load_dotenv
import sys
import threading
import queue
import keyboard
import requests
import json

# --- Configuration ---
load_dotenv()

# --- Constants ---
# API Keys for different services
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY") # This is your OpenRouter API Key
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# --- Model Configuration ---
# A dictionary to hold all available models, their IDs, and the API to use.
MODELS = {
    "Sonoma Sky (OpenRouter)": {
        "id": "openrouter/sonoma-sky-alpha",
        "api": "openrouter",
        "key_name": "OPENROUTER_API_KEY"
    },
    "Sonoma Dusk (OpenRouter)": {
        "id": "openrouter/sonoma-dusk-alpha",
        "api": "openrouter",
        "key_name": "OPENROUTER_API_KEY"
    },
    "Gemini 2.0 Flash (OpenRouter)": {
        "id": "google/gemini-2.0-flash-exp:free",
        "api": "openrouter",
        "key_name": "OPENROUTER_API_KEY"
    },
    "Gemini 1.5 Flash (Google AI)": {
        "id": "gemini-1.5-flash-latest",
        "api": "google",
        "key_name": "GOOGLE_API_KEY"
    }
}


# OpenRouter API Configuration
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_ENDPOINT = f"{OPENROUTER_BASE_URL}/chat/completions"

PREDEFINED_QUESTIONS = [
    "Select a predefined question...",
    "What are your weaknesses?",
    "Describe a time you had a significant disagreement with a colleague.",
    "Tell me about the most complex technical challenge you faced on a project.",
    "How would you handle a client who insists on a feature that hurts performance?",
    "What is your process for deciding whether to switch technologies mid-project?",
    "What are your immediate steps if you discover a security vulnerability?",
    "How do you balance minimalist design with a client's business goals for more ads?",
]

# --- Personalized Context Block ---
PERSONAL_CONTEXT = """
My name is Oliver Revelo, a web developer and designer from Rizal, Philippines, specializing where clean engineering meets user-centric design. I'm set to graduate with a Diploma in Computer Engineering Technology from the Polytechnic University of the Philippines this September.

Core Philosophy & Skills:
My design philosophy is built on 'less is more'—prioritizing minimalism, clarity, and a mobile-first approach. I use generous white space and a clear visual hierarchy to create intuitive user experiences. My goal is to build clean, high-performance websites that are both beautiful and functional.

My primary tech stack for bringing this philosophy to life is Next.js with the App Router, TypeScript, and Tailwind CSS. I use these tools to build modern, performant, and scalable applications. My skillset is strong in JavaScript and TypeScript, and I'm highly proficient with design tools like Figma and Adobe Photoshop. For backend needs, I'm comfortable with Next.js API Routes and databases like Supabase and Firebase.

Experience Highlights:
- As a Web Development Intern at iBuild.PH, I designed and developed user-friendly websites and sharpened my SEO optimization skills.
- At the Google Developer Student Clubs - PUP, I contributed to UI/UX design, reinforcing my commitment to user-centric principles.
- My internship with the Risk Management Information Security Group (RMISG) gave me practical cybersecurity experience, including Linux administration and vulnerability assessment.

Proudest Project: My Personal Portfolio
My portfolio is the best example of my work. It's a project I built from the ground up, showcasing my ability to merge minimalist design with a high-performance tech stack. It's fully responsive, SEO-friendly, and deployed on Vercel, demonstrating my end-to-end project capabilities.

Career Goals & Interests:
I am passionate about building exceptional user interfaces and am particularly drawn to the gaming industry for its focus on performance and engaging design. My five-year goal is to evolve into a senior developer, where I can lead projects that push the boundaries of user experience and mentor the next generation of developers. I'm looking for a forward-thinking team where I can contribute from the ground up and help build a great company culture.
"""

# System prompt to guide the AI's behavior
SYSTEM_PROMPT_BASE = """
You are an expert career coach acting as Oliver Revelo. Your task is to answer interview questions based on the persona and context provided below.
Your answers must be concise, professional, and directly reflect Oliver's skills, experiences, design philosophy, and communication style.
Integrate the details from all provided context naturally into your answers. If company context is provided, tailor your answer to that specific company.
Start your answer directly, without introductory phrases like "As Oliver..." or "Based on my experience...".
"""

# --- UI Styling Constants ---
BG_COLOR = "#fafafa"
CARD_COLOR = "#ffffff"
TEXT_COLOR = "#2d3748"
TEXT_SECONDARY = "#718096"
PRIMARY_COLOR = "#4f46e5"
PRIMARY_HOVER = "#4338ca"
SUCCESS_COLOR = "#10b981"
ERROR_COLOR = "#ef4444"
WARNING_COLOR = "#f59e0b"
BORDER_COLOR = "#e2e8f0"

FONT_FAMILY = "Segoe UI"
FONT_SIZE_LARGE = 14
FONT_SIZE_NORMAL = 11
FONT_SIZE_SMALL = 10

PADDING_XS = 4
PADDING_SM = 8
PADDING_MD = 12
PADDING_LG = 16

class InterviewAssistantApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🎯 Oliver's AI Interview Assistant")
        self.root.geometry("950x850")
        self.root.minsize(700, 600)
        self.root.configure(bg=BG_COLOR)

        self.is_visible = True
        keyboard.add_hotkey('f9', self.toggle_visibility)

        self.is_listening = threading.Event()
        self.queue = queue.Queue()
        self.input_has_placeholder = True
        self.dropdown_clicked = False
        
        self.voice_status_label = None

        # --- Model and API State ---
        self.selected_model_name = "Sonoma Sky (OpenRouter)" # Default model
        self.gemini_model = None # To hold the initialized Google AI model object

        self._configure_styles()
        self.create_widgets()

        # --- AI and Speech Recognition Setup ---
        self._initialize_apis()
        self.recognizer = sr.Recognizer()
        self.recognizer.pause_threshold = 1.5
        self.recognizer.non_speaking_duration = 0.8
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.energy_threshold = 300
        
        self.root.after(100, self.process_queue)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.root.after(500, self._show_welcome_message)
    
    def _show_welcome_message(self):
        """Show a welcome message when the app starts."""
        welcome_msg = """Welcome to your AI Interview Assistant! 🎯

Here's how to get started:
• Use the dropdown above to select common interview questions.
• Type your own questions in the input field below.
• Click the voice button to ask questions using speech.
• Use "Settings" to select your preferred AI model and add company context.

Ready to practice? Ask me any interview question!"""
        
        self.add_message("AI:", welcome_msg, 'ai')
    
    def _configure_styles(self):
        """Configures the modern look and feel of the application."""
        style = ttk.Style(self.root)
        style.theme_use('clam')
        style.configure("TFrame", background=BG_COLOR, relief="flat")
        style.configure("Card.TFrame", background=CARD_COLOR, relief="flat", borderwidth=1)
        style.configure("TLabel", background=BG_COLOR, foreground=TEXT_COLOR, font=(FONT_FAMILY, FONT_SIZE_NORMAL))
        style.configure("Title.TLabel", background=BG_COLOR, foreground=TEXT_COLOR, font=(FONT_FAMILY, FONT_SIZE_LARGE, "bold"))
        style.configure("Secondary.TLabel", background=BG_COLOR, foreground=TEXT_SECONDARY, font=(FONT_FAMILY, FONT_SIZE_SMALL))
        style.configure("Status.TLabel", background=CARD_COLOR, foreground=TEXT_SECONDARY, font=(FONT_FAMILY, FONT_SIZE_SMALL))
        style.configure("VoiceStatus.TLabel", background=BG_COLOR, font=(FONT_FAMILY, FONT_SIZE_NORMAL))
        style.configure("TButton", foreground="white", background=PRIMARY_COLOR, font=(FONT_FAMILY, FONT_SIZE_NORMAL, "bold"), borderwidth=0, relief="flat", padding=(PADDING_MD, PADDING_SM))
        style.map("TButton", background=[('active', PRIMARY_HOVER), ('pressed', PRIMARY_HOVER)], relief=[('pressed', 'flat'), ('!pressed', 'flat')])
        style.configure("Success.TButton", foreground="white", background=SUCCESS_COLOR, font=(FONT_FAMILY, FONT_SIZE_NORMAL, "bold"), borderwidth=0, relief="flat", padding=(PADDING_MD, PADDING_SM))
        style.map("Success.TButton", background=[('active', '#059669'), ('pressed', '#059669')])
        style.configure("Danger.TButton", foreground="white", background=ERROR_COLOR, font=(FONT_FAMILY, FONT_SIZE_NORMAL, "bold"), borderwidth=0, relief="flat", padding=(PADDING_MD, PADDING_SM))
        style.map("Danger.TButton", background=[('active', '#dc2626'), ('pressed', '#dc2626')])
        style.configure("TEntry", fieldbackground=CARD_COLOR, background=CARD_COLOR, foreground=TEXT_COLOR, bordercolor=BORDER_COLOR, lightcolor=BORDER_COLOR, darkcolor=BORDER_COLOR, focuscolor=PRIMARY_COLOR, font=(FONT_FAMILY, FONT_SIZE_NORMAL), padding=(PADDING_SM, PADDING_SM))
        style.configure("TCombobox", fieldbackground=CARD_COLOR, background=CARD_COLOR, foreground=TEXT_COLOR, bordercolor=BORDER_COLOR, lightcolor=BORDER_COLOR, darkcolor=BORDER_COLOR, focuscolor=PRIMARY_COLOR, font=(FONT_FAMILY, FONT_SIZE_NORMAL), padding=(PADDING_SM, PADDING_SM))
        style.configure("TNotebook", background=BG_COLOR, borderwidth=0, tabmargins=(0, 0, 0, 0))
        style.configure("TNotebook.Tab", background=BG_COLOR, foreground=TEXT_SECONDARY, font=(FONT_FAMILY, FONT_SIZE_NORMAL, "bold"), padding=(PADDING_LG, PADDING_SM), borderwidth=0, focuscolor="none")
        style.map("TNotebook.Tab", background=[("selected", CARD_COLOR)], foreground=[("selected", PRIMARY_COLOR)], expand=[("selected", (1, 1, 1, 0))])
        style.configure("TProgressbar", background=PRIMARY_COLOR, troughcolor=BORDER_COLOR, borderwidth=0, lightcolor=PRIMARY_COLOR, darkcolor=PRIMARY_COLOR)
        
    def toggle_visibility(self):
        """Hides or shows the window when F9 is pressed."""
        if self.is_visible: self.root.withdraw()
        else: self.root.deiconify(); self.root.lift(); self.root.focus_force()
        self.is_visible = not self.is_visible

    def create_widgets(self):
        """Creates and arranges all UI components."""
        main_container = ttk.Frame(self.root, style="TFrame")
        main_container.pack(expand=True, fill='both', padx=PADDING_LG, pady=PADDING_LG)
        header_frame = self._create_header_with_settings(main_container)
        header_frame.pack(fill='x', pady=(0, PADDING_LG))
        controls_frame = self._create_controls_frame(main_container)
        controls_frame.pack(side='bottom', fill='x', pady=(PADDING_SM, 0))
        conversation_card = self._create_conversation_area(main_container)
        conversation_card.pack(expand=True, fill='both', pady=(0, PADDING_LG))
        self._init_hidden_context_data()

    def _create_header_with_settings(self, parent):
        """Creates the header section."""
        header_frame = ttk.Frame(parent, style="Card.TFrame")
        header_content = ttk.Frame(header_frame, style="Card.TFrame")
        header_content.pack(fill='x', padx=PADDING_LG, pady=PADDING_MD)
        title_frame = ttk.Frame(header_content, style="Card.TFrame")
        title_frame.pack(side='left', fill='x', expand=True)
        ttk.Label(title_frame, text="🎯 AI Interview Assistant", style="Title.TLabel").pack(anchor='w')
        ttk.Label(title_frame, text="Practice interviews with AI-powered feedback as Oliver Revelo", style="Secondary.TLabel").pack(anchor='w', pady=(2, 0))
        right_frame = ttk.Frame(header_content, style="Card.TFrame")
        right_frame.pack(side='right')
        ttk.Button(right_frame, text="⚙️ Settings", command=self.open_settings, style="TButton").pack(side='right', padx=(PADDING_SM, 0))
        self.connection_status = ttk.Label(right_frame, text="🟢 Ready", style="Secondary.TLabel")
        self.connection_status.pack(side='right', padx=(0, PADDING_SM))
        return header_frame
    
    def _create_conversation_area(self, parent):
        """Creates the conversation display area."""
        conversation_card = ttk.Frame(parent, style="Card.TFrame")
        header = ttk.Frame(conversation_card, style="Card.TFrame")
        header.pack(fill='x', padx=PADDING_LG, pady=(PADDING_MD, PADDING_SM))
        ttk.Label(header, text="💬 Conversation", style="Title.TLabel").pack(side='left')
        ttk.Button(header, text="🗑️ Clear", command=self.clear_conversation, style="TButton").pack(side='right')
        text_frame = ttk.Frame(conversation_card, style="Card.TFrame")
        text_frame.pack(expand=True, fill='both', padx=PADDING_LG, pady=(0, PADDING_MD))
        self.conversation_area = scrolledtext.ScrolledText(text_frame, wrap=tk.WORD, state='disabled', font=(FONT_FAMILY, FONT_SIZE_NORMAL), relief=tk.FLAT, borderwidth=1, bg=CARD_COLOR, fg=TEXT_COLOR, padx=PADDING_MD, pady=PADDING_MD, selectbackground=PRIMARY_COLOR, selectforeground="white")
        self._configure_tags()
        self.conversation_area.pack(expand=True, fill='both')
        return conversation_card
    
    def clear_conversation(self):
        """Clears the conversation area."""
        self.conversation_area.config(state='normal')
        self.conversation_area.delete('1.0', tk.END)
        self.conversation_area.config(state='disabled')
        self.update_status("Conversation cleared")
        
    def _init_hidden_context_data(self):
        """Initializes context data."""
        self.personal_context = PERSONAL_CONTEXT
        self.company_context = ""

    def open_settings(self):
        """Opens the settings popup window."""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("⚙️ Settings")
        settings_window.geometry("700x650")
        settings_window.configure(bg=BG_COLOR)
        settings_window.resizable(True, True)
        settings_window.transient(self.root); settings_window.grab_set()
        
        main_frame = ttk.Frame(settings_window, style="TFrame")
        main_frame.pack(expand=True, fill='both', padx=PADDING_LG, pady=PADDING_LG)
        
        # --- WIDGET PACKING ORDER HAS BEEN CHANGED ---

        # 1. Title is packed at the TOP as usual.
        ttk.Label(main_frame, text="⚙️ Interview Assistant Settings", style="Title.TLabel").pack(anchor='w', pady=(0, PADDING_LG))

        # 2. Button frame is now packed at the BOTTOM first to reserve its space.
        button_frame = ttk.Frame(main_frame, style="TFrame")
        button_frame.pack(side='bottom', fill='x', pady=(PADDING_LG, 0)) # <-- The key change is side='bottom'
        ttk.Button(button_frame, text="💾 Save Settings", command=lambda: self.save_settings(settings_window), style="Success.TButton").pack(side='right', padx=(PADDING_SM, 0))
        ttk.Button(button_frame, text="❌ Cancel", command=settings_window.destroy, style="TButton").pack(side='right')

        # 3. Model selection dropdown is packed at the TOP.
        model_frame = ttk.Frame(main_frame, style="TFrame")
        model_frame.pack(fill='x', pady=(0, PADDING_LG))
        ttk.Label(model_frame, text="🤖 Select AI Model:", style="TLabel").pack(anchor='w', pady=(0, PADDING_XS))
        model_var = tk.StringVar(value=self.selected_model_name)
        self.settings_model_dropdown = ttk.Combobox(
            model_frame, 
            textvariable=model_var, 
            values=list(MODELS.keys()), 
            state="readonly"
        )
        self.settings_model_dropdown.pack(fill='x')

        # 4. Notebook now expands to fill the REMAINING space in the middle.
        notebook = ttk.Notebook(main_frame)
        notebook.pack(expand=True, fill='both', pady=(0, PADDING_LG))
        
        # Personal Profile Tab
        personal_tab = ttk.Frame(notebook, style="TFrame")
        notebook.add(personal_tab, text="👤 Personal Profile")
        ttk.Label(personal_tab, text="Your personal context (read-only):", style="TLabel").pack(anchor='w', padx=PADDING_MD, pady=(PADDING_MD, PADDING_XS))
        personal_text = scrolledtext.ScrolledText(personal_tab, wrap=tk.WORD, font=(FONT_FAMILY, FONT_SIZE_SMALL), relief=tk.FLAT, borderwidth=1, bg=BG_COLOR, fg=TEXT_COLOR, state='disabled')
        personal_text.pack(expand=True, fill='both', padx=PADDING_MD, pady=(0, PADDING_MD))
        personal_text.config(state='normal'); personal_text.insert('1.0', self.personal_context); personal_text.config(state='disabled')
        
        # Company Context Tab
        company_tab = ttk.Frame(notebook, style="TFrame")
        notebook.add(company_tab, text="🏢 Company Context")
        ttk.Label(company_tab, text="Company information and job description:", style="TLabel").pack(anchor='w', padx=PADDING_MD, pady=(PADDING_MD, PADDING_XS))
        ttk.Label(company_tab, text="Enter company details, job requirements, or specific context to tailor responses:", style="Secondary.TLabel").pack(anchor='w', padx=PADDING_MD, pady=(0, PADDING_XS))
        self.settings_company_text = scrolledtext.ScrolledText(company_tab, wrap=tk.WORD, font=(FONT_FAMILY, FONT_SIZE_NORMAL), relief=tk.FLAT, borderwidth=1, bg=CARD_COLOR, fg=TEXT_COLOR, insertbackground=PRIMARY_COLOR)
        self.settings_company_text.pack(expand=True, fill='both', padx=PADDING_MD, pady=(0, PADDING_MD))
        self.settings_company_text.insert('1.0', self.company_context)

    def save_settings(self, settings_window):
        """Save settings from the popup window."""
        self.company_context = self.settings_company_text.get('1.0', 'end-1c').strip()
        
        # --- MODIFIED LINE ---
        # Read directly from the combobox widget instead of its variable
        self.selected_model_name = self.settings_model_dropdown.get()
        # --- End of Modified Line ---

        settings_window.destroy()
        self.update_status(f"Settings saved. Model is now {self.selected_model_name}", "💾")

    def _create_controls_frame(self, parent):
        """Creates the user input and controls section."""
        controls_card = ttk.Frame(parent, style="Card.TFrame", height=200)
        controls_card.pack_propagate(False)
        controls_content = ttk.Frame(controls_card, style="Card.TFrame")
        controls_content.pack(fill='both', expand=True, padx=PADDING_LG, pady=PADDING_MD)
        
        ttk.Label(controls_content, text="⚡ Quick Questions:", style="TLabel").pack(anchor='w', pady=(0, 5))
        self.question_var = tk.StringVar()
        self.question_dropdown = ttk.Combobox(controls_content, textvariable=self.question_var, values=PREDEFINED_QUESTIONS, state="readonly", font=(FONT_FAMILY, FONT_SIZE_NORMAL))
        self.question_dropdown.current(0)
        self.question_dropdown.pack(fill='x', pady=(0, 10))
        self.question_dropdown.bind("<<ComboboxSelected>>", self.on_dropdown_select)
        self.question_dropdown.bind("<Button-1>", self.on_dropdown_mouse_down)
        
        ttk.Label(controls_content, text="💭 Ask Your Question:", style="TLabel").pack(anchor='w', pady=(0, 5))
        input_row = ttk.Frame(controls_content, style="TFrame")
        input_row.pack(fill='x', pady=(0, 10))
        
        self.text_input = ttk.Entry(input_row, font=(FONT_FAMILY, FONT_SIZE_NORMAL))
        self.text_input.pack(side='left', expand=True, fill='x', padx=(0, 10))
        self.text_input.bind("<Return>", self.send_text_question); self.text_input.bind("<FocusIn>", self._on_input_focus_in); self.text_input.bind("<FocusOut>", self._on_input_focus_out)
        self.text_input.insert(0, "Type your interview question here..."); self.text_input.configure(foreground=TEXT_SECONDARY)
        
        self.send_button = ttk.Button(input_row, text="📤 Send", command=self.send_text_question)
        self.send_button.pack(side='left', padx=(0, 5))
        self.listen_button = ttk.Button(input_row, text="🎤 Voice", command=self.toggle_listening)
        self.listen_button.pack(side='left')
        self.voice_status_label = ttk.Label(input_row, text="⚫ Ready", style="VoiceStatus.TLabel", foreground=TEXT_SECONDARY)
        self.voice_status_label.pack(side='left', padx=(10, 0))
        
        status_section = ttk.Frame(controls_content, style="TFrame")
        status_section.pack(fill='x', pady=(15, 0))
        self.progress_bar = ttk.Progressbar(status_section, mode='indeterminate', style="TProgressbar")
        status_bar = ttk.Frame(status_section, style="Card.TFrame", relief="solid", borderwidth=1)
        status_bar.pack(fill='x', pady=(5, 0))
        status_content = ttk.Frame(status_bar, style="Card.TFrame")
        status_content.pack(fill='x', padx=PADDING_SM, pady=PADDING_XS)
        self.status_label = ttk.Label(status_content, text="ℹ️ Ready to help with your interview practice", style="Status.TLabel", font=(FONT_FAMILY, FONT_SIZE_NORMAL))
        self.status_label.pack(side='left', expand=True, fill='x')
        ttk.Label(status_content, text="F9: Toggle window", style="Status.TLabel", font=(FONT_FAMILY, FONT_SIZE_SMALL)).pack(side='right')
        
        return controls_card
    
    def _on_input_focus_in(self, event):
        """Handle focus in for input placeholder."""
        if self.input_has_placeholder:
            self.text_input.delete(0, tk.END); self.text_input.configure(foreground=TEXT_COLOR)
            self.input_has_placeholder = False
    
    def _on_input_focus_out(self, event):
        """Handle focus out for input placeholder."""
        if not self.text_input.get().strip():
            self.text_input.insert(0, "Type your interview question here...")
            self.text_input.configure(foreground=TEXT_SECONDARY)
            self.input_has_placeholder = True

    def _configure_tags(self):
        """Configures text styles for the conversation area."""
        self.conversation_area.tag_configure('you', foreground=PRIMARY_COLOR, font=(FONT_FAMILY, FONT_SIZE_NORMAL, "bold"))
        self.conversation_area.tag_configure('you_bg', background="#f0f7ff", relief=tk.FLAT, borderwidth=1, lmargin1=10, lmargin2=10, rmargin=10)
        self.conversation_area.tag_configure('ai', foreground=SUCCESS_COLOR, font=(FONT_FAMILY, FONT_SIZE_NORMAL, "bold"))
        self.conversation_area.tag_configure('ai_bg', background="#f0fdf4", relief=tk.FLAT, borderwidth=1, lmargin1=10, lmargin2=10, rmargin=10)
        self.conversation_area.tag_configure('text', foreground=TEXT_COLOR, font=(FONT_FAMILY, FONT_SIZE_NORMAL), spacing3=10)
        self.conversation_area.tag_configure('error', foreground=ERROR_COLOR, font=(FONT_FAMILY, FONT_SIZE_NORMAL, "italic"), background="#fef2f2")

    def _initialize_apis(self):
        """Initializes API clients and checks for keys."""
        openrouter_ok = bool(OPENROUTER_API_KEY)
        google_ok = False
        
        if GOOGLE_API_KEY:
            try:
                genai.configure(api_key=GOOGLE_API_KEY)
                self.gemini_model = genai.GenerativeModel(model_name='gemini-1.5-flash-latest')
                google_ok = True
            except Exception as e:
                print(f"Failed to initialize Google AI: {e}")

        status = []
        if openrouter_ok: status.append("OpenRouter Ready")
        if google_ok: status.append("Google AI Ready")
        
        if not status: self.update_status("Error: No API keys found in .env file.", "❌", is_error=True)
        else: self.update_status(" & ".join(status), "✅")

    def _generate_full_prompt(self, question):
        """Dynamically builds the prompt with personal and company context."""
        full_prompt = f"{SYSTEM_PROMPT_BASE}\n\n--- OLIVER'S CONTEXT ---\n{self.personal_context}\n--- END OF OLIVER'S CONTEXT ---\n\n"
        if self.company_context.strip():
            full_prompt += f"--- COMPANY CONTEXT ---\n{self.company_context}\n--- END OF COMPANY CONTEXT ---\n\n"
        full_prompt += f"Now, answer the following question:\nQUESTION: {question}"
        return full_prompt
    
    def _set_ui_state(self, enabled):
        """Enables or disables input controls."""
        state = 'normal' if enabled else 'disabled'
        for widget in [self.text_input, self.send_button, self.listen_button]:
            widget.config(state=state)
        self.question_dropdown.config(state='readonly' if enabled else 'disabled')
        
        if enabled:
            self.progress_bar.stop(); self.progress_bar.pack_forget()
            self.update_status(f"Ready ({self.selected_model_name})", "🟢")
            if hasattr(self, 'connection_status'): self.connection_status.config(text="🟢 Ready", foreground=SUCCESS_COLOR)
        else:
            self.progress_bar.pack(fill='x', pady=(0, 5)); self.progress_bar.start()
            self.update_status(f"Generating with {self.selected_model_name}...", "🤖")
            if hasattr(self, 'connection_status'): self.connection_status.config(text="🤖 Thinking...", foreground=WARNING_COLOR)

    def submit_question_to_ai(self, text):
        """Handles the logic of submitting a question to the AI."""
        if not text: return
        self.add_message("You:", text, 'you')
        self._set_ui_state(enabled=False)
        threading.Thread(target=self.get_ai_answer, args=(text,), daemon=True).start()

    def send_text_question(self, event=None):
        text = self.text_input.get().strip()
        if text and not self.input_has_placeholder:
            self.submit_question_to_ai(text)
            self.text_input.delete(0, tk.END); self._on_input_focus_out(None)

    def on_dropdown_mouse_down(self, event=None):
        self.dropdown_clicked = True
        
    def on_dropdown_select(self, event=None):
        """Handle dropdown selection."""
        question = self.question_var.get()
        if question != PREDEFINED_QUESTIONS[0] and self.dropdown_clicked:
            self.submit_question_to_ai(question)
            self.question_dropdown.current(0)
            self.root.focus_set()
        self.dropdown_clicked = False

    def toggle_listening(self):
        if self.is_listening.is_set(): self.is_listening.clear()
        else: self.is_listening.set(); threading.Thread(target=self._listen_and_process, daemon=True).start()

    def _listen_and_process(self):
        """Handles the voice recognition process."""
        self.queue.put(("button_update", ("🔴 Stop", "Danger.TButton")))
        self.queue.put(("voice_status", ("🔵 Calibrating...", PRIMARY_COLOR)))
        with sr.Microphone() as source:
            try:
                self.recognizer.adjust_for_ambient_noise(source, duration=1.5)
                self.queue.put(("voice_status", ("🟢 Listening...", SUCCESS_COLOR)))
                audio = self.recognizer.listen(source, timeout=10, phrase_time_limit=30)
                self.queue.put(("voice_status", ("🟠 Processing...", WARNING_COLOR)))
                text = self.recognizer.recognize_google(audio, language='en-US')
                if text.strip():
                    self.queue.put(("voice_status", (f"✔️ Recognized", SUCCESS_COLOR)))
                    self.queue.put(("submit_question", text))
                else: self.queue.put(("voice_status", ("⚠️ No speech", WARNING_COLOR)))
            except sr.WaitTimeoutError: self.queue.put(("voice_status", ("⏱️ Timed out", WARNING_COLOR)))
            except sr.UnknownValueError: self.queue.put(("voice_status", ("❌ Could not understand", ERROR_COLOR)))
            except sr.RequestError as e: self.queue.put(("voice_status", ("📡 Network error", ERROR_COLOR))); print(f"Speech service error: {e}")
            except Exception as e: self.queue.put(("voice_status", ("🎤 Mic error", ERROR_COLOR))); print(f"An unexpected mic error: {e}")
            finally:
                self.is_listening.clear()
                self.queue.put(("button_update", ("🎤 Voice", "TButton")))
                self.root.after(2000, lambda: self.queue.put(("voice_status", ("⚫ Ready", TEXT_SECONDARY))))

    def get_ai_answer(self, question):
        """Dispatcher function to call the correct API based on user selection."""
        model_config = MODELS.get(self.selected_model_name)
        if not model_config:
            self.queue.put(("add_message", ("Error:", f"Model '{self.selected_model_name}' not configured.", "error")))
            self.queue.put(("set_ui_state", True))
            return
            
        api_type = model_config['api']
        
        # Check for API key before proceeding
        api_key_name = model_config.get("key_name")
        api_key = globals().get(api_key_name)
        if not api_key:
            error_msg = f"\n❌ API Key Error: {api_key_name} not found in your .env file. Please add it to use this model."
            self.queue.put(("add_message", ("Error:", error_msg, "error")))
            self.queue.put(("set_ui_state", True))
            return

        full_prompt = self._generate_full_prompt(question)
        self.queue.put(("add_message", ("AI:", "", "ai")))

        try:
            if api_type == "openrouter":
                self._get_openrouter_answer(full_prompt, model_config)
            elif api_type == "google":
                self._get_google_gemini_answer(full_prompt, model_config)
        except Exception as e:
            error_msg = f"\n❌ Unexpected Error during API call: {str(e)}"
            self.queue.put(("add_message", ("Error:", error_msg, "error")))
        finally:
            self.queue.put(("set_ui_state", True))

    def _get_openrouter_answer(self, full_prompt, model_config):
        """Gets a streaming answer from the OpenRouter API."""
        payload = {
            "model": model_config['id'],
            "messages": [{"role": "user", "content": full_prompt}],
            "stream": True, "temperature": 0.7, "max_tokens": 1000
        }
        headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}
        
        try:
            response = requests.post(OPENROUTER_ENDPOINT, json=payload, headers=headers, stream=True, timeout=30)
            response.raise_for_status()
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        data = line_str[6:]
                        if data == '[DONE]': break
                        try:
                            chunk = json.loads(data)
                            if 'choices' in chunk and chunk['choices'][0]['delta'].get('content'):
                                text_chunk = chunk['choices'][0]['delta']['content']
                                self.queue.put(("stream_update", text_chunk))
                        except json.JSONDecodeError: continue
        except requests.exceptions.RequestException as e:
            error_msg = f"\n❌ API Connection Error: {str(e)}"
            self.queue.put(("stream_update", error_msg))
            self.queue.put(("status_update", ("API connection failed", "❌")))

    def _get_google_gemini_answer(self, full_prompt, model_config):
        """Gets a streaming answer from the Google AI API."""
        if not self.gemini_model:
            error_msg = "\n❌ Google AI model is not initialized. Check your GOOGLE_API_KEY."
            self.queue.put(("stream_update", error_msg))
            return
        
        try:
            response_stream = self.gemini_model.generate_content(full_prompt, stream=True)
            for chunk in response_stream:
                if chunk.text:
                    self.queue.put(("stream_update", chunk.text))
        except Exception as e:
            error_msg = f"\n❌ Google AI Error: {str(e)}"
            self.queue.put(("stream_update", error_msg))
            self.queue.put(("status_update", ("Google AI request failed", "❌")))

    def process_queue(self):
        """Processes messages from other threads to update the UI safely."""
        try:
            while True:
                message_type, data = self.queue.get_nowait()
                if message_type == "status_update": self.update_status(data[0], data[1])
                elif message_type == "submit_question": self.submit_question_to_ai(data)
                elif message_type == "add_message": self.add_message(data[0], data[1], data[2])
                elif message_type == "stream_update": self.append_to_last_message(data)
                elif message_type == "set_ui_state": self._set_ui_state(data)
                elif message_type == "button_update":
                    self.listen_button.config(text=data[0])
                    if len(data) > 1: self.listen_button.configure(style=data[1])
                elif message_type == "voice_status":
                    if self.voice_status_label: self.voice_status_label.config(text=data[0], foreground=data[1])
        except queue.Empty: pass
        finally: self.root.after(100, self.process_queue)

    def update_status(self, text, icon="ℹ️", is_error=False):
        """Update status with icon and color coding."""
        if hasattr(self, 'status_label'):
            color = ERROR_COLOR if is_error else TEXT_COLOR
            self.status_label.config(text=f"{icon} {text}", foreground=color)
            self.root.update_idletasks()

    def add_message(self, speaker, text, tag):
        """Add a formatted message to the conversation area."""
        self.conversation_area.config(state='normal')
        if self.conversation_area.get('1.0', tk.END).strip():
            self.conversation_area.insert(tk.END, "\n" + "─" * 50 + "\n\n")
        
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M")
        
        speaker_icon = "👤" if speaker == "You:" else "🤖"
        self.conversation_area.insert(tk.END, f"{speaker_icon} {speaker} ({timestamp})\n", tag)
        start_pos = self.conversation_area.index("end-1c linestart")
        
        self.conversation_area.insert(tk.END, text, 'text')
        
        bg_tag = 'you_bg' if tag == 'you' else 'ai_bg'
        self.conversation_area.tag_add(bg_tag, start_pos, self.conversation_area.index("end-1c"))
        
        self.conversation_area.config(state='disabled'); self.conversation_area.see(tk.END)

    def append_to_last_message(self, text_chunk):
        self.conversation_area.config(state='normal')
        self.conversation_area.insert(tk.END, text_chunk, 'text')
        self.conversation_area.config(state='disabled'); self.conversation_area.see(tk.END)

    def on_closing(self):
        self.is_listening.clear()
        self.root.destroy()

if __name__ == "__main__":
    if not sr.Microphone.list_microphone_names():
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Microphone Error", "No microphone found. Please connect a microphone and restart.")
        sys.exit(1)
        
    root = tk.Tk()
    app = InterviewAssistantApp(root)
    root.mainloop()