"""OpenAI API client wrapper for TOGAF Agent using latest API patterns."""

from typing import List, Dict, Any, Optional
import asyncio
from openai import OpenAI, AsyncOpenAI
from openai.types import CreateEmbeddingResponse
from openai.types.chat import ChatCompletion
import logging
from .config import Settings

logger = logging.getLogger(__name__)


class OpenAIClient:
    """Wrapper for OpenAI API with TOGAF-specific configurations using latest v1+ patterns."""
    
    def __init__(self, settings: Settings):
        """Initialize OpenAI clients (both sync and async) with settings."""
        self.settings = settings
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.async_client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.chat_model = settings.openai_chat_model
        self.embedding_model = settings.openai_embedding_model
    
    async def create_chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """Create a chat completion using GPT-4.1 (async)."""
        try:
            response: ChatCompletion = await self.async_client.chat.completions.create(
                model=self.chat_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Chat completion error: {str(e)}")
            raise Exception(f"Error creating chat completion: {str(e)}")
    
    def create_chat_completion_sync(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """Create a chat completion using GPT-4.1 (synchronous)."""
        try:
            response: ChatCompletion = self.client.chat.completions.create(
                model=self.chat_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Chat completion error: {str(e)}")
            raise Exception(f"Error creating chat completion: {str(e)}")
    
    async def create_embedding(self, text: str) -> List[float]:
        """Create an embedding using text-embedding-3-small (async)."""
        try:
            response: CreateEmbeddingResponse = await self.async_client.embeddings.create(
                model=self.embedding_model,
                input=text,
                encoding_format="float"  # Latest: explicit format for better performance
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Embedding creation error: {str(e)}")
            raise Exception(f"Error creating embedding: {str(e)}")
    
    def create_embedding_sync(self, text: str) -> List[float]:
        """Create an embedding using text-embedding-3-small (synchronous)."""
        try:
            response: CreateEmbeddingResponse = self.client.embeddings.create(
                model=self.embedding_model,
                input=text,
                encoding_format="float"
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Embedding creation error: {str(e)}")
            raise Exception(f"Error creating embedding: {str(e)}")
    
    async def create_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Create embeddings for multiple texts in batch (async)."""
        try:
            # OpenAI embeddings API supports batch processing natively
            response: CreateEmbeddingResponse = await self.async_client.embeddings.create(
                model=self.embedding_model,
                input=texts,
                encoding_format="float"
            )
            return [data.embedding for data in response.data]
        except Exception as e:
            logger.error(f"Batch embedding creation error: {str(e)}")
            raise Exception(f"Error creating batch embeddings: {str(e)}")
    
    def create_embeddings_batch_sync(self, texts: List[str]) -> List[List[float]]:
        """Create embeddings for multiple texts in batch (synchronous)."""
        try:
            response: CreateEmbeddingResponse = self.client.embeddings.create(
                model=self.embedding_model,
                input=texts,
                encoding_format="float"
            )
            return [data.embedding for data in response.data]
        except Exception as e:
            logger.error(f"Batch embedding creation error: {str(e)}")
            raise Exception(f"Error creating batch embeddings: {str(e)}")
    
    def validate_api_key(self) -> bool:
        """Validate OpenAI API key by making a test request."""
        try:
            models = self.client.models.list()
            logger.info("✅ OpenAI API key validation successful")
            return True
        except Exception as e:
            logger.error(f"❌ OpenAI API key validation failed: {str(e)}")
            return False
    
    async def validate_api_key_async(self) -> bool:
        """Validate OpenAI API key by making a test request (async)."""
        try:
            models = await self.async_client.models.list()
            logger.info("✅ OpenAI API key validation successful (async)")
            return True
        except Exception as e:
            logger.error(f"❌ OpenAI API key validation failed (async): {str(e)}")
            return False
    
    async def test_embedding_functionality(self) -> bool:
        """Test embedding functionality with a sample text."""
        try:
            test_text = "TOGAF is The Open Group Architecture Framework"
            embedding = await self.create_embedding(test_text)
            
            expected_dimensions = 1536  # text-embedding-3-small dimensions
            if len(embedding) == expected_dimensions:
                logger.info(f"✅ Embedding test successful: {len(embedding)} dimensions")
                return True
            else:
                logger.warning(f"⚠️ Unexpected embedding dimensions: {len(embedding)}, expected {expected_dimensions}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Embedding test failed: {str(e)}")
            return False
    
    def get_model_info(self) -> Dict[str, str]:
        """Get information about configured models."""
        return {
            "chat_model": self.chat_model,
            "embedding_model": self.embedding_model,
            "api_key_configured": bool(self.settings.openai_api_key)
        }