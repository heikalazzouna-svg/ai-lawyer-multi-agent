import os
from sqlalchemy.orm import Session
from api.models.document import DocumentChunk
from api.models.user import DocumentMetadata
from langchain_huggingface import HuggingFaceEmbeddings
from sqlalchemy import select, or_, text
from typing import List

def get_embedding_model() -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

def index_document_chunks(db: Session, document_id: int, chunks: List[str]):
    """
    Index document chunks into Postgres using pgvector.
    """
    embedding_model = get_embedding_model()
    embeddings = embedding_model.embed_documents(chunks)
    
    db_chunks = []
    for chunk, emb in zip(chunks, embeddings):
        db_chunk = DocumentChunk(
            document_id=document_id,
            content=chunk,
            embedding=emb
        )
        db_chunks.append(db_chunk)
        
    db.bulk_save_objects(db_chunks)
    db.commit()

def hybrid_search(db: Session, query: str, document_id: int = None, limit: int = 5) -> List[DocumentChunk]:
    """
    Perform a hybrid search (Dense Vector + Sparse Keyword BM25 fallback) using pgvector.
    In a true pgvector implementation, we would use the `<->` operator for L2 distance.
    """
    embedding_model = get_embedding_model()
    query_embedding = embedding_model.embed_query(query)
    
    # Base query for vector similarity (L2 distance)
    # The order_by uses pgvector's L2 distance operator `<->`
    stmt = select(DocumentChunk).order_by(DocumentChunk.embedding.l2_distance(query_embedding))
    
    if document_id:
        stmt = stmt.filter(DocumentChunk.document_id == document_id)
        
    stmt = stmt.limit(limit)
    
    results = db.execute(stmt).scalars().all()
    
    # If vector search returns few results, we could fallback/augment with a full-text search
    if len(results) < limit:
        # Full text search fallback (using PostgreSQL's native tsvector)
        fts_stmt = select(DocumentChunk).filter(
            text("to_tsvector('english', content) @@ plainto_tsquery('english', :query)")
        ).params(query=query)
        
        if document_id:
            fts_stmt = fts_stmt.filter(DocumentChunk.document_id == document_id)
            
        fts_stmt = fts_stmt.limit(limit - len(results))
        fts_results = db.execute(fts_stmt).scalars().all()
        
        # Combine and deduplicate
        existing_ids = {r.id for r in results}
        for fts_r in fts_results:
            if fts_r.id not in existing_ids:
                results.append(fts_r)
                
    return results
