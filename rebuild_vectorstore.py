"""
Script to rebuild the vector store from user guide documents
"""

from src.config_loader import ConfigLoader
from src.rag_system import RAGSystem

def main():
    print("Rebuilding Vector Store")
    print("=" * 80)

    config = ConfigLoader("config.yaml")
    vector_config = config.get_vector_store_config()
    documents_config = config.get('documents', default={})

    print("\nInitializing RAG system...")
    rag = RAGSystem(vector_config, documents_config)

    print("Loading documents...")
    doc_count = rag.load_documents()
    print(f"Loaded {doc_count} documents")

    print("\nCreating vector store...")
    rag.create_vector_store()

    print("\nTesting retrieval...")
    test_query = "How do I export a report?"
    docs = rag.retrieve_relevant_documents(test_query, k=3)

    print(f"\nRetrieved {len(docs)} documents for query: '{test_query}'")
    for i, doc in enumerate(docs, 1):
        print(f"\nDocument {i}:")
        print(f"Source: {doc.metadata.get('source', 'Unknown')}")
        print(f"Content preview: {doc.page_content[:200]}...")

    print("\n" + "=" * 80)
    print("Vector store rebuilt successfully!")

if __name__ == "__main__":
    main()
