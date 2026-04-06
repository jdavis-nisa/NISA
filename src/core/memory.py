import chromadb
from chromadb.config import Settings
import uuid
from datetime import datetime
from typing import Optional

# ChromaDB v2 client
client = chromadb.HttpClient(host="localhost", port=8000)

def get_or_create_collection(name: str = "nisa_memory"):
    """Get or create the NISA memory collection"""
    try:
        collection = client.get_collection(name)
    except Exception:
        collection = client.create_collection(
            name=name,
            metadata={"description": "NISA conversation memory"}
        )
    return collection

def store_exchange(
    user_message: str,
    nisaba_response: str,
    model_used: str,
    routing_reason: str,
    session_id: Optional[str] = None
) -> str:
    """Store a conversation exchange in ChromaDB"""
    collection = get_or_create_collection()
    
    exchange_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat()
    session_id = session_id or "default"
    
    # Store the combined exchange as a document
    document = f"User: {user_message}\nNisaba: {nisaba_response}"
    
    collection.add(
        documents=[document],
        metadatas=[{
            "user_message": user_message[:500],
            "nisaba_response": nisaba_response[:500],
            "model_used": model_used,
            "routing_reason": routing_reason,
            "session_id": session_id,
            "timestamp": timestamp
        }],
        ids=[exchange_id]
    )
    return exchange_id

def recall_relevant(query: str, n_results: int = 3) -> list:
    """Recall relevant past exchanges for a given query"""
    collection = get_or_create_collection()
    
    try:
        count = collection.count()
        if count == 0:
            return []
        
        n = min(n_results, count)
        results = collection.query(
            query_texts=[query],
            n_results=n
        )
        
        memories = []
        if results and results["metadatas"]:
            for i, meta in enumerate(results["metadatas"][0]):
                memories.append({
                    "user_message": meta.get("user_message", ""),
                    "nisaba_response": meta.get("nisaba_response", ""),
                    "timestamp": meta.get("timestamp", ""),
                    "model_used": meta.get("model_used", ""),
                    "distance": results["distances"][0][i] if results.get("distances") else None
                })
        return memories
    except Exception as e:
        print(f"[Memory] Recall error: {e}")
        return []

def get_session_history(session_id: str, limit: int = 10) -> list:
    """Get recent exchanges from a specific session"""
    collection = get_or_create_collection()
    
    try:
        results = collection.get(
            where={"session_id": session_id},
            limit=limit
        )
        return results.get("metadatas", [])
    except Exception as e:
        print(f"[Memory] Session history error: {e}")
        return []

def format_memory_context(memories: list) -> str:
    """Format recalled memories as context for Nisaba"""
    if not memories:
        return ""
    
    context = "\n[Relevant conversation history:]\n"
    for m in memories:
        ts = m.get("timestamp", "")[:10]
        user = m.get("user_message", "")[:100]
        nisaba = m.get("nisaba_response", "")[:100]
        context += f"- [{ts}] You asked: {user}\n"
        context += f"  Nisaba said: {nisaba}\n"
    return context

def get_memory_stats() -> dict:
    """Get memory collection statistics"""
    collection = get_or_create_collection()
    return {
        "total_exchanges": collection.count(),
        "collection_name": collection.name
    }

if __name__ == "__main__":
    print("Testing NISA memory module...")
    
    # Store a test exchange
    eid = store_exchange(
        user_message="What is a prompt injection attack?",
        nisaba_response="A prompt injection attack manipulates AI input to cause unintended behavior.",
        model_used="redsage-qwen3-8b-dpo",
        routing_reason="security",
        session_id="test_session"
    )
    print(f"Stored exchange: {eid}")
    
    # Store another
    eid2 = store_exchange(
        user_message="How do I defend against prompt injection?",
        nisaba_response="Use input validation, output filtering, and least privilege principles.",
        model_used="redsage-qwen3-8b-dpo",
        routing_reason="security",
        session_id="test_session"
    )
    print(f"Stored exchange: {eid2}")
    
    # Recall relevant memories
    memories = recall_relevant("security vulnerabilities and attacks")
    print(f"\nRecalled {len(memories)} relevant memories:")
    for m in memories:
        print(f"  - {m['user_message'][:60]}")
    
    # Get stats
    stats = get_memory_stats()
    print(f"\nMemory stats: {stats}")
    print("Memory module operational.")
