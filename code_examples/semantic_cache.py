import json
import logging
import os
from typing import Dict, Any
import numpy as np
from fastapi import FastAPI
from sentence_transformers import SentenceTransformer
import redis.asyncio as redis
from redis.exceptions import RedisError

# --- OpenTelemetry Imports ---
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

app = FastAPI()
logging.basicConfig(level=logging.INFO)

# --- Tracing Configuration ---
resource = Resource(attributes={"service.name": "semantic-cache-gateway"})
provider = TracerProvider(resource=resource)
# Send traces to Jaeger (uses environment variable for host, defaults to localhost)
otlp_endpoint = os.getenv("OTLP_ENDPOINT", "http://localhost:4317")
processor = BatchSpanProcessor(OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True))
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)

# Automatically trace all FastAPI routes
FastAPIInstrumentor.instrument_app(app)

# --- AI & Cache Initialization ---
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
# Use environment variable for Redis host so Docker can connect properly
redis_host = os.getenv("REDIS_HOST", "localhost")
redis_client = redis.Redis(host=redis_host, port=6379, decode_responses=True)
tracer = trace.get_tracer(__name__)

SIMILARITY_THRESHOLD = 0.95 

def cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    return float(np.dot(vec_a, vec_b) / (np.linalg.norm(vec_a) * np.linalg.norm(vec_b)))

@app.post("/api/chat")
async def chat_endpoint(user_query: str) -> Dict[str, Any]:
    # We can create custom spans to track exactly how long the embedding takes
    with tracer.start_as_current_span("generate_embedding"):
        query_vector = embedding_model.encode(user_query)
    
    with tracer.start_as_current_span("redis_cache_lookup"):
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
                            "similarity_score": round(similarity, 3)
                        }
        except RedisError as e:
            logging.error(f"Redis cache unavailable: {e}. Bypassing cache.")

    with tracer.start_as_current_span("llm_generation"):
        # Simulated LLM call
        llm_response = "This is a freshly generated response from the LLM."
    
    with tracer.start_as_current_span("redis_cache_write"):
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