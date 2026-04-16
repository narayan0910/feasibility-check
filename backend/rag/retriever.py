import logging

logger = logging.getLogger(__name__)

def retrieve_context(conversation_id: str, query: str, top_k: int = 5) -> tuple[str, list]:
    """
    Retrieves the top-k most relevant chunks for the given query 
    filtered by conversation_id.
    """
    try:
        from qdrant_client import QdrantClient
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        from rag.embedder import embedder, qdrant_client, _init_qdrant, COLLECTION_NAME
        
        _init_qdrant()
        
        query_vector = embedder.encode(query).tolist()
        
        search_result = qdrant_client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_vector,
            query_filter=Filter(
                must=[
                    FieldCondition(
                        key="conversation_id",
                        match=MatchValue(value=conversation_id)
                    )
                ]
            ),
            limit=top_k
        )
        
        if not search_result:
            print(f"  [RAG] 🔍 Retrieved 0 matching chunks for query: '{query}'")
            return "No relevant context found.", []
            
        print(f"\n  [RAG] 🔍 Retrieved top {len(search_result)} chunks for QA:")
        context_texts = []
        chunks_list = []
        for i, hit in enumerate(search_result):
            source = hit.payload.get("source", "unknown")
            text = hit.payload.get("text", "")
            
            print(f"    Hit {i+1} | Score: {hit.score:.4f} | Source: {source}")
            preview = (text or "").replace(chr(10), " ").strip()
            print(f"    Retrieved Text: {preview[:350]}{'...' if len(preview) > 350 else ''}\n")
            
            
            chunks_list.append({
                "source": source,
                "text": text,
                "score": hit.score
            })
            context_texts.append(f"[{source}] {text}")
            
        return "\n\n".join(context_texts), chunks_list
        
    except ImportError as e:
        logger.error(f"Failed to retrieve context (Imports missing): {e}")
        return "RAG is not available because dependencies are missing.", []
    except Exception as e:
        logger.error(f"Error retrieving context for RAG: {e}")
        return "Error retrieving context.", []
