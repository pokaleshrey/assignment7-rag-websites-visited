from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import hashlib
import numpy as np
from pathlib import Path
import faiss
import sys
import requests
import json
from markitdown import MarkItDown
from tqdm import tqdm

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

EMBED_URL = "http://localhost:11434/api/embeddings"
EMBED_MODEL = "nomic-embed-text"
CHUNK_SIZE = 256
CHUNK_OVERLAP = 40
ROOT = Path(__file__).parent.resolve()

class InputData(BaseModel):
    url: str
    body: str

def get_embedding(text: str) -> np.ndarray:
    response = requests.post(EMBED_URL, json={"model": EMBED_MODEL, "prompt": text})
    response.raise_for_status()
    return np.array(response.json()["embedding"], dtype=np.float32)

def chunk_text(text, size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    words = text.split()
    for i in range(0, len(words), size - overlap):
        yield " ".join(words[i:i+size])

def mcp_log(level: str, message: str) -> None:
    """Log a message to stderr to avoid interfering with JSON communication"""
    sys.stderr.write(f"{level}: {message}\n")
    sys.stderr.flush()

def process_documents(url: str, html_body: str):
    """Process a single document (URL) and create/update FAISS index"""
    mcp_log("INFO", f"Indexing document for URL: {url}")
    ROOT = Path(__file__).parent.resolve()
    INDEX_CACHE = ROOT / "faiss_index"
    INDEX_CACHE.mkdir(exist_ok=True)
    INDEX_FILE = INDEX_CACHE / "index.bin"
    METADATA_FILE = INDEX_CACHE / "metadata.json"
    CACHE_FILE = INDEX_CACHE / "doc_index_cache.json"

    def compute_hash(content):
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    CACHE_META = json.loads(CACHE_FILE.read_text()) if CACHE_FILE.exists() else {}
    metadata = json.loads(METADATA_FILE.read_text()) if METADATA_FILE.exists() else []
    index = faiss.read_index(str(INDEX_FILE)) if INDEX_FILE.exists() else None

    # Convert HTML body to markdown text
    # Ensure the result is a string
    markdown_text = str(MarkItDown().convert(str(url)))

    # Compute hash for the markdown text
    content_hash = compute_hash(markdown_text)
    if url in CACHE_META and CACHE_META[url] == content_hash:
        mcp_log("SKIP", f"Skipping unchanged URL: {url}")
        return

    try:
        chunks = list(chunk_text(markdown_text))
        embeddings_for_url = []
        new_metadata = []
        for i, chunk in enumerate(tqdm(chunks, desc=f"Embedding {url}")):
            embedding = get_embedding(chunk)
            embeddings_for_url.append(embedding)
            new_metadata.append({"url": url, "chunk": chunk, "chunk_id": f"{url}_{i}"})

        if embeddings_for_url:
            if index is None:
                dim = len(embeddings_for_url[0])
                index = faiss.IndexFlatL2(dim)
            index.add(np.stack(embeddings_for_url))
            metadata.extend(new_metadata)

        CACHE_META[url] = content_hash
    except Exception as e:
        mcp_log("ERROR", f"Failed to process URL {url}: {e}")

    CACHE_FILE.write_text(json.dumps(CACHE_META, indent=2))
    METADATA_FILE.write_text(json.dumps(metadata, indent=2))
    if index and index.ntotal > 0:
        faiss.write_index(index, str(INDEX_FILE))
        mcp_log("SUCCESS", "Saved FAISS index and metadata")
    else:
        mcp_log("WARN", "No new data or updates to process.")

def ensure_faiss_ready():
    from pathlib import Path
    index_path = ROOT / "faiss_index" / "index.bin"
    meta_path = ROOT / "faiss_index" / "metadata.json"
    if not (index_path.exists() and meta_path.exists()):
        mcp_log("INFO", "Index not found — running process_documents()...")
        process_documents()
    else:
        mcp_log("INFO", "Index already exists. Skipping regeneration.")

@app.post("/index-website")
async def index_website(data: InputData):
    if not data.url or not data.body:
        raise HTTPException(status_code=400, detail="Both 'url' and 'body' are required")

    # Pass the URL and body to process_documents
    mcp_log("INFO", f"Processing website: {data.url}")
    process_documents(data.url, data.body)

    response = {
        "message": "Data processed successfully",
        "url": data.url,
        "body": data.body
    }
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "chrome_website_indexer:app",
        host="127.0.0.1",
        port=8080, 
        reload=True
    )

