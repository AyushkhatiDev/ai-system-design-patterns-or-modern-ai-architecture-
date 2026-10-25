FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for sentence-transformers
RUN apt-get update && apt-get install -y build-essential

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./code_examples /app/code_examples
CMD ["uvicorn", "code_examples.semantic_cache:app", "--host", "0.0.0.0", "--port", "8000"]