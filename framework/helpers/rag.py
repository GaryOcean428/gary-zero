import os
from pathlib import Path
from typing import List

from langchain_core.documents import Document


def extract_file(path: str) -> List[Document]:
    """
    Extract text content from a file and convert it to Document objects for RAG.
    
    Args:
        path: Path to the file to extract content from
        
    Returns:
        List of Document objects containing the extracted text
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        IOError: If the file cannot be read
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
    
    try:
        file_path = Path(path)
        
        # Read file content as bytes
        with open(file_path, 'rb') as f:
            content = f.read()
        
        # Extract text chunks using the existing extract_text function
        text_chunks = extract_text(content)
        
        # Convert chunks to Document objects
        documents = []
        for i, chunk in enumerate(text_chunks):
            # Skip binary markers
            if chunk == "[BINARY]":
                continue
                
            # Create document with metadata
            doc = Document(
                page_content=chunk,
                metadata={
                    "source": str(file_path),
                    "file_name": file_path.name,
                    "file_extension": file_path.suffix,
                    "chunk_index": i,
                    "file_size": len(content),
                    "chunk_size": len(chunk)
                }
            )
            documents.append(doc)
        
        return documents
        
    except Exception as e:
        raise IOError(f"Error reading file {path}: {str(e)}") from e


def extract_text(content: bytes, chunk_size: int = 128) -> list[str]:
    result = []

    def is_binary_chunk(chunk: bytes) -> bool:
        # Check for high concentration of control chars
        try:
            text = chunk.decode("utf-8", errors="ignore")
            control_chars = sum(1 for c in text if ord(c) < 32 and c not in "\n\r\t")
            return control_chars / len(text) > 0.3
        except UnicodeDecodeError:
            return True

    # Process the content in overlapping chunks to handle boundaries
    pos = 0
    while pos < len(content):
        # Get current chunk with overlap
        chunk_end = min(pos + chunk_size, len(content))

        # Add overlap to catch word boundaries, unless at end of content
        if chunk_end < len(content):
            # Look ahead for next newline or space to avoid splitting words
            for i in range(chunk_end, min(chunk_end + 100, len(content))):
                if content[i : i + 1] in [b" ", b"\n", b"\r"]:
                    chunk_end = i + 1
                    break

        chunk = content[pos:chunk_end]

        if is_binary_chunk(chunk):
            if not result or result[-1] != "[BINARY]":
                result.append("[BINARY]")
        else:
            try:
                text = chunk.decode("utf-8", errors="ignore").strip()
                if text:  # Only add non-empty text chunks
                    result.append(text)
            except UnicodeDecodeError:
                if not result or result[-1] != "[BINARY]":
                    result.append("[BINARY]")

        pos = chunk_end

    return result
