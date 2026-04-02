# IMPORTS

import os
import sys
import time
import shutil

# LangChain: Document loaders
from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader

# LangChain: Text splitter
from langchain.text_splitter import RecursiveCharacterTextSplitter

# LangChain: Embedding wrapper around sentence-transformers
from langchain_community.embeddings import SentenceTransformerEmbeddings

# LangChain: Chroma vector store integration
from langchain_community.vectorstores import Chroma

# Directory that contains the PDF files to ingest.
PDF_DIRECTORY = "./pdf_documents"
CHROMA_PERSIST_DIR = "./chroma_db"


CHUNK_SIZE = 1000          # max characters per chunk
CHUNK_OVERLAP = 200        # overlap between consecutive chunks to preserve
                           # semantic continuity across chunk boundaries

# ── Embedding model ──

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

# Name of the Chroma collection (acts like a "table" inside the DB).
CHROMA_COLLECTION_NAME = "local_rag_collection"



# STEP 1 — LOADING PDF DOCUMENTS

def load_documents(pdf_dir: str) -> list:
    """
    Recursively loads every PDF in *pdf_dir*.
    """
    # Validate input directory
    if not os.path.isdir(pdf_dir):
        print(f"[ERROR] The directory '{pdf_dir}' does not exist.")
        print("        Please create it and add your PDF files before running this script.")
        sys.exit(1)

    pdf_count = len([f for f in os.listdir(pdf_dir) if f.lower().endswith(".pdf")])
    if pdf_count == 0:
        print(f"[ERROR] No PDF files found in '{pdf_dir}'.")
        print("        Add at least one .pdf file and re-run.")
        sys.exit(1)

    print(f"[1/4] Loading PDFs from '{pdf_dir}' ...")
    print(f"       Found {pdf_count} PDF file(s).\n")

    loader = DirectoryLoader(
        path=pdf_dir,
        glob="**/*.pdf",          # match PDFs in sub-folders too
        loader_cls=PyPDFLoader,   # per-file loader
        show_progress=True,       # progress bar in terminal
        use_multithreading=True,  # speed up loading for large collections
    )

    documents = loader.load()
    print(f"\n Loaded {len(documents)} page(s) across {pdf_count} PDF(s).\n")
    return documents


# STEP 2 — SPLIT DOCUMENTS INTO CHUNKS


def split_documents(documents: list, chunk_size: int, chunk_overlap: int) -> list:
    """
    Split Document objects into smaller, overlapping text chunks using RecursiveCharacterTextSplitter.
    """
    print(f"[2/4] Splitting documents into chunks ...")
    print(f"       chunk_size  = {chunk_size} characters")
    print(f"       chunk_overlap = {chunk_overlap} characters\n")

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,           # count characters (not tokens)
        is_separator_regex=False,      # treat separators as plain strings
    )

    chunks = text_splitter.split_documents(documents)
    print(f"        Created {len(chunks)} chunk(s) from {len(documents)} page(s).\n")
    return chunks



# STEP 3 — INITIALISING THE EMBEDDING MODEL


def get_embedding_function(model_name: str) -> SentenceTransformerEmbeddings:
    """
    Return a LangChain-compatible embedding function backed by
    the specified SentenceTransformer model.
    """
    print(f"[3/4] Loading embedding model: '{model_name}' ...")
    print(f"       Vector dimensions : 384")
    print(f"       Runs on           : CPU (no GPU required)\n")

    embedding_fn = SentenceTransformerEmbeddings(model_name=model_name)

    print(f"        Embedding model loaded successfully.\n")
    return embedding_fn



# STEP 4 — CREATE / UPDATE THE CHROMA VECTOR STORE


def create_vector_store(
    chunks: list,
    embedding_fn: SentenceTransformerEmbeddings,
    persist_dir: str,
    collection_name: str,
) -> Chroma:
    """
    Embed every chunk and store it in a ChromaDB collection that is persisted
    to *persist_dir*.
    """
    print(f"[4/4] Creating ChromaDB vector store ...")
    print(f"       Persist directory : {persist_dir}")
    print(f"       Collection name   : {collection_name}")
    print(f"       Chunks to embed   : {len(chunks)}\n")

    start = time.time()

    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embedding_fn,
        persist_directory=persist_dir,
        collection_name=collection_name,
    )

    elapsed = round(time.time() - start, 2)
    print(f" Vector store created and persisted in {elapsed}s.\n")
    return vector_store



# MAIN ENTRY POINT


def main():
    """
    Orchestrate the full ingestion pipeline:
        Load → Split → Embed → Store
    """
    print("=" * 70)
    print("   LOCAL RAG SYSTEM — DATA INGESTION PIPELINE")
    print("=" * 70, "\n")

    # ── Guard: skip re-ingestion if the Chroma DB already exists ────────
    if os.path.isdir(CHROMA_PERSIST_DIR):
        print(f"[INFO] Existing vector store detected at '{CHROMA_PERSIST_DIR}'.")
        user_input = input("       Do you want to re-ingest? (y/N): ").strip().lower()
        if user_input != "y":
            print("\n       Skipping ingestion. Loading existing store ...\n")
            embedding_fn = get_embedding_function(EMBEDDING_MODEL_NAME)
            vector_store = Chroma(
                persist_directory=CHROMA_PERSIST_DIR,
                embedding_function=embedding_fn,
                collection_name=CHROMA_COLLECTION_NAME,
            )
            collection_size = vector_store._collection.count()
            print(f"        Loaded existing store with {collection_size} vectors.\n")
            print("=" * 70)
            print("   INGESTION SKIPPED — EXISTING STORE LOADED SUCCESSFULLY")
            print("=" * 70)
            return vector_store
        else:
            # Remove old store so we start fresh
            print(f"       Removing old store at '{CHROMA_PERSIST_DIR}' ...")
            shutil.rmtree(CHROMA_PERSIST_DIR)
            print("       Done.\n")

    # Loading 
    documents = load_documents(PDF_DIRECTORY)

    # Spliting
    chunks = split_documents(documents, CHUNK_SIZE, CHUNK_OVERLAP)

    # Embeding
    embedding_fn = get_embedding_function(EMBEDDING_MODEL_NAME)

    # Storing
    vector_store = create_vector_store(
        chunks=chunks,
        embedding_fn=embedding_fn,
        persist_dir=CHROMA_PERSIST_DIR,
        collection_name=CHROMA_COLLECTION_NAME,
    )



    return vector_store
if __name__ == "__main__":
    main()
