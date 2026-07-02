# Local Voice Cloning Audiobook Creator

A lightweight, 100% offline Python application that converts PDF documents into high-quality, voice-cloned audiobooks. This tool uses local AI models to bypass API rate limits, network dependencies, and privacy concerns, ensuring your documents and voice samples never leave your machine.

## ✨ Features
* **100% Offline Generation:** Powered by local Hugging Face model weights, requiring zero internet connection after the initial setup.
* **Custom Voice Cloning:** Provide a short `.wav` sample of any voice, and the AI will narrate your PDF in that exact voice.
* **Smart Text Chunking:** Automatically breaks down complex technical PDF pages into AI-friendly sentence chunks to prevent token-limit crashes.
* **Clean Audio Processing:** Automatically applies high-pass filters to your base voice samples for clearer generation.
* **Seamless Audio Stitching:** Glues the generated sentence chunks together into smooth, uninterrupted chapter files (`.ogg`).

## 🛠️ Prerequisites
* Python 3.10+
* [uv](https://github.com/astral-sh/uv) (for ultra-fast dependency and model management)

## 🚀 Installation & Setup

**1. Clone the repository**
```bash
git clone [https://github.com/YOUR_USERNAME/Audiobook-Creator.git](https://github.com/YOUR_USERNAME/Audiobook-Creator.git)
cd Audiobook-Creator
```

**2. Install Python Dependencies**
```bash
pip install PyPDF2 scipy soundfile numpy transformers torch
# Note: pocket_tts must be installed per their specific documentation
```

**3. Download the Offline Model**
To run completely offline, you must download the weights locally. We use `uvx` to bypass environment pathing issues.

First, authenticate with Hugging Face (requires a free account and accepting the model terms):
```bash
uvx hf auth login
```

Then, download the model into the project directory:
```bash
uvx hf download kyutai/pocket-tts --local-dir local_model
```

## 🎮 Usage
Once the `local_model` folder is populated, simply run the app:

```bash
python audiobook_app.py
```

1. **Select PDF:** Choose the document you want to read.
2. **Select Voice:** Choose a clear, short (10-15 seconds) `.wav` file of the target voice.
3. **Save As Base:** Choose where to output the final audio files.
4. **Pages per Chapter:** Define how many PDF pages should be combined into a single audio chapter.
5. Click **Generate Audiobook**.

*Note: The UI will update you on the generation progress. As this runs locally, generation speed is dependent on your CPU/GPU hardware.*

## ⚠️ Notes
* **File Exclusions:** The `.gitignore` is configured to exclude the `local_model` folder and generated audio files. If you clone this repo to a new machine, you must repeat the model download step.