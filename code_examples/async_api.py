from fastapi import FastAPI
from pydantic import BaseModel
from celery.result import AsyncResult
from code_examples.celery_worker import celery_app

app = FastAPI()


class QueryRequest(BaseModel):
    user_query: str


@app.post("/api/v1/generate")
async def trigger_generation(request: QueryRequest):
    # Instantly push the task to the Redis queue
    task = celery_app.send_task("generate_llm_response", args=[request.user_query])

    # Return a 202 Accepted with the task ID so the client can poll for status
    return {"message": "Task queued successfully", "task_id": task.id, "status_url": f"/api/v1/status/{task.id}"}


@app.get("/api/v1/status/{task_id}")
async def get_task_status(task_id: str):
    # Check Redis to see if the background worker has finished the task
    task_result = AsyncResult(task_id, app=celery_app)

    if task_result.ready():
        return {"task_id": task_id, "status": "COMPLETED", "result": task_result.result}
    return {"task_id": task_id, "status": task_result.state}
