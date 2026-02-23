"""Audio transcription using Whisper."""
import whisper
from typing import List
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models import AudioBlock, ExtractedDocument
from config import Config


def extract_audio(file_path: str, config: Config = None) -> ExtractedDocument:
    """
    Extract text from audio/video file using Whisper.
    
    Returns one AudioBlock per Whisper segment with timestamps.
    """
    if config is None:
        config = Config.from_env()
    
    # Load Whisper model
    model = whisper.load_model(config.whisper_model, device=config.whisper_device)
    
    # Transcribe with forced English
    result = model.transcribe(
        file_path,
        task="transcribe",  # Transcribe, not translate
        language="en",  # Force English to avoid mis-detection
        verbose=False
    )
    
    blocks: List[AudioBlock] = []
    
    # Create AudioBlock for each segment
    for seg_idx, segment in enumerate(result.get("segments", [])):
        text = segment.get("text", "").strip()
        if not text:
            continue
        
        start_time = segment.get("start", 0.0)
        end_time = segment.get("end", 0.0)
        
        block_id = f"seg_{seg_idx}"
        
        block = AudioBlock(
            block_id=block_id,
            text=text,
            page=0,  # Not applicable for audio
            bbox=(0, 0, 0, 0),  # Not applicable
            font_size=12.0,  # Not applicable
            font_name="",  # Not applicable
            is_header=False,  # Not applicable
            start_time=start_time,
            end_time=end_time,
            confidence=segment.get("no_speech_prob", 0.0)  # Use no_speech_prob as confidence indicator
        )
        blocks.append(block)
    
    # Store Whisper metadata
    metadata = {
        "language": result.get("language", "en"),
        "language_probability": result.get("language_probability", 0.0),
    }
    
    return ExtractedDocument(
        source_path=file_path,
        format="audio",
        blocks=blocks,
        metadata=metadata
    )

