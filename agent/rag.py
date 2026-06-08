import os
from langchain_community.document_loaders import TextLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from utils.config import EMBEDDING_MODEL, VECTOR_STORE_PATH, KNOWLEDGE_PATH
from utils.logger import logger

vectordb = None


def build_knowledge_base():
    global vectordb
    if not os.path.exists(KNOWLEDGE_PATH) or not os.listdir(KNOWLEDGE_PATH):
        logger.warning("knowledge dir empty, skip vector build")
        return

    loader = DirectoryLoader(KNOWLEDGE_PATH, glob="**/*.md", loader_cls=TextLoader)
    docs = loader.load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(docs)
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    vectordb = Chroma.from_documents(chunks, embeddings, persist_directory=VECTOR_STORE_PATH)
    logger.info(f"vector store built: {len(chunks)} chunks")


def init_rag():
    global vectordb
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    if os.path.exists(VECTOR_STORE_PATH) and os.listdir(VECTOR_STORE_PATH):
        vectordb = Chroma(persist_directory=VECTOR_STORE_PATH, embedding_function=embeddings)
        logger.info("vector store loaded from disk")
    else:
        build_knowledge_base()


def retrieve_context(query: str, k: int = 3) -> list:
    global vectordb
    if vectordb is None:
        try:
            init_rag()
        except Exception as e:
            logger.warning(f"rag init failed: {e}")
            return []
    if vectordb is None:
        return []
    docs = vectordb.similarity_search(query, k=k)
    return [doc.page_content for doc in docs]