import os
import streamlit as st
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from langchain_core.messages import AIMessage
from langchain_core.language_models import BaseChatModel
from groq import RateLimitError, APIError, GroqError

load_dotenv()

def get_llm_model() -> BaseChatModel:
    """
    Initialize and return the language model.
    Validates that the GROQ_API_KEY is present in the environment.

    Returns:
        BaseChatModel: The initialized ChatGroq model.
        
    Raises:
        EnvironmentError: If GROQ_API_KEY is missing.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "GROQ_API_KEY is not set. Please create a .env file with your Groq API key."
        )
        
    # Use the model name from env, default to llama-3.3-70b-versatile
    model_name = os.getenv("GROQ_MODEL_NAME", "llama-3.3-70b-versatile")
    return ChatGroq(model=model_name)

def get_context(documents: list[Document]) -> str:
    """
    Combine document contents into a single context string.

    Args:
        documents (list[Document]): List of retrieved documents.

    Returns:
        str: Combined document text.
    """
    context_blocks = []
    for doc in documents:
        # PDFPlumber loader extracts 'page' metadata as a 0-indexed integer. 
        # We add 1 for user-facing page numbers.
        page_num = doc.metadata.get('page', 0) + 1
        source_file = doc.metadata.get('source', 'Unknown Document')
        
        block = f"--- Source: {source_file}, Page: {page_num} ---\n{doc.page_content}"
        context_blocks.append(block)
        
    return "\n\n".join(context_blocks)

custom_prompt_template = """
You are a highly precise legal assistant. Your job is to answer the user's question using ONLY the provided context.

CRITICAL INSTRUCTIONS:
1. You MUST explicitly cite the source document and page number for EVERY claim you make.
2. Format citations exactly like this: [DocumentName.pdf, Page X].
3. Example: "The tenant is responsible for maintenance [LeaseAgreement.pdf, Page 4]."
4. Do NOT hallucinate. Do NOT use outside knowledge.
5. If the answer is not contained within the provided context, you must reply: "The provided context does not contain the answer to this question."

Previous Conversation:
{history}

User Question: {question} 

Provided Context:
{context}

Answer (with strict citations):
"""

def answer_query(
    documents: list[Document], 
    model: BaseChatModel, 
    query: str, 
    history: str = ""
) -> AIMessage | str:
    """
    Answer a user query based on the provided document context using the LLM.

    Args:
        documents (list[Document]): The context documents retrieved from FAISS.
        model (BaseChatModel): The language model to use.
        query (str): The user's question.
        history (str, optional): The conversation history string. Defaults to "".

    Returns:
        AIMessage | str: The response from the LLM, or an error string if the API fails.
    """
    context = get_context(documents)
    prompt = ChatPromptTemplate.from_template(custom_prompt_template)
    chain = prompt | model
    
    try:
        response = chain.invoke({"question": query, "context": context, "history": history})
        return response
    except RateLimitError:
        return "Error: Rate limit reached. Please wait a moment and try again."
    except APIError as e:
        return f"Error: AI service error: {e.message}"
    except GroqError as e:
        return f"Error: Groq API issue: {str(e)}"
    except Exception as e:
        return f"Error: An unexpected error occurred: {str(e)}"


def summarize_document(documents: list[Document]) -> AIMessage | str:
    """
    Summarize the provided documents using the LLM.

    Args:
        documents (list[Document]): The document chunks to summarize.

    Returns:
        AIMessage | str: The summarized text from the LLM, or an error string.
    """
    context = get_context(documents)
    summary_prompt = """
    Summarize the given legal document concisely while preserving key details.
    Provide a structured summary that highlights the most important points.
    
    Document:
    {context}
    
    Summary:
    """
    prompt = ChatPromptTemplate.from_template(summary_prompt)
    model = get_llm_model()
    chain = prompt | model
    
    try:
        return chain.invoke({"context": context})
    except RateLimitError:
        return "Error: Rate limit reached. Could not summarize."
    except APIError as e:
        return f"Error: AI service error during summarization: {e.message}"
    except GroqError as e:
        return f"Error: Groq API issue: {str(e)}"
    except Exception as e:
        return f"Error: An unexpected error occurred: {str(e)}"

def proactive_scan(documents: list[Document]) -> AIMessage | str:
    """
    Proactively scan the uploaded document for critical legal clauses.

    Args:
        documents (list[Document]): The document chunks to scan.

    Returns:
        AIMessage | str: The extracted legal clauses, or an error string.
    """
    context = get_context(documents)
    scan_prompt = """
    You are an expert legal analyst. Scan the provided document and extract the following key legal information if present:
    1. Governing Law / Jurisdiction
    2. Term and Termination
    3. Limitation of Liability
    4. Key Obligations
    
    If any of these are not found, explicitly state "Not specified in document".
    Be extremely concise. Use bullet points.
    
    Document Context:
    {context}
    
    Proactive Legal Scan:
    """
    prompt = ChatPromptTemplate.from_template(scan_prompt)
    model = get_llm_model()
    chain = prompt | model
    
    try:
        return chain.invoke({"context": context})
    except RateLimitError:
        return "Error: Rate limit reached. Could not complete scan."
    except Exception as e:
        return f"Error: Scan failed: {str(e)}"