import os
from pathlib import Path

# ============ BASE PATHS ============
BASE_DIR = Path(__file__).parent.parent
MODEL_DIR = BASE_DIR / "models"
DATA_DIR = BASE_DIR / "data"
VECTORSTORE_DIR = BASE_DIR / "vectorstore" / "chroma_db"

# ============ MODEL SETTINGS ============
LLM_MODEL_PATH = MODEL_DIR / "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
LLM_CONTEXT_LENGTH = 2048
LLM_MAX_TOKENS = 512
LLM_TEMPERATURE = 0.3
LLM_GPU_LAYERS = 0          # Set to 0 for CPU-only, increase for GPU offload
LLM_THREADS = 4             # Number of CPU threads

# ============ EMBEDDING SETTINGS ============
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384

# ============ CHUNKING SETTINGS ============
CHUNK_SIZE = 500
CHUNK_OVERLAP = 200
SEMANTIC_CHUNK_BREAKPOINT_THRESHOLD = 0.3

# ============ RETRIEVAL SETTINGS ============
TOP_K_RESULTS = 5
MMR_DIVERSITY_SCORE = 0.3
MULTI_QUERY_COUNT = 3
BM25_WEIGHT = 0.3
VECTOR_WEIGHT = 0.7
RERANK_TOP_N = 3

# ============ CHROMADB SETTINGS ============
CHROMA_COLLECTION_NAME = "rag_knowledge_base"
CHROMA_DISTANCE_METRIC = "cosine"

# ============ API KEYS (loaded from .env) ============
SEARCHAPI_KEY = os.getenv("SEARCHAPI_KEY", "")

# ============ UI SETTINGS ============
APP_TITLE = "🧠 Local RAG Knowledge Assistant"
APP_ICON = "🧠"
MAX_UPLOAD_SIZE_MB = 50
SUPPORTED_FILE_TYPES = ["pdf"]

# ============ CONTENT TYPE TAGS ============
CONTENT_TYPE_TEXT = "text"
CONTENT_TYPE_IMAGE = "image"
CONTENT_TYPE_TABLE = "table"
