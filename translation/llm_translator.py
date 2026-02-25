"""LLM-based translation using Ollama."""
import asyncio
import httpx
from typing import List, Dict, Callable, Optional
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models import TextBlock
from config import Config


# System prompt for translation
SYSTEM_PROMPT = """You are a professional English-to-French translator.
Translate the given text accurately and naturally.

Rules:
- Preserve the original meaning precisely
- Use formal French (standard professional register)
- Keep formatting markers like bullet points, numbers, or special characters exactly as-is
- Do NOT add explanations or commentary
- Return ONLY the translated text, nothing else
- If the input is a title or header, keep the translation concise"""


def chunk_blocks(blocks: List[TextBlock], max_tokens: int = 800) -> List[List[TextBlock]]:
    """
    Group blocks into chunks for translation.
    
    Estimates token count as len(text) / 4 (rough approximation).
    Groups consecutive blocks until chunk exceeds max_tokens.
    Carries last 1 block from one chunk into the next (overlap) for context continuity.
    """
    chunks = []
    current_chunk = []
    current_tokens = 0
    
    for i, block in enumerate(blocks):
        # Estimate tokens (rough: ~4 chars per token)
        block_tokens = len(block.text) / 4
        
        if current_tokens + block_tokens > max_tokens and current_chunk:
            # Start new chunk, but carry over last block for context
            if len(current_chunk) > 0:
                # Keep last block in current chunk, start new chunk with it
                chunks.append(current_chunk)
                current_chunk = [current_chunk[-1]] if current_chunk else []
                current_tokens = len(current_chunk[-1].text) / 4 if current_chunk else 0
        
        current_chunk.append(block)
        current_tokens += block_tokens
    
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks


class OllamaTranslator:
    """Translator using Ollama local LLM."""
    
    def __init__(self, config: Config):
        self.config = config
        self.base_url = config.ollama_url
        self.model = config.ollama_model
        self.client = httpx.AsyncClient(timeout=300.0)  # 5 minute timeout for large blocks
    
    async def translate_text(
        self,
        text: str,
        context_hint: Optional[str] = None
    ) -> str:
        """
        Translate a single text block using Ollama.
        
        Args:
            text: English text to translate
            context_hint: Optional context hint (e.g., "slide title")
        
        Returns:
            Translated French text
        """
        # Build user message with optional context hint
        user_message = text
        if context_hint:
            user_message = f"{text}\n\n[Context: {context_hint}]"
        
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ]
        
        try:
            response = await self.client.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": 0.1,
                    "stream": False
                }
            )
            response.raise_for_status()
            data = response.json()
            
            # Extract translated text from response
            translated = data.get("message", {}).get("content", "").strip()
            
            # Remove any potential explanations or commentary from the model
            # Filter out lines that look like instructions or metadata
            lines = translated.split("\n")
            filtered_lines = []
            
            # Common prefixes that indicate commentary/instructions (not actual translation)
            commentary_prefixes = [
                "translation:", "translation :", "here is", "here's", "voici", 
                "les règles", "the following", "rules:", "règles:",
                "note:", "note :", "remarque:", "remarque :",
                "context:", "contexte:", "hint:", "indice:"
            ]
            
            for line in lines:
                line_stripped = line.strip()
                if not line_stripped:
                    # Preserve empty lines (they might be intentional paragraph breaks)
                    filtered_lines.append("")
                    continue
                
                # Skip lines that look like instructions or commentary
                line_lower = line_stripped.lower()
                if any(line_lower.startswith(prefix.lower()) for prefix in commentary_prefixes):
                    continue
                
                # Skip lines that are just metadata keywords
                if line_lower in ["translation", "traduction", "rules", "règles"]:
                    continue
                
                # Keep the line (it's actual translated content)
                filtered_lines.append(line_stripped)
            
            # Join all non-commentary lines, preserving line breaks and structure
            if filtered_lines:
                # Remove leading/trailing empty lines but preserve internal ones
                while filtered_lines and not filtered_lines[0]:
                    filtered_lines.pop(0)
                while filtered_lines and not filtered_lines[-1]:
                    filtered_lines.pop()
                translated = "\n".join(filtered_lines)
            else:
                # If we filtered everything, use the original (might be all commentary or single line)
                translated = translated.strip()
            
            return translated if translated else text  # Fallback to original if empty
        
        except Exception as e:
            # Log error and return original text as fallback
            print(f"Translation error: {e}")
            return text
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


class DocumentTranslator:
    """Unified interface for translating documents with concurrency control."""
    
    def __init__(self, config: Config):
        self.config = config
        self.translator = OllamaTranslator(config)
        self.semaphore = asyncio.Semaphore(config.translation_concurrency)
    
    async def translate_blocks(
        self,
        blocks: List[TextBlock],
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> Dict[str, str]:
        """
        Translate all blocks with concurrency control.
        
        Args:
            blocks: List of TextBlock objects to translate
            progress_callback: Optional callback(blocks_done, blocks_total, block_id)
        
        Returns:
            Dictionary mapping block_id to translated text
        """
        total = len(blocks)
        translations = {}
        
        async def translate_one(block: TextBlock):
            async with self.semaphore:
                # Determine context hint
                context_hint = None
                if block.is_header:
                    context_hint = "slide title" if hasattr(block, "slide_index") else "header"
                
                translated = await self.translator.translate_text(block.text, context_hint)
                translations[block.block_id] = translated
                
                if progress_callback:
                    progress_callback(len(translations), total, block.block_id)
        
        # Translate all blocks in parallel
        tasks = [translate_one(block) for block in blocks]
        await asyncio.gather(*tasks)
        
        return translations
    
    async def close(self):
        """Close the translator."""
        await self.translator.close()

