"""
Nura - Chunking Utilities
Helper functions to split documents and reports into manageable chunks for vector embeddings
"""

from typing import List


def chunk_by_fixed_size(text: str, chunk_size: int, overlap: int) -> List[str]:
    """
    Split text into fixed-size character chunks with a specified character overlap.
    
    Args:
        text: The source string to chunk.
        chunk_size: Maximum characters per chunk. Must be positive.
        overlap: Character overlap between consecutive chunks. Must be non-negative and < chunk_size.
        
    Returns:
        List of chunked text strings.
    """
    if not text or text.strip() == "":
        return []
    if chunk_size <= 0:
        raise ValueError("chunk_size must be a positive integer")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be non-negative and less than chunk_size")
        
    chunks = []
    text_length = len(text)
    start = 0
    
    # Calculate step size
    step = chunk_size - overlap
    
    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        if end >= text_length:
            break
        start += step
        
    return chunks


def chunk_by_paragraph(text: str, max_chunk_size: int = 1000) -> List[str]:
    """
    Split text by double newlines into paragraphs, merging small adjacent paragraphs 
    together until max_chunk_size characters is reached. Merged paragraphs are separated 
    by double newlines. Oversized paragraphs are split using fixed-size chunking.
    
    Args:
        text: The source text to chunk.
        max_chunk_size: Target maximum characters in a merged paragraph chunk.
        
    Returns:
        List of paragraph-aligned chunks.
    """
    if not text or text.strip() == "":
        return []
    if max_chunk_size <= 0:
        raise ValueError("max_chunk_size must be a positive integer")

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []
    current_chunk: List[str] = []
    current_size = 0
    
    for p in paragraphs:
        # If single paragraph exceeds max size, split it independently
        if len(p) > max_chunk_size:
            if current_chunk:
                chunks.append("\n\n".join(current_chunk))
                current_chunk = []
                current_size = 0
            
            # Split paragraph using fixed-size chunking (10% overlap fallback)
            overlap = max_chunk_size // 10
            p_chunks = chunk_by_fixed_size(p, max_chunk_size, overlap)
            chunks.extend(p_chunks)
        elif current_size + len(p) + (2 if current_chunk else 0) > max_chunk_size:
            # Yield accumulated chunk and reset
            chunks.append("\n\n".join(current_chunk))
            current_chunk = [p]
            current_size = len(p)
        else:
            current_chunk.append(p)
            current_size += len(p) + (2 if len(current_chunk) > 1 else 0)
            
    if current_chunk:
        chunks.append("\n\n".join(current_chunk))
        
    return chunks


def chunk_by_sliding_window(text: str, window_size: int, step_size: int) -> List[str]:
    """
    Split text into chunks using a sliding window of window_size words/tokens, moving by step_size.
    
    Args:
        text: The source text to chunk.
        window_size: Number of words per window chunk. Must be positive.
        step_size: Number of words to step between chunks. Must be positive.
        
    Returns:
        List of text chunks, each containing up to window_size words.
    """
    if not text or text.strip() == "":
        return []
    if window_size <= 0 or step_size <= 0:
        raise ValueError("window_size and step_size must be positive integers")
        
    words = text.split()
    if not words:
        return []
        
    chunks = []
    total_words = len(words)
    start = 0
    
    while start < total_words:
        window_words = words[start:start + window_size]
        chunks.append(" ".join(window_words))
        if start + window_size >= total_words:
            break
        start += step_size
        
    return chunks
