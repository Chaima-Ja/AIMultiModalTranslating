# Multi-stage Dockerfile for AI Translation Pipeline
# Python 3.11 is required for TTS support (Python 3.9-3.11 compatible)

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    build-essential \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Copy requirements files
COPY requirements.txt requirements-optional.txt ./

# Install NumPy <2.0 first (required for torch compatibility)
RUN pip install --upgrade pip setuptools wheel && \
    pip install "numpy<2.0"

# Install llvmlite (critical dependency for numba/whisper)
# Using pre-built wheel to avoid compilation issues
RUN pip install llvmlite==0.45.0 || \
    (pip install --only-binary :all: llvmlite==0.45.0 || \
     pip install llvmlite==0.45.0 --no-build-isolation)

# Install numba (compatible with llvmlite 0.45.0)
RUN pip install numba==0.62.1 || \
    (pip install --only-binary :all: numba==0.62.1 || \
     pip install numba==0.62.1 --no-build-isolation)

# Install core dependencies
RUN pip install -r requirements.txt

# Install TTS and audio dependencies (optional requirements)
RUN pip install -r requirements-optional.txt || \
    (echo "Warning: Some TTS dependencies failed to install. Audio features may be limited." && \
     pip install soundfile>=0.12.1 scipy>=1.11.0 || true)

# Verify critical packages
RUN python -c "import llvmlite; import numba; import numpy; print(f'llvmlite: {llvmlite.__version__}, numba: {numba.__version__}, numpy: {numpy.__version__}')" && \
    python -c "import whisper; print('Whisper: OK')" || echo "Warning: Whisper import failed" && \
    python -c "try: from TTS.api import TTS; print('TTS: OK'); except: print('TTS: Not available (will use SRT fallback)')"

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p uploads outputs && \
    chmod -R 755 uploads outputs

# Expose ports
# 8000: FastAPI
# 8501: Streamlit UI
EXPOSE 8000 8501

# Default command (can be overridden in docker-compose)
CMD ["python", "start_api.py"]

