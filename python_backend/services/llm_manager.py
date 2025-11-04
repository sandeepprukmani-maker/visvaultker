import os
import yaml
from typing import Dict, List, Optional, Any
from openai import OpenAI
from anthropic import Anthropic
import google.generativeai as genai

class LLMManager:
    def __init__(self, config_path: str = "config.yaml"):
        import os
        if not os.path.exists(config_path):
            config_path = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.openai_client = None
        self.anthropic_client = None
        self.gemini_configured = False
        
        self._initialize_clients()
        self.usage_stats = []
    
    def _initialize_clients(self):
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            self.openai_client = OpenAI(api_key=openai_key)
        
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key:
            self.anthropic_client = Anthropic(api_key=anthropic_key)
        
        gemini_key = os.getenv("GOOGLE_AI_API_KEY")
        if gemini_key:
            genai.configure(api_key=gemini_key)
            self.gemini_configured = True
    
    def select_model(self, task_type: str = "reasoning", with_vision: bool = False) -> Optional[Dict[str, str]]:
        if with_vision or task_type == "vision":
            models = self.config["task_routing"]["vision_tasks"]
        elif task_type == "reasoning":
            models = self.config["task_routing"]["reasoning_tasks"]
        elif task_type == "speed":
            models = self.config["task_routing"]["speed_tasks"]
        elif task_type == "complex":
            models = self.config["task_routing"]["complex_tasks"]
        else:
            models = self.config["task_routing"]["reasoning_tasks"]
        
        for model_name in models:
            provider, model_info = self._get_model_info(model_name)
            if provider and self._is_provider_available(provider):
                return {"provider": provider, "model": model_name, "config": model_info}
        
        return None
    
    def _get_model_info(self, model_name: str) -> tuple[Optional[str], Optional[Dict]]:
        for provider, data in self.config["llm_providers"].items():
            for key, model_info in data["models"].items():
                if key == model_name or model_info["name"] == model_name:
                    return provider, model_info
        return None, None
    
    def _is_provider_available(self, provider: str) -> bool:
        if provider == "openai":
            return self.openai_client is not None
        elif provider == "anthropic":
            return self.anthropic_client is not None
        elif provider == "google":
            return self.gemini_configured
        return False
    
    async def complete(
        self,
        prompt: str,
        task_type: str = "reasoning",
        with_vision: bool = False,
        images: Optional[List[str]] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        model_config = self.select_model(task_type, with_vision)
        if not model_config:
            return {
                "content": "LLM providers not configured. Please set API keys for OpenAI, Anthropic, or Google AI.",
                "usage": {"provider": "none", "model": "none", "prompt_tokens": 0, "completion_tokens": 0, "total_cost": 0},
                "model": "none",
                "error": "no_providers_configured"
            }
        
        provider = model_config["provider"]
        model_info = model_config["config"]
        
        try:
            if provider == "openai":
                return await self._complete_openai(prompt, model_info, images, max_tokens, temperature)
            elif provider == "anthropic":
                return await self._complete_anthropic(prompt, model_info, images, max_tokens, temperature)
            elif provider == "google":
                return await self._complete_gemini(prompt, model_info, images, max_tokens, temperature)
        except Exception as e:
            fallback_models = self._get_fallback_models(provider, task_type, with_vision)
            for fallback in fallback_models:
                try:
                    model_config = {"provider": fallback["provider"], "config": fallback["config"]}
                    if fallback["provider"] == "openai":
                        return await self._complete_openai(prompt, fallback["config"], images, max_tokens, temperature)
                    elif fallback["provider"] == "anthropic":
                        return await self._complete_anthropic(prompt, fallback["config"], images, max_tokens, temperature)
                    elif fallback["provider"] == "google":
                        return await self._complete_gemini(prompt, fallback["config"], images, max_tokens, temperature)
                except:
                    continue
            raise Exception(f"All LLM providers failed: {str(e)}")
    
    async def _complete_openai(
        self,
        prompt: str,
        model_info: Dict,
        images: Optional[List[str]],
        max_tokens: Optional[int],
        temperature: float
    ) -> Dict[str, Any]:
        if not self.openai_client:
            raise Exception("OpenAI client not initialized")
        
        messages = [{"role": "user", "content": prompt}]
        
        if images:
            content = [{"type": "text", "text": prompt}]
            for img in images:
                content.append({"type": "image_url", "image_url": {"url": img}})
            messages = [{"role": "user", "content": content}]
        
        response = self.openai_client.chat.completions.create(
            model=model_info["name"],
            messages=messages,
            max_tokens=max_tokens or model_info["max_tokens"],
            temperature=temperature
        )
        
        usage = {
            "provider": "openai",
            "model": model_info["name"],
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_cost": self._calculate_cost(
                "openai",
                model_info,
                response.usage.prompt_tokens,
                response.usage.completion_tokens
            )
        }
        self.usage_stats.append(usage)
        
        return {
            "content": response.choices[0].message.content,
            "usage": usage,
            "model": model_info["name"]
        }
    
    async def _complete_anthropic(
        self,
        prompt: str,
        model_info: Dict,
        images: Optional[List[str]],
        max_tokens: Optional[int],
        temperature: float
    ) -> Dict[str, Any]:
        if not self.anthropic_client:
            raise Exception("Anthropic client not initialized")
        
        content = [{"type": "text", "text": prompt}]
        
        if images:
            for img in images:
                content.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": img
                    }
                })
        
        response = self.anthropic_client.messages.create(
            model=model_info["name"],
            max_tokens=max_tokens or model_info["max_tokens"],
            temperature=temperature,
            messages=[{"role": "user", "content": content}]
        )
        
        usage = {
            "provider": "anthropic",
            "model": model_info["name"],
            "prompt_tokens": response.usage.input_tokens,
            "completion_tokens": response.usage.output_tokens,
            "total_cost": self._calculate_cost(
                "anthropic",
                model_info,
                response.usage.input_tokens,
                response.usage.output_tokens
            )
        }
        self.usage_stats.append(usage)
        
        return {
            "content": response.content[0].text,
            "usage": usage,
            "model": model_info["name"]
        }
    
    async def _complete_gemini(
        self,
        prompt: str,
        model_info: Dict,
        images: Optional[List[str]],
        max_tokens: Optional[int],
        temperature: float
    ) -> Dict[str, Any]:
        if not self.gemini_configured:
            raise Exception("Gemini not configured")
        
        model = genai.GenerativeModel(model_info["name"])
        
        content = [prompt]
        if images:
            content.extend(images)
        
        response = model.generate_content(
            content,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=max_tokens or model_info["max_tokens"],
                temperature=temperature
            )
        )
        
        prompt_tokens = response.usage_metadata.prompt_token_count if hasattr(response, 'usage_metadata') else 0
        completion_tokens = response.usage_metadata.candidates_token_count if hasattr(response, 'usage_metadata') else 0
        
        usage = {
            "provider": "google",
            "model": model_info["name"],
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_cost": self._calculate_cost(
                "google",
                model_info,
                prompt_tokens,
                completion_tokens
            )
        }
        self.usage_stats.append(usage)
        
        return {
            "content": response.text,
            "usage": usage,
            "model": model_info["name"]
        }
    
    def _calculate_cost(self, provider: str, model_info: Dict, prompt_tokens: int, completion_tokens: int) -> float:
        input_cost = (prompt_tokens / 1000) * model_info["cost_per_1k_input"]
        output_cost = (completion_tokens / 1000) * model_info["cost_per_1k_output"]
        return input_cost + output_cost
    
    def _get_fallback_models(self, failed_provider: str, task_type: str, with_vision: bool) -> List[Dict]:
        fallbacks = []
        if with_vision or task_type == "vision":
            models = self.config["task_routing"]["vision_tasks"]
        else:
            models = self.config["task_routing"]["reasoning_tasks"]
        
        for model_name in models:
            provider, model_info = self._get_model_info(model_name)
            if provider and provider != failed_provider and self._is_provider_available(provider):
                fallbacks.append({"provider": provider, "config": model_info})
        
        return fallbacks
    
    def get_usage_stats(self) -> List[Dict]:
        return self.usage_stats
    
    def get_total_cost(self) -> float:
        return sum(stat["total_cost"] for stat in self.usage_stats)
