"""
Kgotla AI Intelligence Swarm — Free Model Router
Routes tasks to the right free AI model based on task complexity and type.
"""

import os
import requests
from enum import Enum
from dataclasses import dataclass


class TaskType(Enum):
    REASONING      = "reasoning"
    LONG_DOCUMENT  = "long_document"
    EXTRACTION     = "extraction"
    ENTERPRISE_RAG = "enterprise_rag"
    SUMMARIZATION  = "summarization"


@dataclass
class ModelResponse:
    model: str
    task_type: str
    content: str
    tokens_used: int = 0
    success: bool = True
    error: str = ""


class FreeModelRouter:
    GROQ_URL   = "https://api.groq.com/openai/v1/chat/completions"
    GOOGLE_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
    HF_URL     = "https://api-inference.huggingface.co/models/{model}"

    ROUTING_RULES = {
        TaskType.REASONING:      ["groq",       "google",     "hf_mistral"],
        TaskType.LONG_DOCUMENT:  ["google",     "groq",       "hf_mistral"],
        TaskType.EXTRACTION:     ["hf_mistral", "groq",       "google"],
        TaskType.ENTERPRISE_RAG: ["hf_granite", "groq",       "google"],
        TaskType.SUMMARIZATION:  ["groq",       "hf_mistral", "google"],
    }

    def __init__(self):
        self.groq_key   = os.environ.get("GROQ_API_KEY", "")
        self.google_key = os.environ.get("GOOGLE_AI_API_KEY", "")
        self.hf_token   = os.environ.get("HF_API_TOKEN", "")

    def route(self, prompt: str, task_type: TaskType, system: str = "", max_tokens: int = 1024) -> ModelResponse:
        priority   = self.ROUTING_RULES.get(task_type, ["groq", "google", "hf_mistral"])
        last_error = ""
        for model_key in priority:
            try:
                if model_key == "groq":
                    return self._call_groq(prompt, system, max_tokens)
                elif model_key == "google":
                    return self._call_google(prompt, system, max_tokens)
                elif model_key == "hf_mistral":
                    return self._call_hf("mistralai/Mistral-7B-Instruct-v0.3", prompt, max_tokens)
                elif model_key == "hf_granite":
                    return self._call_hf("ibm-granite/granite-3.3-8b-instruct", prompt, max_tokens)
            except Exception as e:
                last_error = str(e)
                print(f"[Router] {model_key} failed: {e}. Trying next...")
                continue
        return ModelResponse(model="none", task_type=task_type.value, content="", success=False, error=last_error)

    def _call_groq(self, prompt: str, system: str, max_tokens: int) -> ModelResponse:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        resp = requests.post(
            self.GROQ_URL,
            headers={"Authorization": f"Bearer {self.groq_key}", "Content-Type": "application/json"},
            json={"model": "llama-3.3-70b-versatile", "messages": messages, "max_tokens": max_tokens},
            timeout=30
        )
        resp.raise_for_status()
        data = resp.json()
        return ModelResponse(
            model="groq/llama-3.3-70b", task_type="groq_call",
            content=data["choices"][0]["message"]["content"],
            tokens_used=data.get("usage", {}).get("total_tokens", 0)
        )

    def _call_google(self, prompt: str, system: str, max_tokens: int) -> ModelResponse:
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        resp = requests.post(
            f"{self.GOOGLE_URL}?key={self.google_key}",
            json={"contents": [{"parts": [{"text": full_prompt}]}],
                  "generationConfig": {"maxOutputTokens": max_tokens}},
            timeout=60
        )
        resp.raise_for_status()
        data = resp.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        return ModelResponse(model="google/gemini-1.5-flash", task_type="google_call", content=text)

    def _call_hf(self, model_id: str, prompt: str, max_tokens: int) -> ModelResponse:
        resp = requests.post(
            self.HF_URL.format(model=model_id),
            headers={"Authorization": f"Bearer {self.hf_token}"},
            json={"inputs": prompt, "parameters": {"max_new_tokens": max_tokens}},
            timeout=60
        )
        resp.raise_for_status()
        data = resp.json()
        text = data[0].get("generated_text", "") if isinstance(data, list) else data.get("generated_text", str(data))
        return ModelResponse(model=f"hf/{model_id}", task_type="hf_call", content=text)


router = FreeModelRouter()
