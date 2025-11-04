"""
OpenAI API Adapter for Langchain Chat Models
Provides OpenAI-compatible interface for all langchain chat models
"""
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """OpenAI-style message"""
    role: str
    content: str


@dataclass
class Choice:
    """OpenAI-style choice"""
    index: int
    message: Message
    finish_reason: str


@dataclass
class CompletionResponse:
    """OpenAI-style completion response"""
    id: str
    object: str
    created: int
    model: str
    choices: List[Choice]


class ChatCompletions:
    """OpenAI-compatible chat completions interface"""
    
    def __init__(self, langchain_model):
        self.langchain_model = langchain_model
    
    def create(
        self,
        model: Optional[str] = None,
        messages: Optional[List[Dict[str, str]]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict]] = None,
        **kwargs
    ) -> CompletionResponse:
        """
        Create a chat completion using the langchain model
        
        Args:
            model: Model name (ignored, uses configured model)
            messages: List of message dictionaries
            temperature: Temperature override
            max_tokens: Max tokens override
            tools: Tool definitions (not yet supported)
            **kwargs: Additional parameters
            
        Returns:
            OpenAI-style completion response
        """
        if not messages:
            raise ValueError("messages is required")
        
        # Convert OpenAI messages format to langchain BaseMessage objects
        langchain_messages = []
        for msg in messages:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            
            if role == 'system':
                langchain_messages.append(SystemMessage(content=content))
            elif role == 'user':
                langchain_messages.append(HumanMessage(content=content))
            elif role == 'assistant':
                langchain_messages.append(AIMessage(content=content))
        
        # Invoke the langchain model
        try:
            response = self.langchain_model.invoke(langchain_messages)
            
            # Extract content from langchain response
            if hasattr(response, 'content'):
                content = response.content
            else:
                content = str(response)
            
            # Create OpenAI-style response
            message = Message(role='assistant', content=content)
            choice = Choice(index=0, message=message, finish_reason='stop')
            
            return CompletionResponse(
                id='chatcmpl-adapter',
                object='chat.completion',
                created=0,
                model=str(model or 'adapter'),
                choices=[choice]
            )
        except Exception as e:
            logger.error(f"Error invoking langchain model: {str(e)}")
            raise


class Chat:
    """OpenAI-compatible chat interface"""
    
    def __init__(self, langchain_model):
        self.completions = ChatCompletions(langchain_model)


class OpenAIAdapter:
    """Adapter to make langchain chat models compatible with OpenAI SDK interface"""
    
    def __init__(self, langchain_model):
        """
        Initialize the adapter
        
        Args:
            langchain_model: Any langchain chat model (ChatOpenAI, ChatAnthropic, ChatGoogleGenerativeAI)
        """
        self.langchain_model = langchain_model
        self.chat = Chat(langchain_model)
        logger.info(f"✅ OpenAI adapter created for {type(langchain_model).__name__}")
