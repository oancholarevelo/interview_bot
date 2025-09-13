# GUI AI Interview Assistant for Oliver Revelo (v3.0 - Dynamic & Persistent Config)
#
# This script creates a desktop application with a user interface
# for the interview assistant, using the ttkbootstrap library for a modern look.
# It now saves personal context and predefined questions to a config.json file.
#
# Before running, please install the necessary libraries:
# pip install speechrecognition pyaudio keyboard python-dotenv requests google-generativeai ttkbootstrap Pillow

import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog, Listbox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
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
import datetime

# --- Configuration ---
load_dotenv()
CONFIG_FILE = "config.json"

# --- Constants ---
# API Keys for different services
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY") # This is your OpenRouter API Key
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# --- Model Configuration ---
MODELS = {
    "Sonoma Sky (OpenRouter)": {"id": "openrouter/sonoma-sky-alpha", "api": "openrouter", "key_name": "OPENROUTER_API_KEY"},
    "Sonoma Dusk (OpenRouter)": {"id": "openrouter/sonoma-dusk-alpha", "api": "openrouter", "key_name": "OPENROUTER_API_KEY"},
    "Gemini 2.0 Flash (OpenRouter)": {"id": "google/gemini-2.0-flash-exp:free", "api": "openrouter", "key_name": "OPENROUTER_API_KEY"},
    "Gemini 1.5 Flash (Google AI)": {"id": "gemini-1.5-flash-latest", "api": "google", "key_name": "GOOGLE_API_KEY"}
}

# OpenRouter API Configuration
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_ENDPOINT = f"{OPENROUTER_BASE_URL}/chat/completions"

# --- Default Data (used only if config.json is not found) ---
DEFAULT_PREDEFINED_QUESTIONS = [
    "Select a predefined question...",
    "What are your weaknesses?",
    "Describe a time you had a significant disagreement with a colleague.",
    "Tell me about the most complex technical challenge you faced on a project.",
    "How would you handle a client who insists on a feature that hurts performance?",
]

DEFAULT_PERSONAL_CONTEXT = """
My name is Oliver Revelo, a web developer and designer from Rizal, Philippines, specializing where clean engineering meets user-centric design. I'm set to graduate with a Diploma in Computer Engineering Technology from the Polytechnic University of the Philippines this September.

Core Philosophy & Skills:
My design philosophy is built on 'less is more'—prioritizing minimalism, clarity, and a mobile-first approach. I use generous white space and a clear visual hierarchy to create intuitive user experiences. My goal is to build clean, high-performance websites that are both beautiful and functional.

My primary tech stack for bringing this philosophy to life is Next.js with the App Router, TypeScript, and Tailwind CSS. I use these tools to build modern, performant, and scalable applications. My skillset is strong in JavaScript and TypeScript, and I'm highly proficient with design tools like Figma and Adobe Photoshop. For backend needs, I'm comfortable with Next.js API Routes and databases like Supabase and Firebase.
"""

# --- System Prompts ---
SYSTEM_PROMPT_BASE = """
You are an expert career coach acting as Oliver Revelo. Your task is to answer interview questions based on the persona and context provided below.
Your answers must be concise, professional, and directly reflect Oliver's skills, experiences, design philosophy, and communication style.
Integrate the details from all provided context naturally into your answers. If company context is provided, tailor your answer to that specific company.
Start your answer directly, without introductory phrases like "As Oliver..." or "Based on my experience...".
"""

SYSTEM_PROMPT_EVALUATION = """
You are an expert career coach. Your task is to evaluate an interview answer provided by a user who is role-playing as Oliver Revelo.
First, review Oliver's personal and professional context.
Then, review the user's answer to the interview question.
Provide constructive, concise feedback in markdown format. Focus on these points:
- **Strengths:** What did the user do well? Did they align with Oliver's persona?
- **Areas for Improvement:** How could the answer be stronger, more concise, or better aligned with Oliver's skills and philosophy?
- **Suggested Answer:** Provide an improved, example answer that Oliver might give.
Your feedback should be encouraging and aim to help the user improve.
"""

# --- UI Styling Constants ---
FONT_FAMILY = "Segoe UI"

class InterviewAssistantApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🎯 Oliver's AI Interview Assistant")
        self.root.geometry("1000x850")
        self.root.minsize(800, 700)

        # --- Load Configuration ---
        self._load_config()

        # --- State Management ---
        self.is_visible = True
        self.is_listening = threading.Event()
        self.queue = queue.Queue()
        self.input_has_placeholder = True
        self.dropdown_clicked = False
        self.selected_model_name = "Sonoma Sky (OpenRouter)"
        self.gemini_model = None
        self.company_context = ""
        self.conversation_history = []
        self.last_ai_response = ""
        self.last_question_asked = ""
        self.evaluation_mode = tk.BooleanVar(value=False)
        
        keyboard.add_hotkey('f9', self.toggle_visibility)
        self.create_widgets()

        # --- AI and Speech Recognition Setup ---
        self._initialize_apis()
        self.recognizer = sr.Recognizer()
        self.recognizer.pause_threshold = 1.5
        self.recognizer.dynamic_energy_threshold = True
        
        self.root.after(100, self.process_queue)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.after(500, self._show_welcome_message)

    def _load_config(self):
        """Loads personal context and questions from config.json, or creates it with defaults."""
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.personal_context = config.get("personal_context", DEFAULT_PERSONAL_CONTEXT)
                self.predefined_questions = config.get("predefined_questions", DEFAULT_PREDEFINED_QUESTIONS)
        except (FileNotFoundError, json.JSONDecodeError):
            self.personal_context = DEFAULT_PERSONAL_CONTEXT
            self.predefined_questions = list(DEFAULT_PREDEFINED_QUESTIONS)
            self._save_config() # Create the file for the first time

    def _save_config(self):
        """Saves the current personal context and questions to config.json."""
        # Ensure the placeholder isn't duplicated
        questions_to_save = [q for q in self.predefined_questions if q != DEFAULT_PREDEFINED_QUESTIONS[0]]
        questions_to_save.insert(0, DEFAULT_PREDEFINED_QUESTIONS[0])

        config = {
            "personal_context": self.personal_context,
            "predefined_questions": questions_to_save
        }
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)

    def on_closing(self):
        """Handle window closing event."""
        self._save_config() # Save config on exit
        self.is_listening.clear()
        self.root.destroy()
    
    def _show_welcome_message(self):
        welcome_msg = """Welcome to your AI Interview Assistant! 🎯

Here's how to get started:
• **Ask Questions**: Use the dropdown or type your own question.
• **Evaluation Mode**: Toggle the switch to get feedback on *your own* answers.
• **Save/Load**: Use the header buttons to save or load practice sessions.
• **Settings**: Configure the AI model, company context, and your personal profile.

Ready to practice? Ask me any interview question!"""
        self.add_message("AI:", welcome_msg, 'ai', is_welcome=True)
    
    def toggle_visibility(self):
        if self.is_visible: self.root.withdraw()
        else: self.root.deiconify(); self.root.lift(); self.root.focus_force()
        self.is_visible = not self.is_visible

    def create_widgets(self):
        """Creates and arranges all UI components using a grid layout."""
        main_container = ttk.Frame(self.root, padding=10)
        main_container.pack(expand=True, fill='both')
        
        main_container.rowconfigure(1, weight=1)
        main_container.columnconfigure(0, weight=1)

        header_frame = self._create_header_frame(main_container)
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        conversation_frame = self._create_conversation_area(main_container)
        conversation_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 10))

        controls_frame = self._create_controls_frame(main_container)
        controls_frame.grid(row=2, column=0, sticky="ew")

    def _create_header_frame(self, parent):
        header_frame = ttk.Frame(parent, padding=15, bootstyle="light")
        header_frame.columnconfigure(0, weight=1)

        title_frame = ttk.Frame(header_frame, bootstyle="light")
        title_frame.grid(row=0, column=0, sticky="w")
        ttk.Label(title_frame, text="🎯 AI Interview Assistant", font=(FONT_FAMILY, 16, "bold"), bootstyle="inverse-light").pack(anchor='w')
        ttk.Label(title_frame, text="Practice interviews with AI-powered feedback", bootstyle="secondary-inverse-light").pack(anchor='w', pady=(2, 0))

        buttons_frame = ttk.Frame(header_frame, bootstyle="light")
        buttons_frame.grid(row=0, column=1, sticky="e")
        ttk.Button(buttons_frame, text="💾 Save", command=self.save_conversation, bootstyle="secondary-outline").pack(side='left', padx=5)
        ttk.Button(buttons_frame, text="📂 Load", command=self.load_conversation, bootstyle="secondary-outline").pack(side='left', padx=5)
        ttk.Button(buttons_frame, text="⚙️ Settings", command=self.open_settings, bootstyle="primary").pack(side='left', padx=5)
        
        return header_frame

    def _create_conversation_area(self, parent):
        conv_card = ttk.Frame(parent, padding=15, bootstyle="light")
        conv_card.rowconfigure(1, weight=1)
        conv_card.columnconfigure(0, weight=1)

        header = ttk.Frame(conv_card, bootstyle="light")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        header.columnconfigure(0, weight=1)
        ttk.Label(header, text="💬 Conversation", font=(FONT_FAMILY, 14, "bold"), bootstyle="inverse-light").grid(row=0, column=0, sticky="w")
        
        button_group = ttk.Frame(header, bootstyle="light")
        button_group.grid(row=0, column=1, sticky="e")
        ttk.Button(button_group, text="📋 Copy Last", command=self.copy_last_response, bootstyle="info-outline").pack(side='left', padx=5)
        ttk.Button(button_group, text="🗑️ Clear", command=self.clear_conversation, bootstyle="danger-outline").pack(side='left', padx=5)

        self.conversation_area = scrolledtext.ScrolledText(conv_card, wrap=tk.WORD, state='disabled', font=(FONT_FAMILY, 11), relief=tk.FLAT, borderwidth=1, padx=10, pady=10)
        self.conversation_area.grid(row=1, column=0, sticky="nsew")
        self._configure_tags()
        return conv_card
    
    def _create_controls_frame(self, parent):
        controls_card = ttk.Frame(parent, padding=15, bootstyle="light")
        controls_card.columnconfigure(0, weight=1)

        ttk.Label(controls_card, text="⚡ Quick Questions:", font=(FONT_FAMILY, 10, "bold")).grid(row=0, column=0, sticky="w", columnspan=2, pady=(0, 5))
        self.question_var = tk.StringVar()
        self.question_dropdown = ttk.Combobox(controls_card, textvariable=self.question_var, values=self.predefined_questions, state="readonly")
        self.question_dropdown.current(0)
        self.question_dropdown.grid(row=1, column=0, sticky="ew", columnspan=2, pady=(0, 10))
        self.question_dropdown.bind("<<ComboboxSelected>>", self.on_dropdown_select)
        self.question_dropdown.bind("<Button-1>", lambda e: setattr(self, 'dropdown_clicked', True))
        
        ttk.Label(controls_card, text="💭 Your Input:", font=(FONT_FAMILY, 10, "bold")).grid(row=2, column=0, sticky="w", columnspan=2, pady=(0, 5))
        input_row = ttk.Frame(controls_card, bootstyle="light")
        input_row.grid(row=3, column=0, sticky="ew", columnspan=2, pady=(0, 10))
        input_row.columnconfigure(0, weight=1)
        
        self.text_input = ttk.Entry(input_row, font=(FONT_FAMILY, 11))
        self.text_input.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.text_input.bind("<Return>", self.send_text_question); self.text_input.bind("<FocusIn>", self._on_input_focus_in); self.text_input.bind("<FocusOut>", self._on_input_focus_out)
        self.text_input.insert(0, "Type your interview question or answer here..."); self.text_input.config(bootstyle="secondary")
        
        self.send_button = ttk.Button(input_row, text="📤 Send", command=self.send_text_question, bootstyle="primary")
        self.send_button.grid(row=0, column=1, padx=(0, 5))
        self.listen_button = ttk.Button(input_row, text="🎤 Voice", command=self.toggle_listening, bootstyle="info")
        self.listen_button.grid(row=0, column=2)

        status_section = ttk.Frame(controls_card, bootstyle="light")
        status_section.grid(row=4, column=0, sticky="ew", columnspan=2, pady=(5, 0))
        status_section.columnconfigure(1, weight=1)

        self.eval_switch = ttk.Checkbutton(status_section, text="Answer Evaluation Mode", variable=self.evaluation_mode, bootstyle="success-round-toggle")
        self.eval_switch.grid(row=0, column=0, sticky="w")
        self.voice_status_label = ttk.Label(status_section, text="⚫ Ready", bootstyle="secondary")
        self.voice_status_label.grid(row=0, column=1, sticky="w", padx=20)
        
        self.status_label = ttk.Label(status_section, text="ℹ️ Ready to practice!", bootstyle="secondary")
        self.status_label.grid(row=0, column=2, sticky="e")
        
        self.progress_bar = ttk.Progressbar(controls_card, mode='indeterminate', bootstyle="primary")
        self.progress_bar.grid(row=5, column=0, sticky="ew", columnspan=2, pady=(10, 0))
        self.progress_bar.grid_remove() 

        return controls_card

    def _on_input_focus_in(self, event):
        if self.input_has_placeholder:
            self.text_input.delete(0, tk.END); self.text_input.config(bootstyle="primary")
            self.input_has_placeholder = False
    
    def _on_input_focus_out(self, event):
        if not self.text_input.get().strip():
            self.text_input.insert(0, "Type your interview question or answer here...")
            self.text_input.config(bootstyle="secondary")
            self.input_has_placeholder = True

    def _configure_tags(self):
        self.conversation_area.tag_configure('you', foreground="#0d6efd", font=(FONT_FAMILY, 11, "bold"))
        self.conversation_area.tag_configure('ai', foreground="#198754", font=(FONT_FAMILY, 11, "bold"))
        self.conversation_area.tag_configure('eval', foreground="#fd7e14", font=(FONT_FAMILY, 11, "bold"))
        self.conversation_area.tag_configure('text', font=(FONT_FAMILY, 11), spacing3=10)
        self.conversation_area.tag_configure('error', foreground="#dc3545", font=(FONT_FAMILY, 11, "italic"))
    
    def clear_conversation(self):
        self.conversation_area.config(state='normal')
        self.conversation_area.delete('1.0', tk.END)
        self.conversation_area.config(state='disabled')
        self.conversation_history.clear()
        self.last_ai_response = ""
        self.update_status("Conversation cleared")

    def open_settings(self):
        settings_window = tk.Toplevel(self.root)
        settings_window.title("⚙️ Settings")
        settings_window.geometry("800x700")
        settings_window.transient(self.root); settings_window.grab_set()
        
        main_frame = ttk.Frame(settings_window, padding=20)
        main_frame.pack(expand=True, fill='both')
        ttk.Label(main_frame, text="⚙️ Interview Assistant Settings", font=(FONT_FAMILY, 16, "bold")).pack(anchor='w', pady=(0, 20))
        
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(side='bottom', fill='x', pady=(20, 0))
        ttk.Button(button_frame, text="💾 Save & Close", command=lambda: self.save_settings(settings_window), bootstyle="success").pack(side='right', padx=(10, 0))
        
        model_frame = ttk.Frame(main_frame)
        model_frame.pack(fill='x', pady=(0, 20))
        ttk.Label(model_frame, text="🤖 Select AI Model:", font=(FONT_FAMILY, 10, "bold")).pack(anchor='w', pady=(0, 5))
        self.settings_model_dropdown = ttk.Combobox(model_frame, textvariable=tk.StringVar(value=self.selected_model_name), values=list(MODELS.keys()), state="readonly")
        self.settings_model_dropdown.pack(fill='x')

        notebook = ttk.Notebook(main_frame, bootstyle="primary")
        notebook.pack(expand=True, fill='both')
        
        personal_tab = ttk.Frame(notebook, padding=10)
        notebook.add(personal_tab, text="👤 Personal Profile")
        ttk.Label(personal_tab, text="Edit your personal context below:", font=(FONT_FAMILY, 10, "bold")).pack(anchor='w', pady=5)
        self.settings_personal_text = scrolledtext.ScrolledText(personal_tab, wrap=tk.WORD, font=(FONT_FAMILY, 10))
        self.settings_personal_text.pack(expand=True, fill='both')
        self.settings_personal_text.insert('1.0', self.personal_context)
        
        company_tab = ttk.Frame(notebook, padding=10)
        notebook.add(company_tab, text="🏢 Company Context")
        ttk.Label(company_tab, text="Enter company info, job description, etc.:", font=(FONT_FAMILY, 10, "bold")).pack(anchor='w', pady=5)
        self.settings_company_text = scrolledtext.ScrolledText(company_tab, wrap=tk.WORD, font=(FONT_FAMILY, 11))
        self.settings_company_text.pack(expand=True, fill='both')
        self.settings_company_text.insert('1.0', self.company_context)

        questions_tab = ttk.Frame(notebook, padding=10)
        notebook.add(questions_tab, text="❓ Manage Questions")
        self._create_question_manager_tab(questions_tab)

    def _create_question_manager_tab(self, parent_tab):
        parent_tab.columnconfigure(0, weight=1)
        parent_tab.rowconfigure(1, weight=1)
        ttk.Label(parent_tab, text="Manage the list of predefined questions.", font=(FONT_FAMILY, 10, "bold")).grid(row=0, column=0, columnspan=2, sticky='w', pady=(0, 10))

        list_frame = ttk.Frame(parent_tab)
        list_frame.grid(row=1, column=0, columnspan=2, sticky='nsew', pady=(0, 10))
        list_frame.rowconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)
        self.settings_question_listbox = Listbox(list_frame, font=(FONT_FAMILY, 10), height=10)
        self.settings_question_listbox.grid(row=0, column=0, sticky='nsew')
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.settings_question_listbox.yview)
        scrollbar.grid(row=0, column=1, sticky='ns')
        self.settings_question_listbox.config(yscrollcommand=scrollbar.set)
        
        self._refresh_question_listbox()
        self.settings_question_listbox.bind('<<ListboxSelect>>', self._on_question_select_in_settings)

        ttk.Label(parent_tab, text="Question Text:").grid(row=2, column=0, columnspan=2, sticky='w', pady=(5,0))
        self.settings_question_entry = ttk.Entry(parent_tab, font=(FONT_FAMILY, 10))
        self.settings_question_entry.grid(row=3, column=0, columnspan=2, sticky='ew', pady=5)
        
        button_frame = ttk.Frame(parent_tab)
        button_frame.grid(row=4, column=0, columnspan=2, sticky='ew')
        ttk.Button(button_frame, text="➕ Add New", command=self._add_question, bootstyle="success-outline").pack(side='left', padx=(0, 5))
        ttk.Button(button_frame, text="💾 Update", command=self._update_question, bootstyle="info-outline").pack(side='left', padx=5)
        ttk.Button(button_frame, text="❌ Delete", command=self._delete_question, bootstyle="danger-outline").pack(side='left', padx=5)
        ttk.Button(button_frame, text="Clear Entry", command=lambda: self.settings_question_entry.delete(0, tk.END), bootstyle="secondary-outline").pack(side='left', padx=5)
    
    def _refresh_question_listbox(self):
        self.settings_question_listbox.delete(0, tk.END)
        # We edit the list without the placeholder
        editable_questions = [q for q in self.predefined_questions if q != DEFAULT_PREDEFINED_QUESTIONS[0]]
        for q in editable_questions:
            self.settings_question_listbox.insert(tk.END, q)
    
    def _on_question_select_in_settings(self, event):
        selected_indices = self.settings_question_listbox.curselection()
        if not selected_indices: return
        selected_question = self.settings_question_listbox.get(selected_indices[0])
        self.settings_question_entry.delete(0, tk.END)
        self.settings_question_entry.insert(0, selected_question)
        
    def _add_question(self):
        new_question = self.settings_question_entry.get().strip()
        editable_questions = [q for q in self.predefined_questions if q != DEFAULT_PREDEFINED_QUESTIONS[0]]
        if new_question and new_question not in editable_questions:
            self.predefined_questions.append(new_question)
            self._refresh_question_listbox()
            self.settings_question_entry.delete(0, tk.END)
            self.settings_question_listbox.selection_clear(0, tk.END)
    
    def _update_question(self):
        selected_indices = self.settings_question_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("No Selection", "Please select a question to update.")
            return
        updated_text = self.settings_question_entry.get().strip()
        if not updated_text:
            messagebox.showwarning("Empty Question", "Question text cannot be empty.")
            return
        
        original_question = self.settings_question_listbox.get(selected_indices[0])
        try:
            original_index = self.predefined_questions.index(original_question)
            self.predefined_questions[original_index] = updated_text
            self._refresh_question_listbox()
            self.settings_question_entry.delete(0, tk.END)
        except ValueError:
            messagebox.showerror("Error", "Could not find the original question to update. Please try again.")

    def _delete_question(self):
        selected_indices = self.settings_question_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("No Selection", "Please select a question to delete.")
            return
        question_to_delete = self.settings_question_listbox.get(selected_indices[0])
        if question_to_delete in self.predefined_questions:
            self.predefined_questions.remove(question_to_delete)
        self._refresh_question_listbox()
        self.settings_question_entry.delete(0, tk.END)

    def save_settings(self, settings_window):
        self.personal_context = self.settings_personal_text.get('1.0', 'end-1c').strip()
        self.company_context = self.settings_company_text.get('1.0', 'end-1c').strip()
        self.selected_model_name = self.settings_model_dropdown.get()
        
        # Ensure the placeholder is the first item if it's not there
        if not self.predefined_questions or self.predefined_questions[0] != DEFAULT_PREDEFINED_QUESTIONS[0]:
            # Remove any other instances of the placeholder before adding it to the start
            self.predefined_questions = [q for q in self.predefined_questions if q != DEFAULT_PREDEFINED_QUESTIONS[0]]
            self.predefined_questions.insert(0, DEFAULT_PREDEFINED_QUESTIONS[0])

        self.question_dropdown['values'] = self.predefined_questions
        self.question_dropdown.current(0)
        
        settings_window.destroy()
        self.update_status(f"Settings have been applied.", "💾")

    def _initialize_apis(self):
        openrouter_ok = bool(OPENROUTER_API_KEY)
        google_ok = False
        if GOOGLE_API_KEY:
            try:
                genai.configure(api_key=GOOGLE_API_KEY)
                self.gemini_model = genai.GenerativeModel(model_name='gemini-1.5-flash-latest')
                google_ok = True
            except Exception as e: print(f"Failed to initialize Google AI: {e}")
        status = []
        if openrouter_ok: status.append("OpenRouter Ready")
        if google_ok: status.append("Google AI Ready")
        if not status: self.update_status("Error: No API keys found!", "❌", is_error=True)
        else: self.update_status(" & ".join(status), "✅")

    def _generate_prompt(self, question, user_answer=None):
        """Dynamically builds the prompt based on the current mode."""
        if self.evaluation_mode.get() and user_answer:
            prompt = f"{SYSTEM_PROMPT_EVALUATION}\n\n--- OLIVER'S CONTEXT ---\n{self.personal_context}\n\n"
            if self.company_context.strip():
                prompt += f"--- COMPANY CONTEXT ---\n{self.company_context}\n\n"
            prompt += f"--- INTERVIEW QUESTION ---\n{question}\n\n--- USER'S ANSWER AS OLIVER ---\n{user_answer}\n\nNow, provide your evaluation:"
            return prompt
        else:
            prompt = f"{SYSTEM_PROMPT_BASE}\n\n--- OLIVER'S CONTEXT ---\n{self.personal_context}\n\n"
            if self.company_context.strip():
                prompt += f"--- COMPANY CONTEXT ---\n{self.company_context}\n\n"
            prompt += f"Now, answer the following question:\nQUESTION: {question}"
            return prompt
    
    def _set_ui_state(self, enabled):
        state = 'normal' if enabled else 'disabled'
        self.text_input.config(state=state)
        self.send_button.config(state=state)
        self.listen_button.config(state=state)
        self.question_dropdown.config(state='readonly' if enabled else 'disabled')
        
        if enabled:
            self.progress_bar.stop()
            self.progress_bar.grid_remove()
            self.update_status(f"Ready ({self.selected_model_name})", "🟢")
        else:
            self.progress_bar.grid()
            self.progress_bar.start()
            self.update_status(f"Generating with {self.selected_model_name}...", "🤖")

    def submit_question_to_ai(self, text):
        if not text: return

        if self.evaluation_mode.get():
            if not self.last_question_asked:
                messagebox.showwarning("No Question", "Please ask a question first before providing an answer for evaluation.")
                return
            self.add_message("You (My Answer):", text, 'you')
            self._set_ui_state(enabled=False)
            threading.Thread(target=self.get_ai_answer, args=(self.last_question_asked, text), daemon=True).start()
        else:
            self.last_question_asked = text
            self.add_message("You:", text, 'you')
            self._set_ui_state(enabled=False)
            threading.Thread(target=self.get_ai_answer, args=(text, None), daemon=True).start()

    def send_text_question(self, event=None):
        text = self.text_input.get().strip()
        if text and not self.input_has_placeholder:
            self.submit_question_to_ai(text)
            self.text_input.delete(0, tk.END); self._on_input_focus_out(None)

    def on_dropdown_select(self, event=None):
        question = self.question_var.get()
        if question != DEFAULT_PREDEFINED_QUESTIONS[0] and self.dropdown_clicked:
            if self.evaluation_mode.get():
                 messagebox.showinfo("Evaluation Mode Active", f"The question has been set to:\n\n'{question}'\n\nNow, please type your answer in the input box and press Send.")
                 self.last_question_asked = question
            else:
                self.submit_question_to_ai(question)
            self.question_dropdown.current(0)
            self.root.focus_set()
        self.dropdown_clicked = False

    def toggle_listening(self):
        if self.is_listening.is_set(): self.is_listening.clear()
        else: self.is_listening.set(); threading.Thread(target=self._listen_and_process, daemon=True).start()

    def _listen_and_process(self):
        self.queue.put(("button_update", ("🔴 Stop", "danger")))
        self.queue.put(("voice_status", ("🔵 Calibrating...", "info")))
        with sr.Microphone() as source:
            try:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                self.queue.put(("voice_status", ("🟢 Listening...", "success")))
                audio = self.recognizer.listen(source, timeout=10, phrase_time_limit=30)
                self.queue.put(("voice_status", ("🟠 Processing...", "warning")))
                text = self.recognizer.recognize_google(audio, language='en-US')
                if text.strip():
                    self.queue.put(("voice_status", (f"✔️ Recognized", "success")))
                    self.queue.put(("submit_question", text))
                else: self.queue.put(("voice_status", ("⚠️ No speech", "warning")))
            except sr.WaitTimeoutError: self.queue.put(("voice_status", ("⏱️ Timed out", "warning")))
            except sr.UnknownValueError: self.queue.put(("voice_status", ("❌ Could not understand", "danger")))
            except sr.RequestError as e: self.queue.put(("voice_status", ("📡 Network error", "danger"))); print(f"Speech service error: {e}")
            finally:
                self.is_listening.clear()
                self.queue.put(("button_update", ("🎤 Voice", "info")))
                self.root.after(2000, lambda: self.queue.put(("voice_status", ("⚫ Ready", "secondary"))))

    def get_ai_answer(self, question, user_answer=None):
        model_config = MODELS.get(self.selected_model_name)
        if not model_config:
            self.queue.put(("add_message", ("Error:", f"Model '{self.selected_model_name}' not configured.", "error")))
            self.queue.put(("set_ui_state", True)); return
            
        api_key = globals().get(model_config.get("key_name"))
        if not api_key:
            error_msg = f"\n❌ API Key Error: {model_config.get('key_name')} not found in .env file."
            self.queue.put(("add_message", ("Error:", error_msg, "error")))
            self.queue.put(("set_ui_state", True)); return

        full_prompt = self._generate_prompt(question, user_answer)
        
        tag = 'eval' if self.evaluation_mode.get() else 'ai'
        speaker = "AI (Evaluation):" if self.evaluation_mode.get() else "AI:"
        self.queue.put(("add_message", (speaker, "", tag)))

        self.last_ai_response = "" # Reset before streaming
        try:
            if model_config['api'] == "openrouter": self._get_openrouter_answer(full_prompt)
            elif model_config['api'] == "google": self._get_google_gemini_answer(full_prompt)
        except Exception as e:
            self.queue.put(("stream_update", f"\n❌ Unexpected Error during API call: {str(e)}"))
        finally:
            self.queue.put(("set_ui_state", True))

    def _get_openrouter_answer(self, full_prompt):
        payload = {"model": MODELS[self.selected_model_name]['id'], "messages": [{"role": "user", "content": full_prompt}], "stream": True}
        headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
        try:
            response = requests.post(OPENROUTER_ENDPOINT, json=payload, headers=headers, stream=True, timeout=30)
            response.raise_for_status()
            for line in response.iter_lines():
                if line and line.decode('utf-8').startswith('data: '):
                    data = line.decode('utf-8')[6:]
                    if data == '[DONE]': break
                    try:
                        chunk = json.loads(data)
                        if 'choices' in chunk and chunk['choices'][0]['delta'].get('content'):
                            text_chunk = chunk['choices'][0]['delta']['content']
                            self.last_ai_response += text_chunk
                            self.queue.put(("stream_update", text_chunk))
                    except json.JSONDecodeError: continue
        except requests.exceptions.RequestException as e:
            self.queue.put(("stream_update", f"\n❌ API Connection Error: {str(e)}"))

    def _get_google_gemini_answer(self, full_prompt):
        if not self.gemini_model:
            self.queue.put(("stream_update", "\n❌ Google AI model not initialized.")); return
        try:
            response_stream = self.gemini_model.generate_content(full_prompt, stream=True)
            for chunk in response_stream:
                if chunk.text:
                    self.last_ai_response += chunk.text
                    self.queue.put(("stream_update", chunk.text))
        except Exception as e:
            self.queue.put(("stream_update", f"\n❌ Google AI Error: {str(e)}"))

    def process_queue(self):
        try:
            while True:
                msg_type, data = self.queue.get_nowait()
                if msg_type == "submit_question": self.submit_question_to_ai(data)
                elif msg_type == "add_message": self.add_message(data[0], data[1], data[2], is_welcome=data[3] if len(data) > 3 else False)
                elif msg_type == "stream_update": self.append_to_last_message(data)
                elif msg_type == "set_ui_state": self._set_ui_state(data)
                elif msg_type == "button_update": self.listen_button.config(text=data[0], bootstyle=data[1])
                elif msg_type == "voice_status": self.voice_status_label.config(text=data[0], bootstyle=data[1])
        except queue.Empty: pass
        finally: self.root.after(100, self.process_queue)

    def update_status(self, text, icon="ℹ️", is_error=False):
        style = "danger" if is_error else "secondary"
        self.status_label.config(text=f"{icon} {text}", bootstyle=style)

    def add_message(self, speaker, text, tag, is_welcome=False):
        entry = {'speaker': speaker, 'text': text, 'tag': tag, 'timestamp': datetime.datetime.now().isoformat()}
        
        self.conversation_area.config(state='normal')
        if self.conversation_area.get('1.0', tk.END).strip() and not is_welcome:
            self.conversation_area.insert(tk.END, "\n\n")
        
        timestamp = datetime.datetime.fromisoformat(entry['timestamp']).strftime("%H:%M")
        icon = "👤" if speaker.startswith("You") else "🤖"
        self.conversation_area.insert(tk.END, f"{icon} {speaker} ({timestamp})\n", tag)
        self.conversation_area.insert(tk.END, text, 'text')
        self.conversation_area.config(state='disabled'); self.conversation_area.see(tk.END)
        
        if not is_welcome:
            self.conversation_history.append(entry)

    def append_to_last_message(self, text_chunk):
        self.conversation_area.config(state='normal')
        self.conversation_area.insert(tk.END, text_chunk, 'text')
        self.conversation_area.config(state='disabled'); self.conversation_area.see(tk.END)
        if self.conversation_history:
            self.conversation_history[-1]['text'] += text_chunk
    
    def copy_last_response(self):
        if not self.last_ai_response:
            messagebox.showinfo("No Response", "No AI response available to copy.")
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(self.last_ai_response)
        self.update_status("AI response copied to clipboard!", "📋")

    def save_conversation(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
            title="Save Conversation"
        )
        if not filepath: return
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.conversation_history, f, indent=4)
            self.update_status(f"Conversation saved to {os.path.basename(filepath)}", "💾")
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save conversation: {e}")

    def load_conversation(self):
        filepath = filedialog.askopenfilename(
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
            title="Load Conversation"
        )
        if not filepath: return
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                history = json.load(f)
            
            self.clear_conversation()
            for entry in history:
                self.root.after(10, lambda e=entry: self.add_message(e['speaker'], e['text'], e['tag']))
            self.update_status(f"Loaded conversation from {os.path.basename(filepath)}", "📂")
        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load conversation: {e}")

def main():
    """Main function to run the application with a splash screen."""
    root = ttk.Window(themename="sandstone")
    root.withdraw()

    splash = tk.Toplevel(root)
    splash.overrideredirect(True)
    w, h = 400, 200
    ws, hs = root.winfo_screenwidth(), root.winfo_screenheight()
    x, y = (ws/2) - (w/2), (hs/2) - (h/2)
    splash.geometry(f'{w}x{h}+{int(x)}+{int(y)}')
    
    splash_frame = ttk.Frame(splash, bootstyle="primary")
    splash_frame.pack(expand=True, fill='both')
    ttk.Label(splash_frame, text="🎯 AI Interview Assistant", font=(FONT_FAMILY, 16, "bold"), bootstyle="inverse-primary").pack(pady=(40, 10))
    ttk.Label(splash_frame, text="Loading models and preparing workspace...", bootstyle="inverse-primary").pack()

    def setup_main_app():
        app = InterviewAssistantApp(root)
        splash.destroy()
        root.deiconify()

    root.after(2500, setup_main_app)
    root.mainloop()

if __name__ == "__main__":
    if not sr.Microphone.list_microphone_names():
        root = tk.Tk(); root.withdraw()
        messagebox.showerror("Microphone Error", "No microphone found. Please connect a microphone and restart.")
        sys.exit(1)
    
    main()