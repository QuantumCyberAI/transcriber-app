import os
import time
import threading
import tkinter as tk
from tkinter import messagebox, ttk, filedialog
from datetime import datetime
import whisper
from pydub.utils import mediainfo
import pydub
import ttkbootstrap as ttkb
import requests
from PIL import Image, ImageTk
from io import BytesIO
import json

# Set FFmpeg path (adjust this to your system or make it configurable)
import platform
import sys

if platform.system() == "Windows":
    pydub.AudioSegment.ffmpeg = r"C:\Users\alexa\Downloads\FFMPEG\ffmpeg.exe"
    pydub.AudioSegment.ffprobe = r"C:\Users\alexa\Downloads\FFMPEG\ffprobe.exe"
else:
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    pydub.AudioSegment.ffmpeg = os.path.join(base_path, "ffmpeg")
    pydub.AudioSegment.ffprobe = os.path.join(base_path, "ffprobe")

# Global variables
settings_file = "settings.json"
default_settings = {
    "dark_mode": True,
    "source_dir": os.getcwd(),
    "output_dir": "transcripts",
    "model_size": "base",
    "preset": {
        "category": "Professional & Work",
        "type": "Team Meeting",
        "tasks": ["Summarize", "Extract Action Items"]
    }
}
whisper_model = None  # Global Whisper model variable
model_loaded = False  # Flag to track if model is ready

# Language mapping
language_map = {
    "Autodetect": None,
    "English": "en",
    "Spanish": "es",
    "French": "fr",
    "German": "de",
    "Chinese": "zh",
    "Japanese": "ja",
    "Russian": "ru",
    "Italian": "it",
    "Portuguese": "pt",
    "Arabic": "ar"
}

# New AI prompts structure
ai_prompts = {
    "Professional & Work": {
        "Team Meeting": "You are a highly organized executive assistant. This is a transcript of a team meeting. Provide a structured summary by topic, list key decisions, unresolved issues, and assign follow-ups.",
        "Client Call / Meeting": "You are a client success manager. This transcript covers a conversation with a client. Summarize goals, pain points, commitments, and next steps with clarity and professionalism.",
        "Strategy Session": "You are a strategic advisor. This is a planning session. Identify high-level goals, strategic conflicts, decisions made, and long-term actions.",
        "Workshop or Training": "You are a corporate trainer. Extract the structure of the workshop, summarize key teachings, exercises, and any assigned tasks.",
        "Sales Call / Pitch": "You are a sales strategist. Extract the customer’s needs, objections, responses, value propositions, and closing steps.",
        "Support Call": "You are a customer service analyst. Identify the user issue, troubleshooting steps, resolution, and emotional tone of the exchange.",
        "Internal Presentation": "You are a communication expert. Summarize the speaker’s message, supporting points, and recommendations with precision.",
        "Coaching / Mentorship Session": "You are a leadership coach. Capture developmental goals, advice given, progress markers, and next action items.",
        "Focus Group": "You are a market researcher. Summarize participant feedback, group consensus or conflicts, and recommendations."
    },
    "Education & Learning": {
        "Lecture": "You are an academic summarizer. This lecture transcript should be broken into sections. Extract definitions, core concepts, and examples.",
        "Interview (Academic or Professional)": "You are a journalist. Extract major themes, compelling insights, and illustrative quotes from the interview.",
        "Panel Discussion": "You are a debate analyst. Break down key topics, note which panelist said what, and highlight any conflicts or agreements.",
        "Seminar / Q&A Session": "You are an academic assistant. Structure the transcript by questions/topics and summarize expert responses.",
        "Study Group": "You are a study group moderator. Extract group insights, confusion points, clarifications, and any shared resources."
    },
    "Media & Content Creation": {
        "Podcast Episode": "You are a podcast editor. Break the conversation into logical segments, summarize main themes, and extract highlights or soundbites.",
        "YouTube Video": "You are a content strategist. Outline the video structure, capture the main message, and extract key teaching moments.",
        "Livestream": "You are a community analyst. Organize the discussion by topic shifts, identify viewer engagement moments, and summarize key takeaways.",
        "Voiceover Script": "You are a scriptwriter. Review the transcript for structure, clarity, and effectiveness. Suggest improvements or structure.",
        "Public Talk / Speech": "You are a communications coach. Identify the speaker’s main message, tone, rhetorical structure, and audience calls to action."
    },
    "Self-Reflection & Thought Capture": {
        "Voice Note / Brain Dump": "You are a thought organization assistant. This is a spontaneous voice note. Extract clear ideas, themes, and tasks mentioned.",
        "Personal Journal Entry (Voice)": "You are a journaling assistant. Capture the speaker’s mood, emotions, recurring thoughts, and reflective questions.",
        "Planning / To-Do Voice Memo": "You are a productivity assistant. Extract specific tasks, deadlines, dependencies, and structure them into a checklist.",
        "Coaching Yourself / Self Talk": "You are a self-improvement coach. Reflect on goals, self-critique, affirmations, and next steps.",
        "Dream Log (Voice)": "You are a dream interpreter. Reconstruct the dream sequence, identify surreal or symbolic elements, and summarize emotional tones."
    },
    "Calls & Conversations": {
        "Personal Phone Call": "You are a relationship-aware assistant. Identify the nature of the relationship, key themes, decisions made, and emotional undertones.",
        "Check-in with Friend / Partner": "You are a sentiment tracker. Summarize the emotional exchanges, important life updates, shared plans, and recurring concerns.",
        "Therapy Session": "You are a reflective analysis tool. Extract themes, mental patterns, emotional shifts, and therapeutic insights.",
        "Catch-up Call": "You are a conversation summarizer. Highlight important updates, emotional tone, and any plans or intentions expressed.",
        "Difficult Conversation": "You are a conflict resolution advisor. Summarize each person’s concerns, emotional language, responses, and unresolved tension."
    },
    "Legal, Official, & Institutional": {
        "Legal Hearing / Deposition": "You are a legal transcript summarizer. Identify all parties, legal claims, questions raised, rulings, and next steps.",
        "Town Hall or Government Meeting": "You are a policy analyst. Capture the agenda, key policy points, community feedback, and speaker positions.",
        "Board Meeting / Minutes": "You are a board secretary. Summarize decisions made, voting outcomes, dissenting views, and follow-up actions.",
        "Compliance / Regulatory Review": "You are a compliance officer. Summarize discussed rules, breaches (if any), corrective actions, and approvals."
    },
    "General or Unstructured": {
        "General Discussion": "You are a flexible summarization tool. Extract primary topics, categorize themes, and list action items.",
        "Multi-topic Recording": "You are a conversation disentangler. Divide the transcript by topic, summarize each separately, and identify any logical flow.",
        "Unstructured Conversation": "You are a pattern detector. Analyze the freeform discussion for recurring ideas, emotions, and implicit concerns."
    }
}

# Secondary (multi-select) task options
secondary_tasks = {
    "Summarize": "Summarize the content concisely.",
    "Extract Action Items": "List all actionable tasks with responsible parties if known.",
    "Identify Key Themes": "Identify major themes and recurring patterns.",
    "List Questions Raised": "List any open questions or points needing follow-up.",
    "Highlight Quotes": "Highlight notable or insightful quotes.",
    "Convert to Bullet Points": "Convert the full content into organized bullet points.",
    "Create Outline": "Create a hierarchical outline of the conversation or topic.",
    "Translate to Formal Language": "Convert the text into formal professional language.",
    "Translate to Casual Summary": "Provide a light, informal summary suitable for team updates."
}

# Function to build the prompt
def build_prompt(category, type_, selected_tasks):
    base_prompt = ai_prompts.get(category, {}).get(type_, "This is a transcript. Analyze and summarize appropriately.")
    task_texts = [secondary_tasks[t] for t in selected_tasks if t in secondary_tasks]
    full_prompt = base_prompt + "\n\n" + "\n".join(task_texts) if task_texts else base_prompt
    return full_prompt

# Load/save settings
def load_settings():
    try:
        with open(settings_file, "r") as f:
            loaded_settings = json.load(f)
            for key, value in default_settings.items():
                if key not in loaded_settings:
                    loaded_settings[key] = value
            return loaded_settings
    except (FileNotFoundError, json.JSONDecodeError):
        return default_settings.copy()

def save_settings():
    with open(settings_file, "w") as f:
        json.dump(settings_dict, f, indent=4)

settings_dict = load_settings()

# Utility functions
def get_audio_duration(filepath):
    try:
        return float(mediainfo(filepath)["duration"])
    except Exception:
        return 60  # Default fallback duration

def load_model(model_size):
    try:
        return whisper.load_model(model_size)
    except Exception as e:
        raise Exception(f"Failed to load Whisper model: {str(e)}")

# Tooltip function with improved styling
def create_tooltip(widget, text):
    tooltip = None
    def show_tooltip(event):
        nonlocal tooltip
        x, y = widget.winfo_pointerxy()
        tooltip = tk.Toplevel(widget)
        tooltip.wm_overrideredirect(True)
        tooltip.wm_geometry(f"+{x+10}+{y+10}")
        label = ttk.Label(tooltip, text=text, background="#ffffe0", foreground="black", 
                          font=("Arial", 10), relief="solid", borderwidth=1, padding=3)
        label.pack()
    def hide_tooltip(event):
        nonlocal tooltip
        if tooltip:
            tooltip.destroy()
            tooltip = None
    widget.bind("<Enter>", show_tooltip)
    widget.bind("<Leave>", hide_tooltip)

# GUI functions
def update_progress(root, progress_var, percent_label, progress, total, time_remaining=None):
    progress_var.set(progress)
    percent_text = f"{progress:.1f}%"
    if time_remaining is not None and time_remaining > 0:
        percent_text += f" | ~{int(time_remaining)}s left"
    percent_label.config(text=percent_text)
    root.update()

def settings_window(root):
    settings_win = tk.Toplevel(root)
    settings_win.title("Settings")
    settings_win.geometry("400x420")
    settings_win.resizable(False, False)
    settings_win.transient(root)
    settings_win.grab_set()

    ttk.Label(settings_win, text="Settings", font=("Arial", 12, "bold")).pack(pady=10)

    dark_var = tk.BooleanVar(value=settings_dict["dark_mode"])
    ttk.Checkbutton(settings_win, text="Dark Mode", variable=dark_var, 
                    command=lambda: update_theme(root, dark_var.get())).pack(pady=5)

    ttk.Label(settings_win, text="Model Size:").pack(pady=5)
    model_var = tk.StringVar(value=settings_dict["model_size"])
    ttk.Combobox(settings_win, textvariable=model_var, 
                 values=["tiny", "base", "small", "medium", "large"], state="readonly").pack(pady=5)

    ttk.Label(settings_win, text="Source Directory:").pack(pady=5)
    source_entry = ttk.Entry(settings_win, width=40)
    source_entry.insert(0, settings_dict["source_dir"])
    source_entry.pack()
    ttk.Button(settings_win, text="Browse", 
               command=lambda: source_entry.delete(0, tk.END) or source_entry.insert(0, filedialog.askdirectory())).pack(pady=5)

    ttk.Label(settings_win, text="Output Directory:").pack(pady=5)
    output_entry = ttk.Entry(settings_win, width=40)
    output_entry.insert(0, settings_dict["output_dir"])
    output_entry.pack()
    ttk.Button(settings_win, text="Browse", 
               command=lambda: output_entry.delete(0, tk.END) or output_entry.insert(0, filedialog.askdirectory())).pack(pady=5)

    def save():
        global whisper_model, model_loaded
        new_model_size = model_var.get()
        new_dark_mode = dark_var.get()

        if new_model_size != settings_dict["model_size"]:
            try:
                whisper_model = load_model(new_model_size)
                model_loaded = True
            except Exception as e:
                messagebox.showerror("Error", f"Failed to reload Whisper model:\n{e}")
                return

        if new_dark_mode != settings_dict["dark_mode"]:
            update_theme(root, new_dark_mode)

        settings_dict.update({
            "dark_mode": new_dark_mode,
            "source_dir": source_entry.get(),
            "output_dir": output_entry.get(),
            "model_size": new_model_size
        })
        save_settings()
        settings_win.destroy()

    ttk.Button(settings_win, text="Save", command=save).pack(pady=10)

def update_theme(root, dark_mode):
    root.style.theme_use("darkly" if dark_mode else "cosmo")
    settings_dict["dark_mode"] = dark_mode
    save_settings()

def transcribe_audio(root, filepath, status_label, progress_var, progress_bar, progress_label, preview_text, language_var, output_dir, category_var, type_var, secondary_listbox):
    status_label.config(text=f"Transcribing: {os.path.basename(filepath)}")
    start_button.config(state="disabled")
    progress_bar.pack(pady=5)
    progress_label.pack()

    try:
        language = language_map[language_var.get()]
        global whisper_model
        model = whisper_model
        duration = get_audio_duration(filepath)

        result = None
        transcription_done = False

        def do_transcription():
            nonlocal result, transcription_done
            result = model.transcribe(filepath, language=language)
            transcription_done = True

        thread = threading.Thread(target=do_transcription)
        thread.start()

        start_time = time.time()
        while not transcription_done:
            elapsed = time.time() - start_time
            percent = min(elapsed / duration * 100, 99.9)
            update_progress(root, progress_var, progress_label, percent, 100, duration - elapsed)
            time.sleep(0.1)

        update_progress(root, progress_var, progress_label, 100, 100)
        transcript_text = result["text"].strip()
        if not transcript_text:
            raise Exception("Transcription failed: No text returned.")

        today = datetime.now().strftime("%Y-%m-%d")
        daily_dir = os.path.join(output_dir, today)
        os.makedirs(daily_dir, exist_ok=True)
        filename = os.path.splitext(os.path.basename(filepath))[0]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = os.path.join(daily_dir, f"{filename}_{timestamp}.txt")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(transcript_text)

        status_label.config(text="Transcription Complete!")
        preview_text.delete(1.0, tk.END)
        preview_text.insert(tk.END, transcript_text)
        progress_bar.pack_forget()
        progress_label.pack_forget()

        # Generate AI Assistant-ready prompt with new structure
        category = category_var.get()
        type_ = type_var.get()
        selected_tasks = [secondary_listbox.get(i) for i in secondary_listbox.curselection()]
        full_prompt = build_prompt(category, type_, selected_tasks) + f"\n\n{transcript_text}"

        if messagebox.askyesno("Success", f"Transcript saved to:\n{out_path}\n\nCopy AI Assistant prompt + transcript to clipboard?"):
            root.clipboard_clear()
            root.clipboard_append(full_prompt)
            messagebox.showinfo("Copied", "Prompt and transcript copied to clipboard.\nPaste it into AI Assistant for instant analysis.")

    except Exception as e:
        status_label.config(text="Transcription Failed")
        messagebox.showerror("Error", str(e))
        progress_bar.pack_forget()
        progress_label.pack_forget()

    start_button.config(state="normal")

def main():
    global whisper_model, model_loaded, start_button

    root = ttkb.Window(themename="darkly" if settings_dict["dark_mode"] else "cosmo")
    root.title("Quantum Cyber AI Transcriber")
    root.geometry("600x800")
    root.resizable(False, False)

    # Center content in a frame
    main_frame = ttk.Frame(root)
    main_frame.pack(expand=True)

    try:
        response = requests.get("https://quantum-cyber-ai.com/wp-content/uploads/2025/01/cropped-cropped-QCA-Logo-2.jog_.webp")
        logo_img = Image.open(BytesIO(response.content)).resize((100, 100), Image.Resampling.LANCZOS)
        logo = ImageTk.PhotoImage(logo_img)
        ttk.Label(main_frame, image=logo).pack(pady=10)
    except Exception:
        ttk.Label(main_frame, text="Quantum Cyber AI Transcriber", font=("Arial", 14, "bold")).pack(pady=10)

    status_label = ttk.Label(main_frame, text="Loading Whisper model...", font=("Arial", 11))
    status_label.pack(pady=10)

    # Language dropdown
    ttk.Label(main_frame, text="Language:").pack()
    language_var = tk.StringVar(value="Autodetect")
    ttk.Combobox(main_frame, textvariable=language_var, 
                 values=list(language_map.keys()), 
                 state="readonly", width=30).pack(pady=5)  # Widened to 30

    # Category dropdown
    ttk.Label(main_frame, text="Category:").pack()
    category_var = tk.StringVar(value=settings_dict["preset"]["category"])
    category_combo = ttk.Combobox(main_frame, textvariable=category_var, 
                                  values=list(ai_prompts.keys()), 
                                  state="readonly", width=30).pack(pady=5)  # Widened to 30

    # Type dropdown (dynamically updates based on category)
    ttk.Label(main_frame, text="Recording Type:").pack()
    type_var = tk.StringVar(value=settings_dict["preset"]["type"])
    type_combo = ttk.Combobox(main_frame, textvariable=type_var, state="readonly", width=30)  # Widened to 30
    type_combo.pack(pady=5)

    def update_types(*args):
        selected_category = category_var.get()
        type_combo["values"] = list(ai_prompts.get(selected_category, {}).keys())
        type_var.set(type_combo["values"][0] if type_combo["values"] else "")
    category_var.trace("w", update_types)
    update_types()  # Initial population

    # Secondary tasks multi-select with help icon and scrollbar
    secondary_frame = ttk.Frame(main_frame)
    secondary_frame.pack(pady=5)
    ttk.Label(secondary_frame, text="Secondary Tasks (Ctrl+Click to select multiple):").pack(side=tk.LEFT)
    help_icon = ttk.Label(secondary_frame, text="💡", font=("Arial", 12), foreground="yellow")
    help_icon.pack(side=tk.LEFT, padx=5)
    create_tooltip(help_icon, "These additional tasks help the assistant tailor the output. Ctrl+Click to select multiple.")
    
    secondary_listbox_frame = ttk.Frame(main_frame)
    secondary_listbox_frame.pack(pady=5)
    secondary_listbox = tk.Listbox(secondary_listbox_frame, selectmode="multiple", height=4, width=35)  # Widened to 35
    scrollbar_listbox = ttk.Scrollbar(secondary_listbox_frame, orient="vertical", command=secondary_listbox.yview)
    secondary_listbox.configure(yscrollcommand=scrollbar_listbox.set)
    scrollbar_listbox.pack(side=tk.RIGHT, fill="y")
    secondary_listbox.pack(side=tk.LEFT, fill="y")
    for task in secondary_tasks.keys():
        secondary_listbox.insert(tk.END, task)

    # Load preset on startup
    def apply_preset():
        preset = settings_dict["preset"]
        category_var.set(preset["category"])
        update_types()  # Ensure type dropdown updates
        type_var.set(preset["type"])
        secondary_listbox.selection_clear(0, tk.END)
        for task in preset["tasks"]:
            if task in secondary_tasks:
                idx = list(secondary_tasks.keys()).index(task)
                secondary_listbox.selection_set(idx)

    apply_preset()  # Apply preset on startup

    # Preset buttons
    preset_frame = ttk.Frame(main_frame)
    preset_frame.pack(pady=5)

    def save_preset():
        settings_dict["preset"] = {
            "category": category_var.get(),
            "type": type_var.get(),
            "tasks": [secondary_listbox.get(i) for i in secondary_listbox.curselection()]
        }
        save_settings()
        messagebox.showinfo("Preset Saved", "Your current selections have been saved as a preset.")

    def load_preset():
        apply_preset()
        messagebox.showinfo("Preset Loaded", "Preset loaded from saved settings.")

    ttk.Button(preset_frame, text="Save Preset", command=save_preset).pack(side=tk.LEFT, padx=5)
    ttk.Button(preset_frame, text="Load Preset", command=load_preset).pack(side=tk.LEFT, padx=5)

    progress_var = tk.DoubleVar()
    progress_bar = ttk.Progressbar(main_frame, variable=progress_var, length=300)
    progress_label = ttk.Label(main_frame, font=("Arial", 9))
    progress_bar.pack_forget()
    progress_label.pack_forget()

    preview_frame = ttk.Frame(main_frame)
    preview_text = tk.Text(preview_frame, height=10, width=70, wrap=tk.WORD)
    scrollbar_text = ttk.Scrollbar(preview_frame, command=preview_text.yview)
    preview_text.configure(yscrollcommand=scrollbar_text.set)
    scrollbar_text.pack(side=tk.RIGHT, fill=tk.Y)
    preview_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    preview_frame.pack(pady=10, fill=tk.BOTH, expand=True)

    def start_transcription():
        if not model_loaded:
            messagebox.showinfo("Please Wait", "Model is still loading. Try again in a moment.")
            return
        filepath = filedialog.askopenfilename(initialdir=settings_dict["source_dir"], 
                                              filetypes=[("Audio Files", "*.mp3 *.wav *.m4a *.ogg")])
        if filepath:
            transcribe_audio(root, filepath, status_label, progress_var, progress_bar, progress_label, 
                            preview_text, language_var, settings_dict["output_dir"], category_var, type_var, secondary_listbox)

    start_button = ttk.Button(main_frame, text="Select Audio File", command=start_transcription, state="disabled")
    start_button.pack(pady=10)
    ttk.Button(main_frame, text="Settings", command=lambda: settings_window(root)).pack(pady=5)

    def load_model_in_background():
        global whisper_model, model_loaded
        try:
            whisper_model = load_model(settings_dict["model_size"])
            model_loaded = True
            status_label.config(text="Model loaded. Select an audio file to transcribe.")
            start_button.config(state="normal")
        except Exception as e:
            status_label.config(text="Failed to load Whisper model.")
            messagebox.showerror("Error", f"Could not load Whisper model:\n{e}")
            root.destroy()

    threading.Thread(target=load_model_in_background, daemon=True).start()

    root.mainloop()

if __name__ == "__main__":
    main()