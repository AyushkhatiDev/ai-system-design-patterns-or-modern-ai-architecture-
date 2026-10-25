import json
import pytest
from code_examples.prompt_manager import PromptManager


# Simulated LLM response for CI/CD testing
def mock_llm_call(system_message: str, user_input: str) -> str:
    """Mocks an LLM returning structured JSON."""
    return '{"category": "billing", "confidence": 0.95}'


def test_prompt_schema_compliance():
    """Evaluates if the LLM output strictly matches the required schema."""
    manager = PromptManager()
    router_config = manager.get_prompt("customer_support_router")

    # Execute the mock LLM call
    ai_response = mock_llm_call(
        system_message=router_config["system_message"], user_input="Why was I charged twice this month?"
    )

    # Evaluation 1: Is it valid JSON?
    try:
        parsed_response = json.loads(ai_response)
    except json.JSONDecodeError:
        pytest.fail("LLM Evaluation Failed: Output is not valid JSON.")

    # Evaluation 2: Did it return the exact keys we expect?
    assert "category" in parsed_response, "LLM missed required key: 'category'"
    assert "confidence" in parsed_response, "LLM missed required key: 'confidence'"

    # Evaluation 3: Is the routing hallucinated?
    valid_categories = ["billing", "technical_support", "refunds", "general"]
    assert parsed_response["category"] in valid_categories, f"LLM hallucinated category: {parsed_response['category']}"
