import asyncio

from ollama import AsyncClient, Message, GenerateResponse, ChatResponse
from nc_py_api.talk import TalkMessage
from typing import Optional, List
from simple_logger import Logger
from lib.config import Config
from datetime import datetime
from lib.retry import retry_sync,retry_async

log = Logger()

class OllamaChat:

    def __init__(self):
        self.conf = Config()
        self.host = self.conf.OLLAMA_HOST
        self.model = self.conf.OLLAMA_MODEL
        self.system_prompt = self.conf.OLLAMA_SYSTEM_PROMPT
        self.assistant_id = self.conf.OLLAMA_ACTOR_ID
        self.client = AsyncClient(host=self.host)
        self.max_retries: int = int(self.conf.NEXTCLOUD_MAX_RETRIES)
        self.retry_delay: int = int(self.conf.NEXTCLOUD_RETRY_DELAY)
        log.info("[Ollama] Initialized with model: " + self.model)

    @retry_async()
    async def send_message_chat(self, messages: List[Message]) -> ChatResponse:
                response: ChatResponse = await self.client.chat(messages=messages, model=self.model)
                response_content = response.message.content if response.message else "No response received."
                if response_content not in [None,'']:
                    log.info("[Ollama] Response correctly received.")
                    return response_content
                else:
                    raise Exception("Ollama returned an invalid response")
    
    @retry_async()
    async def send_message_generate(self, message: str) -> GenerateResponse:
                log.debug("[Ollama] Sending message via /generate...")
                response: GenerateResponse = await self.client.generate(model=self.model, prompt=message)
                result = response.response if response.response else "No response received."
                log.info("[Ollama] Response correctly received.")
                log.debug("[Ollama] Response received: " + result)
                return result
        
if __name__ == "__main__":
    async def test_ollama():
        chat = OllamaChat()
        user_input = "Hello, how are you?"
        response = await chat.send_message_generate(user_input)
        log.info(f"Ollama: {response}")
    
    asyncio.run(test_ollama())