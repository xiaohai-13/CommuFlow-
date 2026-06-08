"""RAG — Chroma vector store with keyword fallback. Supports modelscope + HuggingFace."""
import os
from utils.config import EMBEDDING_MODEL, VECTOR_STORE_PATH, KNOWLEDGE_PATH
from utils.logger import logger

vectordb = None
_keyword_docs = []


def _load_keyword_docs():
    global _keyword_docs
    if _keyword_docs:
        return
    if not os.path.exists(KNOWLEDGE_PATH):
        return
    for fname in os.listdir(KNOWLEDGE_PATH):
        if fname.endswith(".md"):
            with open(os.path.join(KNOWLEDGE_PATH, fname), "r", encoding="utf-8") as f:
                _keyword_docs.append(f.read())
    logger.info(f"keyword fallback: {len(_keyword_docs)} docs loaded")


def _keyword_search(query: str, k: int = 3) -> list:
    _load_keyword_docs()
    scored = []
    for doc in _keyword_docs:
        score = sum(1 for i in range(len(query)-1) if query[i:i+2] in doc)
        scored.append((score, doc))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [doc for score, doc in scored[:k] if score > 0]


def _load_embeddings():
    """Load embedding model: try modelscope first, then HuggingFace."""
    from langchain_huggingface import HuggingFaceEmbeddings

    # Option 1: modelscope (download from China mirror)
    try:
        from modelscope import snapshot_download
        model_dir = snapshot_download(EMBEDDING_MODEL)
        logger.info(f"embeddings loaded via modelscope: {model_dir}")
        return HuggingFaceEmbeddings(model_name=model_dir)
    except ImportError:
        logger.info("modelscope not installed, trying HuggingFace...")
    except Exception as e:
        logger.warning(f"modelscope download failed: {e}")

    # Option 2: HuggingFace (respects HF_ENDPOINT env var)
    try:
        return HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    except Exception as e:
        raise RuntimeError(f"Failed to load embedding model: {e}")


def build_knowledge_base():
    global vectordb
    try:
        from langchain_community.document_loaders import DirectoryLoader, TextLoader
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        from langchain_community.vectorstores import Chroma

        if not os.path.exists(KNOWLEDGE_PATH) or not os.listdir(KNOWLEDGE_PATH):
            logger.warning("knowledge dir empty")
            return

        loader = DirectoryLoader(KNOWLEDGE_PATH, glob="**/*.md", loader_cls=TextLoader)
        docs = loader.load()
        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        chunks = splitter.split_documents(docs)
        embeddings = _load_embeddings()
        vectordb = Chroma.from_documents(chunks, embeddings, persist_directory=VECTOR_STORE_PATH)
        logger.info(f"vector store built: {len(chunks)} chunks")
    except Exception as e:
        logger.warning(f"vector build failed (will use keyword): {e}")


def init_rag():
    """Lazy init: try Chroma, fall back to keyword on any error."""
    global vectordb
    if vectordb is not None:
        return

    has_store = os.path.exists(VECTOR_STORE_PATH) and os.listdir(VECTOR_STORE_PATH)
    if not has_store:
        logger.info("no vector store on disk, skipping (keyword fallback active)")
        return

    try:
        from langchain_community.vectorstores import Chroma
        embeddings = _load_embeddings()
        vectordb = Chroma(persist_directory=VECTOR_STORE_PATH, embedding_function=embeddings)
        logger.info("vector store loaded from disk")
    except Exception as e:
        logger.warning(f"RAG init failed, using keyword fallback: {e}")
        vectordb = None


def retrieve_context(query: str, k: int = 3) -> list:
    global vectordb
    if vectordb is None:
        try:
            init_rag()
        except Exception:
            pass

    if vectordb is not None:
        try:
            docs = vectordb.similarity_search(query, k=k)
            return [doc.page_content for doc in docs]
        except Exception:
            pass

    return _keyword_search(query, k)
