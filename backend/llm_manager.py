"""
Centralized LLM Manager
Single unified interface for all AI model interactions
"""

import yaml
from typing import Dict, List, Optional, Any
from openai import OpenAI
from anthropic import Anthropic
import google.generativeai as genai
import os
from enum import Enum

class TaskType(str, Enum):
    VISION = "vision"
    REASONING = "reasoning"
    FAST = "fast"
    DEFAULT = "default"

class LLMManager:
    def __init__(self, config_path: str = "backend/config.yaml"):
        """Initialize LLM manager with configuration"""
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.llm_config = self.config['llm']
        self.models = self.llm_config['models']
        
        # Initialize API clients
        self._init_clients()
    
    def _init_clients(self):
        """Initialize all LLM provider clients"""
        self.clients = {}
        
        # OpenAI
        openai_key = os.getenv('OPENAI_API_KEY')
        if openai_key:
            self.clients['openai'] = OpenAI(api_key=openai_key)
        
        # Anthropic
        anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        if anthropic_key:
            self.clients['anthropic'] = Anthropic(api_key=anthropic_key)
        
        # Google Gemini
        google_key = os.getenv('GOOGLE_API_KEY')
        if google_key:
            genai.configure(api_key=google_key)
            self.clients['google'] = genai
    
    def get_best_model(self, task_type: TaskType = TaskType.DEFAULT) -> str:
        """
        Automatically select the best model based on task type
        
        Args:
            task_type: Type of task (vision, reasoning, fast, default)
        
        Returns:
            Model ID to use
        """
        routing = self.llm_config['task_routing']
        
        # Map task type to routing config
        task_map = {
            TaskType.VISION: 'vision_tasks',
            TaskType.REASONING: 'complex_reasoning',
            TaskType.FAST: 'fast_tasks',
            TaskType.DEFAULT: 'default'
        }
        
        route_key = task_map.get(task_type, 'default')
        preferred_models = routing[route_key]['preferred']
        
        # Return first enabled preferred model
        for model_id in preferred_models:
            if self.models.get(model_id, {}).get('enabled', False):
                provider = self.models[model_id]['provider']
                if provider in self.clients:
                    return model_id
        
        # Fallback to default
        default_model = self.llm_config['default_model']
        if self.models.get(default_model, {}).get('enabled', False):
            return default_model
        
        raise ValueError("No enabled models available")
    
    def complete(
        self,
        prompt: str,
        model_id: Optional[str] = None,
        task_type: TaskType = TaskType.DEFAULT,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Unified completion method across all providers
        
        Args:
            prompt: The input prompt
            model_id: Specific model to use (or auto-select based on task_type)
            task_type: Type of task for auto-selection
            temperature: Override default temperature
            max_tokens: Override default max tokens
        
        Returns:
            Model response text
        """
        # Auto-select model if not specified
        if model_id is None:
            model_id = self.get_best_model(task_type)
        
        model_config = self.models[model_id]
        provider = model_config['provider']
        
        # Use config defaults if not specified
        final_temperature = temperature if temperature is not None else model_config.get('temperature', 0.7)
        final_max_tokens = max_tokens if max_tokens is not None else model_config.get('max_tokens', 4096)
        
        # Route to appropriate provider
        if provider == 'openai':
            return self._complete_openai(model_config, prompt, final_temperature, final_max_tokens, **kwargs)
        elif provider == 'anthropic':
            return self._complete_anthropic(model_config, prompt, final_temperature, final_max_tokens, **kwargs)
        elif provider == 'google':
            return self._complete_google(model_config, prompt, final_temperature, final_max_tokens, **kwargs)
        else:
            raise ValueError(f"Unknown provider: {provider}")
    
    def _complete_openai(self, model_config: Dict, prompt: str, temperature: float, max_tokens: int, **kwargs) -> str:
        """OpenAI completion"""
        client = self.clients['openai']
        response = client.chat.completions.create(
            model=model_config['model_name'],
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content
    
    def _complete_anthropic(self, model_config: Dict, prompt: str, temperature: float, max_tokens: int, **kwargs) -> str:
        """Anthropic completion"""
        client = self.clients['anthropic']
        response = client.messages.create(
            model=model_config['model_name'],
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.content[0].text
    
    def _complete_google(self, model_config: Dict, prompt: str, temperature: float, max_tokens: int, **kwargs) -> str:
        """Google Gemini completion"""
        model = self.clients['google'].GenerativeModel(model_config['model_name'])
        response = model.generate_content(
            prompt,
            generation_config={
                'temperature': temperature,
                'max_output_tokens': max_tokens
            }
        )
        return response.text
    
    def complete_with_vision(
        self,
        prompt: str,
        image_path: str,
        model_id: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Complete with vision capabilities
        
        Args:
            prompt: Text prompt
            image_path: Path to image file
            model_id: Specific model (auto-selects vision model if None)
        """
        if model_id is None:
            model_id = self.get_best_model(TaskType.VISION)
        
        model_config = self.models[model_id]
        provider = model_config['provider']
        
        if 'vision' not in model_config['capabilities']:
            raise ValueError(f"Model {model_id} does not support vision")
        
        # Vision-specific implementations would go here
        # For now, returning a placeholder
        return self.complete(prompt, model_id=model_id, **kwargs)
    
    def get_model_info(self, model_id: str) -> Dict[str, Any]:
        """Get information about a specific model"""
        return self.models.get(model_id, {})
    
    def list_models(self, enabled_only: bool = True) -> List[Dict[str, Any]]:
        """List all available models"""
        models = []
        for model_id, config in self.models.items():
            if enabled_only and not config.get('enabled', False):
                continue
            models.append({
                'id': model_id,
                **config
            })
        return models

# Global instance
llm_manager = LLMManager()
