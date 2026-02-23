"""Main translation pipeline orchestrator."""
import os
import asyncio
from pathlib import Path
from typing import Optional, Callable
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
from models import ExtractedDocument
from ingestion import extract_pdf, extract_docx, extract_pptx, extract_audio
from translation import DocumentTranslator
from reconstruction import rebuild_docx, rebuild_pptx, rebuild_pdf, rebuild_audio_output


class TranslationPipeline:
    """Orchestrates the complete translation pipeline."""
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config.from_env()
        self.config.ensure_directories()
        self.translator = None
    
    def _detect_format(self, file_path: str) -> str:
        """Detect file format from extension."""
        ext = Path(file_path).suffix.lower()
        
        if ext == ".pdf":
            return "pdf"
        elif ext in [".docx", ".doc"]:
            return "docx"
        elif ext in [".pptx", ".ppt"]:
            return "pptx"
        elif ext in [".mp3", ".mp4", ".wav", ".m4a", ".ogg", ".flac"]:
            return "audio"
        else:
            raise ValueError(f"Unsupported file format: {ext}")
    
    def _extract(self, file_path: str, format: str) -> ExtractedDocument:
        """Route to correct extractor based on format."""
        # Validate file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Check file size
        if os.path.getsize(file_path) == 0:
            raise ValueError(f"File is empty: {file_path}")
        
        if format == "pdf":
            return extract_pdf(file_path)
        elif format == "docx":
            try:
                return extract_docx(file_path)
            except ValueError as e:
                # Re-raise with clearer context
                raise ValueError(f"Failed to extract text from Word document: {e}") from e
        elif format == "pptx":
            return extract_pptx(file_path)
        elif format == "audio":
            return extract_audio(file_path, self.config)
        else:
            raise ValueError(f"Unknown format: {format}")
    
    def _rebuild(
        self,
        extracted: ExtractedDocument,
        translations: dict,
        output_path: str
    ) -> str:
        """Route to correct builder based on format."""
        if extracted.format == "docx":
            return rebuild_docx(extracted, translations, output_path)
        elif extracted.format == "pptx":
            return rebuild_pptx(extracted, translations, output_path)
        elif extracted.format == "pdf":
            return rebuild_pdf(extracted, translations, output_path)
        elif extracted.format == "audio":
            # For audio, generate audio file (not SRT) by default
            return rebuild_audio_output(extracted, translations, output_path, self.config, generate_audio=True)
        else:
            raise ValueError(f"Unknown format: {extracted.format}")
    
    async def translate_file(
        self,
        input_path: str,
        output_path: Optional[str] = None,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> str:
        """
        Translate a file from English to French.
        
        Args:
            input_path: Path to input file
            output_path: Optional output path (auto-generated if not provided)
            progress_callback: Optional callback(blocks_done, blocks_total, block_id)
        
        Returns:
            Path to translated output file
        """
        # Detect format
        format_type = self._detect_format(input_path)
        
        # Extract text blocks
        if progress_callback:
            progress_callback(0, 100, "extracting")
        
        extracted = self._extract(input_path, format_type)
        
        if not extracted.blocks:
            raise ValueError("No text blocks found in document")
        
        # Initialize translator
        if not self.translator:
            self.translator = DocumentTranslator(self.config)
        
        # Translate blocks
        if progress_callback:
            progress_callback(0, len(extracted.blocks), "translating")
        
        translations = await self.translator.translate_blocks(
            extracted.blocks,
            progress_callback=progress_callback
        )
        
        # Generate output path if not provided
        if output_path is None:
            input_stem = Path(input_path).stem
            if extracted.format == "audio":
                # For audio, output as audio file (same format as input, or WAV)
                input_ext = Path(input_path).suffix.lower()
                if input_ext in ['.mp3', '.wav', '.m4a', '.ogg', '.flac']:
                    output_path = os.path.join(self.config.output_dir, f"{input_stem}_fr{input_ext}")
                else:
                    # Default to WAV if format not recognized
                    output_path = os.path.join(self.config.output_dir, f"{input_stem}_fr.wav")
            else:
                ext = Path(input_path).suffix
                output_path = os.path.join(self.config.output_dir, f"{input_stem}_fr{ext}")
        
        # Rebuild document
        if progress_callback:
            progress_callback(len(extracted.blocks), len(extracted.blocks), "rebuilding")
        
        result_path = self._rebuild(extracted, translations, output_path)
        
        return result_path
    
    async def close(self):
        """Clean up resources."""
        if self.translator:
            await self.translator.close()


# CLI entry point
async def main():
    """CLI entry point for direct pipeline execution."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python pipeline.py <input_file> [output_file]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    config = Config.from_env()
    pipeline = TranslationPipeline(config)
    
    def progress_callback(done: int, total: int, block_id: str):
        percent = int((done / total) * 100) if total > 0 else 0
        print(f"Progress: {percent}% ({done}/{total}) - {block_id}")
    
    try:
        result = await pipeline.translate_file(input_file, output_file, progress_callback)
        print(f"Translation complete: {result}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        await pipeline.close()


if __name__ == "__main__":
    asyncio.run(main())

