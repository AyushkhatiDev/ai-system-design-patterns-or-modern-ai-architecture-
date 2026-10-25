import random
from locust import HttpUser, task, between

# A list of similar questions to trigger the Semantic Cache
PROMPTS = [
    "How do I reset my password?",
    "Forgot my password, how to reset?",
    "What is the process to change my password?",
    "Tell me a joke.", # Cache miss generator
    "Write a python script for a binary tree." # Cache miss generator
]

class AIGatewayUser(HttpUser):
    # Simulate a realistic wait time between user requests (1 to 3 seconds)
    wait_time = between(1, 3)

    @task
    def test_chat_endpoint(self):
        # Randomly select a prompt to simulate real-world user variance
        query = random.choice(PROMPTS)
        
        # Hit the FastAPI endpoint we built in the code-examples folder
        self.client.post(
            f"/api/chat?user_query={query}",
            name="/api/chat (Semantic Routing)"
        )