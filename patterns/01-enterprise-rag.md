# Blueprint: Enterprise RAG (Retrieval-Augmented Generation)

Enterprise RAG allows companies to securely connect open-source or proprietary LLMs to their internal databases without leaking sensitive information.

## 🏗️ Architecture Diagram

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant Client as Next.js (Frontend)
    participant API as FastAPI (Orchestrator)
    participant Auth as Auth0 / IAM
    participant VectorDB as Pinecone / Milvus
    participant DB as Postgres (Metadata & ACL)
    participant LLM as Llama 3 / OpenAI

    User->>Client: Submit query (e.g., "Summarize Q3 financials")
    Client->>API: POST /api/chat {query, token}
    API->>Auth: Validate JWT
    Auth-->>API: User ID & Roles
    API->>API: Embed User Query (Text to Vector)
    API->>VectorDB: Semantic Search (Top K)
    VectorDB-->>API: Return Context Chunks + Doc IDs
    API->>DB: Check Row-Level Access for Doc IDs
    DB-->>API: Filtered Doc IDs (Authorized Only)
    API->>LLM: Prompt + Authorized Context Chunks
    LLM-->>API: Stream Response Tokens
    API-->>Client: Server-Sent Events (SSE) Stream
    Client-->>User: Render Streamed UI