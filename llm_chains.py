import os
import yaml
import requests
from prompt_templates import SYSTEM_PROMPT, MEMORY_PROMPT_TEMPLATE

with open('config.yaml') as f:
    config = yaml.safe_load(f)


class ConversationMemory:
    def __init__(self, max_turns=6):
        self.max_turns = max_turns
        self.messages = []

    def add_user_message(self, text):
        self.messages.append({"role": "user", "content": text})
        self._trim()

    def add_ai_message(self, text):
        self.messages.append({"role": "assistant", "content": text})
        self._trim()

    def get_history(self):
        return self.messages[-self.max_turns:]

    def _trim(self):
        if len(self.messages) > self.max_turns:
            self.messages = self.messages[-self.max_turns:]

    def clear(self):
        self.messages = []

    def format_for_prompt(self):
        lines = []
        for msg in self.messages:
            role = "Human" if msg["role"] == "user" else "Assistant"
            lines.append(f"{role}: {msg['content']}")
        return "\n".join(lines)


def _build_prompt(prompt, memory):
    history = memory.format_for_prompt() if memory else ""
    return MEMORY_PROMPT_TEMPLATE.format(
        system_prompt=SYSTEM_PROMPT,
        memory=history,
        human_input=prompt,
    )


class OllamaProvider:
    def __init__(self, model_cfg):
        self.model = model_cfg["model"]
        self.base_url = model_cfg["base_url"].rstrip("/")
        self.temperature = model_cfg["temperature"]
        self.max_tokens = model_cfg["max_tokens"]

    def generate(self, prompt, memory=None):
        full_prompt = _build_prompt(prompt, memory)
        try:
            resp = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": full_prompt,
                    "options": {
                        "temperature": self.temperature,
                        "num_predict": self.max_tokens,
                    },
                    "stream": False,
                },
                timeout=120,
            )
            resp.raise_for_status()
            return resp.json()["response"]
        except requests.exceptions.ConnectionError:
            return "Error: Cannot connect to Ollama. Is it running? (ollama serve)"
        except Exception as e:
            return f"Error: {e}"


class OpenAIProvider:
    def __init__(self, model_cfg):
        self.model = model_cfg["model"]
        self.temperature = model_cfg["temperature"]
        self.max_tokens = model_cfg["max_tokens"]
        self.api_key = model_cfg.get("api_key") or os.environ.get("OPENAI_API_KEY", "")

    def generate(self, prompt, memory=None):
        try:
            from openai import OpenAI
        except ImportError:
            return "Error: openai package not installed. Run: pip install openai"

        client = OpenAI(api_key=self.api_key)
        full_prompt = _build_prompt(prompt, memory)
        messages = [{"role": "user", "content": full_prompt}]

        try:
            resp = client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            return resp.choices[0].message.content
        except Exception as e:
            return f"Error: {e}"


class AnthropicProvider:
    def __init__(self, model_cfg):
        self.model = model_cfg["model"]
        self.temperature = model_cfg["temperature"]
        self.max_tokens = model_cfg["max_tokens"]
        self.api_key = model_cfg.get("api_key") or os.environ.get("ANTHROPIC_API_KEY", "")

    def generate(self, prompt, memory=None):
        try:
            import anthropic
        except ImportError:
            return "Error: anthropic package not installed. Run: pip install anthropic"

        client = anthropic.Anthropic(api_key=self.api_key)
        full_prompt = _build_prompt(prompt, memory)
        messages = [{"role": "user", "content": full_prompt}]

        try:
            resp = client.messages.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            return resp.content[0].text
        except Exception as e:
            return f"Error: {e}"


class LocalProvider:
    def __init__(self, model_cfg):
        self.model_path = model_cfg["model_path"]
        self.model_type = model_cfg["model_type"]
        self.temperature = model_cfg["temperature"]
        self.max_tokens = model_cfg["max_tokens"]
        self.gpu_layers = model_cfg.get("gpu_layers", 0)

    def generate(self, prompt, memory=None):
        try:
            from ctransformers import LLM
        except ImportError:
            return "Error: ctransformers not installed. Run: pip install ctransformers"

        try:
            llm = LLM(
                model_path=self.model_path,
                model_type=self.model_type,
                config={
                    "max_new_tokens": self.max_tokens,
                    "temperature": self.temperature,
                    "gpu_layers": self.gpu_layers,
                },
            )
            full_prompt = _build_prompt(prompt, memory)
            return llm(full_prompt)
        except Exception as e:
            return f"Error: {e}"


class LLMChain:
    def __init__(self):
        self.memory = ConversationMemory()
        self.provider = self._create_provider()

    def _create_provider(self):
        llm_cfg = config["llm"]
        provider_name = llm_cfg["provider"]
        providers = {
            "ollama": OllamaProvider,
            "openai": OpenAIProvider,
            "anthropic": AnthropicProvider,
            "local": LocalProvider,
        }
        provider_cls = providers.get(provider_name)
        if not provider_cls:
            raise ValueError(f"Unknown provider: {provider_name}. Supported: {list(providers.keys())}")
        return provider_cls(llm_cfg[provider_name])

    def run(self, user_input):
        self.memory.add_user_message(user_input)
        response = self.provider.generate(user_input, self.memory)
        self.memory.add_ai_message(response)
        return response

    def get_memory(self):
        return self.memory


def create_llm_chain():
    return LLMChain()
