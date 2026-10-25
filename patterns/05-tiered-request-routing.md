# Blueprint: Tiered Request Routing & Fallbacks

At enterprise scale, sending every user query to a heavy frontier model (like GPT-4o or Claude 3.5 Sonnet) wastes millions of dollars and spikes latency. This architecture introduces a lightweight semantic router that categorizes queries by complexity, routing simple tasks to fast, cheap models (or caches) and reserving heavy compute only for tasks requiring deep reasoning.

## 🏗️ Architecture Diagram

```mermaid
flowchart TD
    Client[Client Request] --> API[API Gateway]
    API --> Classifier{Intent & Complexity<br>Classifier (Fast/Local)}
    
    Classifier -->|High Similarity| Cache[(Vector Cache)]
    Cache -->|Cache Hit| Return[Return Instant Response]
    
    Classifier -->|Simple Task<br>(Summarization, Extraction)| Tier1[Tier 1 Model<br>Llama 3 8B / GPT-4o-mini]
    
    Classifier -->|Complex Task<br>(Coding, Deep Reasoning)| Tier2[Tier 2 Model<br>GPT-4o / Claude 3.5 Sonnet]
    
    Tier1 --> Circuit1{Circuit Breaker}
    Tier2 --> Circuit2{Circuit Breaker}
    
    Circuit1 -->|Timeout / 5xx| Fallback[Degraded State<br>Static Response or Queue]
    Circuit2 -->|Rate Limit / 429| Tier1
    
    Tier1 --> Return
    Tier2 --> Return
    Fallback --> Return
```

## 💰 Cost Analysis at Scale
*Assuming 10 million queries per month.*

* **Naïve Approach (100% Tier 2):** 10M queries to GPT-4o = **~$150,000/month**.
* **Tiered Approach (70% Tier 1, 30% Tier 2):** 
  * 7M queries to GPT-4o-mini (or local Llama 3) = ~$1,500/month.
  * 3M queries to GPT-4o = ~$45,000/month.
  * **Total Savings: ~$103,500/month (69% reduction).**

## ⚡ Operational Resilience (The "Unhappy Path")

1. **Cascading Timeouts:**
   * *Failure Mode:* A cloud provider experiences degradation. If your API waits 60 seconds for a response, your connection pool exhausts, taking down the entire backend.
   * *Mitigation:* Implement strict 5-second `p99` timeout thresholds on all Tier 2 calls. If the threshold is breached, the Circuit Breaker opens and instantly routes traffic to the Tier 1 model or a cached fallback, returning a degraded but functional response rather than a 504 Gateway Timeout.
2. **Classifier Overhead:**
   * *Failure Mode:* If the complexity classifier takes 2 seconds to run, you have defeated the purpose of routing to a faster model.
   * *Mitigation:* The classifier must be an ultra-lightweight zero-shot model (like a quantized ONNX model) running locally in memory, executing in under 20ms.

## 🛡️ Security Guardrails

* **Data Sensitivity Routing:** Extend the router to scan for PII (Personally Identifiable Information). If a query contains high-risk data (e.g., SSNs, medical records), the router hard-forces the request to a localized, isolated Tier 1 model inside your VPC, explicitly blocking it from reaching external APIs regardless of task complexity.