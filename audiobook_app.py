import os
# Force Hugging Face libraries to operate completely offline
os.environ["HF_HUB_OFFLINE"] = "1"

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import re
import PyPDF2
import scipy.io.wavfile
import soundfile as sf
from pocket_tts import TTSModel
import numpy as np
from scipy.signal import butter, lfilter
import tempfile

class LocalVoiceCloneApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Local Voice Cloning Audiobook")
        self.root.geometry("500x550")
        
        self.pdf_path = tk.StringVar()
        self.audio_path = tk.StringVar()
        self.voice_sample_path = tk.StringVar()
        self.pages_per_chapter = tk.StringVar(value="10")
        
        self.model = None
        self.setup_ui()
        
        # Start model loading in the background
        threading.Thread(target=self.load_model, daemon=True).start()

    def load_model(self):
        try:
            # Load strictly from the downloaded local folder
            self.model = TTSModel.load_model(model_path="./local_model")
            
            self.root.after(0, lambda: self.status_label.config(text="Status: Ready (100% Offline Mode)"))
            self.root.after(0, lambda: self.convert_btn.config(state="normal"))
        except Exception as e:
            error_text = str(e)
            self.root.after(0, lambda msg=error_text: messagebox.showerror("Load Error", f"Model Load Failed: {msg}"))

    def clean_audio(self, input_file_path):
        """Applies a high-pass filter to clean up the base voice sample."""
        sample_rate, data = scipy.io.wavfile.read(input_file_path)
        audio_float = data.astype(np.float32) / 32768.0
        
        if len(audio_float.shape) > 1: 
            audio_float = np.mean(audio_float, axis=1)
            
        b, a = butter(4, 85.0 / (0.5 * sample_rate), btype='high', analog=False)
        filtered = lfilter(b, a, audio_float)
        
        temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        scipy.io.wavfile.write(temp_file.name, sample_rate, (np.clip(filtered * 32767.0, -32768.0, 32767.0)).astype(np.int16))
        return temp_file.name

    def split_into_chunks(self, text, max_words=18):
        """Breaks text into small pieces to safely fit the AI's 50-token processing limit."""
        sentences = re.split(r'(?<=[.!?]) +', text)
        chunks = []
        for sentence in sentences:
            words = sentence.split()
            while len(words) > max_words:
                chunks.append(" ".join(words[:max_words]))
                words = words[max_words:]
            if words:
                chunks.append(" ".join(words))
        return [c.strip() for c in chunks if c.strip()]

    def setup_ui(self):
        """Initializes the Tkinter graphical interface."""
        frame = ttk.LabelFrame(self.root, text="Configuration")
        frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Button(frame, text="Select PDF", command=lambda: self.select_file(self.pdf_path, [("PDF", "*.pdf")])).grid(row=0, column=0, pady=5, padx=5)
        ttk.Label(frame, textvariable=self.pdf_path).grid(row=0, column=1, sticky="w")
        
        ttk.Button(frame, text="Select Voice", command=lambda: self.select_file(self.voice_sample_path, [("WAV", "*.wav")])).grid(row=1, column=0, pady=5, padx=5)
        ttk.Label(frame, textvariable=self.voice_sample_path).grid(row=1, column=1, sticky="w")
        
        ttk.Button(frame, text="Save As Base", command=self.select_audio_save).grid(row=2, column=0, pady=5, padx=5)
        ttk.Label(frame, textvariable=self.audio_path).grid(row=2, column=1, sticky="w")
        
        ttk.Label(frame, text="Pages per Chapter:").grid(row=3, column=0, pady=5, padx=5)
        ttk.Entry(frame, textvariable=self.pages_per_chapter, width=5).grid(row=3, column=1, sticky="w")
        
        self.convert_btn = ttk.Button(self.root, text="Generate Audiobook", command=self.start_conversion, state="disabled")
        self.convert_btn.pack(pady=20)
        
        self.status_label = ttk.Label(self.root, text="Status: Loading local model weights...")
        self.status_label.pack()

    def select_file(self, var, types):
        path = filedialog.askopenfilename(filetypes=types)
        if path: var.set(path)

    def select_audio_save(self):
        path = filedialog.asksaveasfilename(defaultextension=".ogg")
        if path: self.audio_path.set(path)

    def start_conversion(self):
        self.convert_btn.config(state="disabled")
        threading.Thread(target=self.process_audiobook, daemon=True).start()

    def process_audiobook(self):
        """Handles the core logic of reading the PDF, chunking text, generating audio, and saving to disk."""
        temp_path = None
        try:
            reader = PyPDF2.PdfReader(self.pdf_path.get())
            ppc = int(self.pages_per_chapter.get())
            
            # Prepare the cloned voice profile
            temp_path = self.clean_audio(self.voice_sample_path.get())
            voice_state = self.model.get_state_for_audio_prompt(temp_path)
            
            for i in range(0, len(reader.pages), ppc):
                # 1. Extract raw text for the pages
                raw_text = " ".join([p.extract_text().replace('\n', ' ') for p in reader.pages[i:i+ppc]])
                
                # 2. Split into small, model-friendly chunks
                text_chunks = self.split_into_chunks(raw_text)
                audio_pieces = []
                
                self.root.after(0, lambda current=i: self.status_label.config(text=f"Status: Generating Chapter {current//ppc + 1} of {(len(reader.pages)//ppc) + 1}..."))
                
                # 3. Generate audio sequentially
                for chunk in text_chunks:
                    if not chunk: continue
                    audio_tensor = self.model.generate_audio(voice_state, chunk)
                    # Flatten array to stitch cleanly
                    audio_pieces.append(audio_tensor.numpy().flatten())
                
                if not audio_pieces:
                    continue
                    
                # 4. Glue pieces together and export
                final_audio = np.concatenate(audio_pieces)
                
                base = os.path.splitext(self.audio_path.get())[0]
                wav_temp = f"{base}_temp.wav"
                ogg_final = f"{base}_ch{(i//ppc)+1}.ogg"
                
                scipy.io.wavfile.write(wav_temp, self.model.sample_rate, final_audio)
                data, sr = sf.read(wav_temp)
                sf.write(ogg_final, data, sr, format='OGG', subtype='VORBIS')
                
                os.remove(wav_temp)
                
            os.remove(temp_path)
            self.root.after(0, lambda: messagebox.showinfo("Done", "Audiobook generation complete!"))
            self.root.after(0, lambda: self.status_label.config(text="Status: Ready (100% Offline Mode)"))
            
        except Exception as e:
            error_text = str(e)
            self.root.after(0, lambda msg=error_text: messagebox.showerror("Processing Error", msg))
            self.root.after(0, lambda: self.status_label.config(text="Status: Error occurred"))
        finally:
            self.root.after(0, lambda: self.convert_btn.config(state="normal", text="Generate Audiobook"))

if __name__ == "__main__":
    root = tk.Tk()
    app = LocalVoiceCloneApp(root)
    root.mainloop()