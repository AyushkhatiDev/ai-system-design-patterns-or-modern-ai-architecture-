import json
import logging
import numpy as np
from fastapi import FastAPI
from sentence_transformers import SentenceTransformer
import redis.asyncio as redis
from redis.exceptions import RedisError

app = FastAPI()
logging.basicConfig(level=logging.INFO)

embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
redis_client = redis.Redis(host="localhost", port=6379, decode_responses=True)

SIMILARITY_THRESHOLD = 0.95 

def cosine_similarity(vec_a, vec_b):
    return np.dot(vec_a, vec_b) / (np.linalg.norm(vec_a) * np.linalg.norm(vec_b))

@app.post("/api/chat")
async def chat_endpoint(user_query: str):
    query_vector = embedding_model.encode(user_query)
    
    # GRACEFUL DEGRADATION: If Redis fails, log the error and bypass the cache
    try:
        cached_keys = await redis_client.keys("cache:*")
        for key in cached_keys:
            cached_data = await redis_client.get(key)
            if cached_data:
                cache_entry = json.loads(cached_data)
                cached_vector = np.array(cache_entry["vector"])
                
                similarity = cosine_similarity(query_vector, cached_vector)
                if similarity >= SIMILARITY_THRESHOLD:
                    return {
                        "response": cache_entry["llm_response"],
                        "cache_hit": True,
                        "similarity_score": round(float(similarity), 3)
                    }
    except RedisError as e:
        logging.error(f"Redis cache unavailable: {e}. Bypassing cache.")

    # Fallback to LLM (Simulated)
    llm_response = "This is a freshly generated response from the LLM."
    
    try:
        new_cache_entry = {
            "vector": query_vector.tolist(),
            "llm_response": llm_response
        }
        await redis_client.setex(
            f"cache:{hash(user_query)}", 
            86400, 
            json.dumps(new_cache_entry)
        )
    except RedisError as e:
        logging.error(f"Failed to write to Redis cache: {e}")
    
    return {
        "response": llm_response,
        "cache_hit": False
    }