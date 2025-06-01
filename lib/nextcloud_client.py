import ollama
import time
import asyncio

from nc_py_api import AsyncNextcloud, NextcloudException, FsNode 
from httpx import Limits, Timeout, AsyncClient, HTTPTransport
from nc_py_api.talk import TalkMessage, Conversation,MessageReactions
from typing import List, Any, Optional
from simple_logger import Logger
from lib.config import Config
from lib.constants import REACTIONS
from lib.retry import retry_async, retry_sync

log = Logger()

class NextcloudClient:

    def __init__(self) -> None:
        self.conf = Config()
        self.url = self.conf.NEXTCLOUD_URL
        self.username = self.conf.NEXTCLOUD_USERNAME
        self.password = self.conf.NEXTCLOUD_PASSWORD
        self.max_retries: int = int(self.conf.NEXTCLOUD_MAX_RETRIES)
        self.retry_delay: int = int(self.conf.NEXTCLOUD_RETRY_DELAY)
        self.nc: Optional[AsyncNextcloud] = None

        self.client: AsyncClient = AsyncClient(
            transport=HTTPTransport(retries=5, verify=False),
            limits=Limits(max_connections=10, max_keepalive_connections=5),
            timeout=Timeout(10.0, connect=5.0),
        )

        log.info("[Nextcloud] Connecting to Nextcloud...")
        self.connect_nextcloud()

    @retry_sync()
    def connect_nextcloud(self) -> None:
        log.info("[Nextcloud] Attempting connection...")
        self.nc = AsyncNextcloud(
            nextcloud_url=self.url,
            nc_auth_user=self.username,
            nc_auth_pass=self.password,
            client=self.client
        )
        log.info("[Nextcloud] Connected to Nextcloud.")

    @retry_async(exceptions=(NextcloudException,))
    async def retrieve_conversation_by_id(self, conversation_id: int) -> Conversation:
        return next((conv for conv in await self.nc.talk.get_user_conversations() if conv.conversation_id == conversation_id), None)

    @retry_async(exceptions=(NextcloudException,))
    async def retrieve_message_by_id(self, conversation_id: int, message_id: int) -> TalkMessage:
        conversation = await self.retrieve_conversation_by_id(conversation_id)
        messages = await self.nc.talk.receive_messages(conversation=conversation, look_in_future=False, limit=200)
        return next(message for message in messages if message.message_id == message_id)

    @retry_async(exceptions=(NextcloudException,))
    async def receive_messages(self, conversation: Conversation, look_in_future=False):
        return await self.nc.talk.receive_messages(conversation=conversation, look_in_future=look_in_future, limit=200)

    @retry_async(exceptions=(NextcloudException,))
    async def retrieve_conversation_history(self, conversation_id: int) -> List[TalkMessage]:
        log.info(f"[Nextcloud] Retrieving messages for conversation {conversation_id}")
        conversation = await self.retrieve_conversation_by_id(conversation_id)
        if conversation:
            messages = await self.receive_messages(conversation=conversation, look_in_future=False)
            if messages:
                log.info(f"[Nextcloud] Retrieved {len(messages)} messages.")
                return messages
        log.warning(f"[Nextcloud] No messages found for conversation {conversation_id}")
        return []

    @retry_async()
    async def reply_to_conversation(self, conversation: Conversation, message: str) -> bool:
        log.info(f"[Nextcloud] Replying to conversation {conversation.conversation_id} with message: {message}")
        if conversation:
            await self.nc.talk.send_message(conversation=conversation, message=message)
            log.info(f"[Nextcloud] Replied to conversation {conversation.conversation_id}.")
            return True
        log.warning(f"[Nextcloud] Conversation not found")
        return False

    @retry_async()
    async def get_user_conversations(self, no_status_update: bool = True, include_status: bool = False, modified_since: int | bool = 0) -> list[Conversation]:
        log.info("[Nextcloud] Retrieving user conversations...")
        conversations = await self.nc.talk.get_user_conversations(no_status_update=no_status_update, include_status=include_status, modified_since=modified_since)
        if conversations:
            log.info(f"[Nextcloud] Retrieved {len(conversations)} conversations.")
            return conversations
        log.info("[Nextcloud] No conversations found.")
        return []

    async def get_last_message(self, conv: Conversation) -> TalkMessage:
        return conv.last_message

    async def set_message_unread(self, conversation_id: int, message_id: int):
        pass  # TODO to be implemented

    @retry_async()
    async def set_reaction(self, conversation: Conversation, message: TalkMessage, reaction: Optional[str] = None) -> bool:
        conversation = await self.retrieve_conversation_by_id(conversation.conversation_id)
        message = await self.retrieve_message_by_id(conversation_id=conversation.conversation_id, message_id=message.message_id)
        reactions_dict = await self.nc.talk.get_message_reactions(conversation=conversation, message=message)
        for emoji, reacts in reactions_dict.items():
            if emoji in REACTIONS.values():
                for react in reacts:
                    if react.actor_id == self.username:
                        await self.nc.talk.delete_reaction(conversation=conversation, message=message, reaction=emoji)
        if reaction not in [None, REACTIONS.get("DELETE")]:
            await self.nc.talk.react_to_message(conversation=conversation, message=message, reaction=reaction)
        return True

    @retry_async()
    async def clear_reactions(self, conversation: Conversation) -> bool:
        for message in await self.receive_messages(conversation=conversation, look_in_future=False):
            if len(message.reactions) != 0:
                await self.set_reaction(conversation=conversation, message=message, reaction=REACTIONS.get("DELETE"))
        return True
