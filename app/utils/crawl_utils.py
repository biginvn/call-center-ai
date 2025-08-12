"""
Utility functions for web crawling and ChromaDB integration.
"""

import re
from typing import List, Dict, Any

try:
    import chromadb
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False


def smart_chunk_markdown(markdown: str, max_len: int = 1000) -> List[str]:
    """Hierarchically splits markdown by #, ##, ### headers, then by characters, to ensure all chunks < max_len."""
    def split_by_header(md, header_pattern):
        indices = [m.start() for m in re.finditer(header_pattern, md, re.MULTILINE)]
        indices.append(len(md))
        return [md[indices[i]:indices[i+1]].strip() for i in range(len(indices)-1) if md[indices[i]:indices[i+1]].strip()]

    chunks = []

    for h1 in split_by_header(markdown, r'^# .+$'):
        if len(h1) > max_len:
            for h2 in split_by_header(h1, r'^## .+$'):
                if len(h2) > max_len:
                    for h3 in split_by_header(h2, r'^### .+$'):
                        if len(h3) > max_len:
                            for i in range(0, len(h3), max_len):
                                chunks.append(h3[i:i+max_len].strip())
                        else:
                            chunks.append(h3)
                else:
                    chunks.append(h2)
        else:
            chunks.append(h1)

    final_chunks = []

    for c in chunks:
        if len(c) > max_len:
            final_chunks.extend([c[i:i+max_len].strip() for i in range(0, len(c), max_len)])
        else:
            final_chunks.append(c)

    return [c for c in final_chunks if c]


def extract_section_info(chunk: str) -> Dict[str, Any]:
    """Extracts headers and stats from a chunk."""
    headers = re.findall(r'^(#+)\s+(.+)$', chunk, re.MULTILINE)
    header_str = '; '.join([f'{h[0]} {h[1]}' for h in headers]) if headers else ''

    return {
        "headers": header_str,
        "char_count": len(chunk),
        "word_count": len(chunk.split())
    }


def get_chroma_client(db_dir: str = "./chroma_db"):
    """Get ChromaDB client."""
    if not CHROMADB_AVAILABLE:
        raise Exception("ChromaDB is not installed. Please install it using: pip install chromadb")
    
    try:
        client = chromadb.PersistentClient(path=db_dir)
        return client
    except Exception as e:
        raise Exception(f"Failed to connect to ChromaDB: {str(e)}")


def get_or_create_collection(client, collection_name: str, embedding_model_name: str = "all-MiniLM-L6-v2"):
    """Get or create a ChromaDB collection."""
    if not CHROMADB_AVAILABLE:
        raise Exception("ChromaDB is not installed. Please install it using: pip install chromadb")
        
    try:
        collection = client.get_collection(name=collection_name)
        return collection
    except Exception:
        # Collection doesn't exist, create it
        collection = client.create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        return collection


def add_documents_to_collection(collection, ids: List[str], documents: List[str], metadatas: List[Dict[str, Any]], batch_size: int = 100):
    """Add documents to ChromaDB collection in batches."""
    for i in range(0, len(ids), batch_size):
        batch_ids = ids[i:i+batch_size]
        batch_documents = documents[i:i+batch_size]
        batch_metadatas = metadatas[i:i+batch_size]
        
        collection.add(
            ids=batch_ids,
            documents=batch_documents,
            metadatas=batch_metadatas
        )
