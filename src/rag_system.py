"""
RAG (Retrieval Augmented Generation) System Module

This module implements the document retrieval system for user guide questions.
It handles document loading, chunking, embedding, and similarity search.
"""

import os
from typing import List, Dict, Any
from pathlib import Path

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader,
    UnstructuredMarkdownLoader,
    UnstructuredHTMLLoader
)
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma, FAISS
from langchain.schema import Document


class RAGSystem:
    """
    Manages document ingestion, vectorization, and retrieval for user guides.

    This system loads user guide documents, splits them into chunks,
    creates embeddings, and enables similarity-based retrieval.

    Attributes:
        config (Dict): RAG system configuration
        embeddings: Embedding model for vectorization
        vector_store: Vector database for document storage and retrieval
        documents (List[Document]): Loaded documents
    """

    def __init__(self, vector_config: Dict[str, Any], documents_config: Dict[str, Any]):
        """
        Initialize the RAG system.

        Args:
            vector_config (Dict): Vector store configuration
            documents_config (Dict): Documents configuration
        """
        self.vector_config = vector_config
        self.documents_config = documents_config
        self.embeddings = None
        self.vector_store = None
        self.documents = []

        self._initialize_embeddings()

    def _initialize_embeddings(self) -> None:
        """
        Initialize the embedding model based on configuration.
        """
        embedding_model = self.vector_config.get(
            'embedding_model',
            'sentence-transformers/all-MiniLM-L6-v2'
        )
        self.embeddings = HuggingFaceEmbeddings(model_name=embedding_model)

    def load_documents(self) -> int:
        """
        Load all documents from the configured user guides directory.

        Returns:
            int: Number of documents loaded

        Raises:
            FileNotFoundError: If user guides directory does not exist
        """
        guides_path = Path(self.documents_config.get('user_guides_path', './data/user_guides'))

        if not guides_path.exists():
            raise FileNotFoundError(f"User guides directory not found: {guides_path}")

        supported_formats = self.documents_config.get('supported_formats', ['.txt'])
        loaded_docs = []

        for file_path in guides_path.rglob('*'):
            if file_path.is_file() and file_path.suffix in supported_formats:
                try:
                    docs = self._load_single_document(file_path)
                    loaded_docs.extend(docs)
                except Exception as e:
                    print(f"Warning: Failed to load {file_path}: {str(e)}")

        self.documents = loaded_docs
        return len(self.documents)

    def _load_single_document(self, file_path: Path) -> List[Document]:
        """
        Load a single document based on its file type.

        Args:
            file_path (Path): Path to the document

        Returns:
            List[Document]: List of loaded documents

        Raises:
            ValueError: If file format is not supported
        """
        suffix = file_path.suffix.lower()

        loaders = {
            '.txt': TextLoader,
            '.pdf': PyPDFLoader,
            '.md': UnstructuredMarkdownLoader,
            '.html': UnstructuredHTMLLoader
        }

        if suffix not in loaders:
            raise ValueError(f"Unsupported file format: {suffix}")

        loader = loaders[suffix](str(file_path))
        return loader.load()

    def create_vector_store(self) -> None:
        """
        Create vector store from loaded documents.

        This method splits documents into chunks, creates embeddings,
        and stores them in the vector database.

        Raises:
            ValueError: If no documents have been loaded
        """
        if not self.documents:
            raise ValueError("No documents loaded. Call load_documents() first.")

        chunk_size = self.vector_config.get('chunk_size', 1000)
        chunk_overlap = self.vector_config.get('chunk_overlap', 200)

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
        )

        chunks = text_splitter.split_documents(self.documents)

        store_type = self.vector_config.get('type', 'chromadb').lower()

        if store_type == 'chromadb':
            self._create_chroma_store(chunks)
        elif store_type == 'faiss':
            self._create_faiss_store(chunks)
        else:
            raise ValueError(f"Unsupported vector store type: {store_type}")

    def _create_chroma_store(self, chunks: List[Document]) -> None:
        """
        Create ChromaDB vector store.

        Args:
            chunks (List[Document]): Document chunks to store
        """
        persist_directory = self.vector_config.get('persist_directory', './data/vector_db')
        collection_name = self.vector_config.get('collection_name', 'user_guides')

        self.vector_store = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            persist_directory=persist_directory,
            collection_name=collection_name
        )

    def _create_faiss_store(self, chunks: List[Document]) -> None:
        """
        Create FAISS vector store.

        Args:
            chunks (List[Document]): Document chunks to store
        """
        self.vector_store = FAISS.from_documents(
            documents=chunks,
            embedding=self.embeddings
        )

        persist_directory = self.vector_config.get('persist_directory', './data/vector_db')
        Path(persist_directory).mkdir(parents=True, exist_ok=True)
        self.vector_store.save_local(persist_directory)

    def load_existing_vector_store(self) -> bool:
        """
        Load an existing vector store from disk.

        Returns:
            bool: True if store loaded successfully, False otherwise
        """
        try:
            persist_directory = self.vector_config.get('persist_directory', './data/vector_db')
            store_type = self.vector_config.get('type', 'chromadb').lower()

            if store_type == 'chromadb':
                collection_name = self.vector_config.get('collection_name', 'user_guides')
                self.vector_store = Chroma(
                    persist_directory=persist_directory,
                    embedding_function=self.embeddings,
                    collection_name=collection_name
                )
            elif store_type == 'faiss':
                self.vector_store = FAISS.load_local(
                    persist_directory,
                    self.embeddings
                )
            else:
                return False

            return True
        except Exception as e:
            print(f"Failed to load existing vector store: {str(e)}")
            return False

    def retrieve_relevant_documents(self, query: str, k: int = 3) -> List[Document]:
        """
        Retrieve the most relevant documents for a query.

        Args:
            query (str): User query
            k (int): Number of documents to retrieve

        Returns:
            List[Document]: Retrieved relevant documents

        Raises:
            ValueError: If vector store has not been initialized
        """
        if self.vector_store is None:
            raise ValueError("Vector store not initialized. Call create_vector_store() or load_existing_vector_store().")

        return self.vector_store.similarity_search(query, k=k)

    def get_context_for_query(self, query: str, k: int = 3) -> str:
        """
        Get formatted context string for a query.

        Args:
            query (str): User query
            k (int): Number of documents to retrieve

        Returns:
            str: Formatted context string
        """
        docs = self.retrieve_relevant_documents(query, k=k)

        context_parts = []
        for i, doc in enumerate(docs, 1):
            source = doc.metadata.get('source', 'Unknown')
            content = doc.page_content
            context_parts.append(f"[Source {i}: {source}]\n{content}")

        return "\n\n".join(context_parts)

    def initialize_or_load(self) -> str:
        """
        Initialize the RAG system by either loading existing store or creating new one.

        Returns:
            str: Status message indicating what action was taken
        """
        if self.load_existing_vector_store():
            return "Loaded existing vector store"
        else:
            doc_count = self.load_documents()
            self.create_vector_store()
            return f"Created new vector store with {doc_count} documents"
