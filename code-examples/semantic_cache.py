import json
import numpy as np
from fastapi import FastAPI
from sentence_transformers import SentenceTransformer
import redis.asyncio as redis

app = FastAPI()

# 1. Load a tiny, fast local model for embeddings (runs on CPU)
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# 2. Connect to Redis (acting as our vector cache)
redis_client = redis.Redis(host="localhost", port=6379, decode_responses=True)

SIMILARITY_THRESHOLD = 0.95 

def cosine_similarity(vec_a, vec_b):
    return np.dot(vec_a, vec_b) / (np.linalg.norm(vec_a) * np.linalg.norm(vec_b))

@app.post("/api/chat")
async def chat_endpoint(user_query: str):
    # Step 1: Generate embedding for the incoming query instantly
    query_vector = embedding_model.encode(user_query)
    
    # Step 2: Fetch all cached queries (In production, use Redis RediSearch/Vector module)
    cached_keys = await redis_client.keys("cache:*")
    
    for key in cached_keys:
        cached_data = await redis_client.get(key)
        cache_entry = json.loads(cached_data)
        cached_vector = np.array(cache_entry["vector"])
        
        # Step 3: Check for semantic similarity
        similarity = cosine_similarity(query_vector, cached_vector)
        
        if similarity >= SIMILARITY_THRESHOLD:
            # CACHE HIT: Return the answer instantly, zero LLM cost
            return {
                "response": cache_entry["llm_response"],
                "cache_hit": True,
                "similarity_score": round(float(similarity), 3)
            }
            
    # CACHE MISS: Forward to the expensive LLM
    # llm_response = call_openai_api(user_query) ... (Mocked below)
    llm_response = "This is a freshly generated response from the LLM."
    
    # Step 4: Store the new query and response in the cache with a 24-hour TTL
    new_cache_entry = {
        "vector": query_vector.tolist(),
        "llm_response": llm_response
    }
    await redis_client.setex(
        f"cache:{hash(user_query)}", 
        86400, # 24-hour TTL prevents stale data
        json.dumps(new_cache_entry)
    )
    
    return {
        "response": llm_response,
        "cache_hit": False
    }