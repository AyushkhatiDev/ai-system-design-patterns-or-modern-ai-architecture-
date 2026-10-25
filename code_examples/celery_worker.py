import os
import time
import logging
from celery import Celery

# Configure Celery to use our Redis container as both the message broker and result backend
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
celery_app = Celery("ai_tasks", broker=redis_url, backend=redis_url)

logging.basicConfig(level=logging.INFO)

@celery_app.task(bind=True, name="generate_llm_response")
def generate_llm_response(self, user_query: str) -> str:
    """
    This function runs completely in the background. 
    It simulates a long-running LLM generation process.
    """
    logging.info(f"Worker received task: {self.request.id} for query: {user_query}")
    
    # Simulate a slow LLM API taking 10 seconds to generate tokens
    time.sleep(10) 
    
    response = f"Background processed response for: '{user_query}'"
    logging.info(f"Worker completed task: {self.request.id}")
    
    return response