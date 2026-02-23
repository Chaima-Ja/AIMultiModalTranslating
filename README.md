# AI Multi-Modal Translation Pipeline

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A fully local, on-premise document and audio translation system using local AI models. Translate PDFs, Word documents, PowerPoint presentations, and audio files while preserving original formatting.

## Overview

This project provides a complete translation pipeline that:
- Works entirely offline (no cloud services)
- Preserves document formatting
- Supports multiple file formats (PDF, DOCX, PPTX, Audio)
- Translates audio to audio (with TTS) or SRT subtitles
- Uses local models (Ollama + Whisper + Coqui TTS)

## Features

- **Supported Input Formats:**
  - PDF documents (`.pdf`)
  - Word documents (`.docx`) - Note: Legacy `.doc` format not supported
  - PowerPoint presentations (`.pptx`)
  - Audio/Video files (`.mp3`, `.mp4`, `.wav`, `.m4a`, `.ogg`, `.flac`)

- **Output:**
  - Documents: Translated version with original formatting preserved
  - Audio: Translated audio file (same format as input) OR SRT subtitle file

- **Fully Local:** 
  - Uses Ollama (local LLM) for translation
  - Uses Whisper (local model) for audio transcription
  - Uses Coqui TTS (optional) for audio synthesis

## Prerequisites

### System Dependencies

1. **Python 3.11+**
2. **ffmpeg** 
3. **Ollama** 

## Quick Start

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Chaima-Ja/AIMultiModalTranslating.git
   cd AIMultiModalTranslating
   ```

2. **Install dependencies:**
   ```bash
   python3.11 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Start Ollama and pull the model:**
   ```bash
   ollama serve
   ollama pull mistral:7b
   ```

4. **Start the application:**
   ```bash
   # Terminal 1: API server
   python start_api.py
   
   # Terminal 2: Web UI
   streamlit run ui.py
   ```




## Usage

### Option 1: Web UI (Recommended)


### Option 2: Command Line


### Option 3: API Only



## Project Structure

```
AIMultiModalTranslating/
├── config.py                 # Configuration management
├── models.py                 # Data models
├── pipeline.py               # Main pipeline orchestrator
├── ingestion/                # Text extraction
│   ├── pdf_extractor.py
│   ├── docx_pptx_extractor.py
│   └── audio_extractor.py
├── translation/              # Translation layer
│   └── llm_translator.py
├── reconstruction/           # Document rebuilding
│   └── builders.py
├── api/                      # FastAPI application
│   └── app.py
├── ui.py                     # Streamlit UI
├── start_api.py              # API startup script
├── requirements.txt          # Core dependencies
├── requirements-optional.txt # TTS dependencies
├── INSTALLATION.md           # Detailed installation guide
├── INSTALLATION_TTS.md       # TTS-specific installation
├── QUICK_START.md            # Quick start guide
└── README.md                 # This file
```

## How It Works

### Document Translation Flow

1. **Ingestion:** Extracts all text blocks from the document with unique IDs
2. **Translation:** Translates each block independently using Ollama (mistral:7b)
3. **Reconstruction:** Rebuilds the document by mapping translated text back to original positions

This ID-based approach preserves formatting because we never rebuild documents from scratch (except PDF, which is approximate).

### Audio Translation Flow

1. **Transcription:** Whisper transcribes audio to English text with timestamps
2. **Translation:** Ollama translates each segment to target language (French)
3. **Synthesis:** TTS generates translated audio preserving original timing
4. **Output:** Translated audio file (same format as input) or SRT subtitles (if TTS unavailable)

## Version Compatibility

**Important:** For TTS support, use these exact versions (tested and verified):

| Package | Version | Notes |
|---------|---------|-------|
| Python | 3.11 | Recommended (3.9-3.10 also work) |
| llvmlite | **0.45.0** | Download pre-built wheel from PyPI |
| numba | **0.62.1** | Compatible with llvmlite 0.45.0 |
| TTS | 0.22.0+ | Coqui TTS |
| NumPy | <2.0 | Required for torch compatibility |

See [INSTALLATION_TTS.md](INSTALLATION_TTS.md) for detailed TTS installation instructions.

## Known Limitations

- **PDF Reconstruction:** Approximate - background graphics and complex layouts are not reproduced
- **Multi-run Formatting:** Inline formatting differences within paragraphs are simplified (uses first run's style)
- **Job Store:** In-memory only - not suitable for multi-worker production deployments
- **Whisper Hallucination:** May produce repeated text on very short audio segments
- **Legacy .doc files:** Not supported - convert to .docx format first


## License

See LICENSE file for details.


## Repository

GitHub: [https://github.com/Chaima-Ja/AIMultiModalTranslating](https://github.com/Chaima-Ja/AIMultiModalTranslating)

## Support

For questions or issues, please open an issue on GitHub.

