import yaml
from pathlib import Path
from typing import Any


class PromptManager:
    def __init__(self, config_path: str = "code_examples/prompts.yaml"):
        self.config_path = Path(config_path)
        self._prompts = self._load_config()

    def _load_config(self) -> dict[str, Any]:
        with open(self.config_path, "r") as file:
            return yaml.safe_load(file)

    def get_prompt(self, prompt_name: str) -> dict[str, Any]:
        if prompt_name not in self._prompts["prompts"]:
            raise ValueError(f"Prompt {prompt_name} not found in configuration.")
        return self._prompts["prompts"][prompt_name]


# Usage example:
# manager = PromptManager()
# support_prompt = manager.get_prompt("customer_support_router")
