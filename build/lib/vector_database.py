import os
import streamlit as st
from langchain_community.document_loaders import PDFPlumberLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

# Define the directory to store PDFs
PDFS_DIRECTORY = "pdfs/"
# Define the path to store the FAISS database
FAISS_DB_PATH = "vectorstore/db_faiss"

# Ensure directories exist
os.makedirs(PDFS_DIRECTORY, exist_ok=True)
os.makedirs("vectorstore", exist_ok=True)


def upload_pdf(file) -> str:
    """
    Save an uploaded PDF file to the local directory.

    Args:
        file: The uploaded file object (e.g., from Streamlit's file_uploader).

    Returns:
        str: The local file path where the PDF was saved.
    """
    file_path = os.path.join(PDFS_DIRECTORY, file.name)
    with open(file_path, "wb") as f:
        f.write(file.getbuffer())
    
    return file_path


def load_pdf(file_path: str) -> list[Document]:
    """
    Load a PDF document and extract its text content.

    Args:
        file_path (str): The path to the PDF file.

    Returns:
        list[Document]: A list of LangChain Document objects extracted from the PDF.
    """
    loader = PDFPlumberLoader(file_path)
    return loader.load()


def create_chunks(documents: list[Document], file_name: str) -> list[Document]:
    """
    Split documents into smaller chunks for vectorization.

    Args:
        documents (list[Document]): The loaded documents.
        file_name (str): The name of the source file to embed as metadata.

    Returns:
        list[Document]: A list of smaller chunked Document objects.
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        add_start_index=True
    )
    text_chunks = text_splitter.split_documents(documents)
    
    # Add metadata (file name) to each chunk to enable filtering during retrieval
    for chunk in text_chunks:
        chunk.metadata["source"] = file_name
    
    return text_chunks


@st.cache_resource
def get_embedding_model() -> HuggingFaceEmbeddings:
    """
    Initialize and cache the embedding model.
    Cached via Streamlit to prevent reloading the model on every rerun.

    Returns:
        HuggingFaceEmbeddings: The initialized embedding model.
    """
    return HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")


def index_pdf(file_path: str) -> FAISS:
    """
    Process a PDF file and index its contents into the FAISS vector database.
    If a database already exists, the new documents are merged into it.

    Args:
        file_path (str): The path to the PDF file to index.

    Returns:
        FAISS: The updated FAISS vector database instance.
    """
    documents = load_pdf(file_path)
    file_name = os.path.basename(file_path)
    text_chunks = create_chunks(documents, file_name)
    
    embedding_model = get_embedding_model()
    new_db = FAISS.from_documents(text_chunks, embedding_model)
    
    # Merge with existing index if it exists, otherwise create new
    if os.path.exists(FAISS_DB_PATH) and os.listdir(FAISS_DB_PATH):
        try:
            # allow_dangerous_deserialization is needed to load local pickle files in FAISS
            existing_db = FAISS.load_local(FAISS_DB_PATH, embedding_model, allow_dangerous_deserialization=True)
            existing_db.merge_from(new_db)
            existing_db.save_local(FAISS_DB_PATH)
            return existing_db
        except Exception as e:
            print(f"Failed to load existing index, overwriting: {e}")
            new_db.save_local(FAISS_DB_PATH)
            return new_db
    else:
        new_db.save_local(FAISS_DB_PATH)
        return new_db


def retrieve_docs(query: str, file_names: list[str]) -> list[Document]:
    """
    Retrieve documents relevant to the query from the vector database,
    filtered by the specific file names.

    Args:
        query (str): The search query.
        file_names (list[str]): The source file names to filter results by.

    Returns:
        list[Document]: A list of retrieved Document objects.
    """
    embedding_model = get_embedding_model()
    
    if not os.path.exists(FAISS_DB_PATH) or not os.listdir(FAISS_DB_PATH):
        return []
        
    faiss_db = FAISS.load_local(FAISS_DB_PATH, embedding_model, allow_dangerous_deserialization=True)
    
    # Retrieve top 10 similar documents for better context coverage
    retrieved_docs = faiss_db.similarity_search(query, k=10)
    
    # Filter by source files
    filtered_docs = [doc for doc in retrieved_docs if doc.metadata.get("source") in file_names]

    return filtered_docs
