import logging
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.security import APIKeyHeader
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pydantic import BaseModel

# Initialize Rate Limiter (limits based on user IP)
limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Require an API Key for all requests
api_key_header = APIKeyHeader(name="X-API-Key")

class ChatRequest(BaseModel):
    user_query: str

def verify_api_key(api_key: str = Depends(api_key_header)):
    # In production, this would check a database or hash vault
    if api_key != "sk-enterprise-test-key":
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return api_key

def check_prompt_injection(query: str):
    """
    A lightweight heuristic check for common prompt injection vectors.
    In a true enterprise setup, this would route to a lightweight classifier model
    (like Llama-Guard) or use Microsoft Presidio for PII masking.
    """
    suspicious_keywords = ["ignore previous instructions", "system prompt", "bypass", "DAN"]
    if any(keyword in query.lower() for keyword in suspicious_keywords):
        logging.warning(f"Blocked potential prompt injection: {query}")
        raise HTTPException(status_code=400, detail="Request blocked by security guardrails.")

@app.post("/api/v1/secure-chat")
@limiter.limit("5/minute") # Strict rate limit: 5 requests per minute per IP
async def secure_chat_endpoint(
    request: Request, 
    payload: ChatRequest, 
    api_key: str = Depends(verify_api_key)
):
    # Step 1: Guardrail Check
    check_prompt_injection(payload.user_query)
    
    # Step 2: Proceed to standard architecture (Cache -> LLM)
    return {
        "status": "success",
        "message": "Query passed security checks and rate limits.",
        "query": payload.user_query
    }