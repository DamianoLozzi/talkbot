import asyncio

from nc_py_api.talk import Conversation, TalkMessage,ConversationType
from lib.ollama_client import OllamaChat as OllamaAI
from lib.message_processor import MessageProcessor
from lib.nextcloud_client import NextcloudClient
from simple_logger import Logger
from lib.config import Config
from typing import List
from lib.constants import REACTIONS

log=Logger()


class TalkBot:

    def __init__(self):
        log.info("[TalkBot] Initializing NextcloudBot and OllamaAI...")
        self.conf = Config()
        self.nc_bot = NextcloudClient()
        self.ollama = OllamaAI()
        self.processor=MessageProcessor(self.nc_bot,self.ollama)
        self.check_interval = int(self.conf.NEXTCLOUD_CHECK_INTERVAL)

    async def monitor_and_reply(self, check_interval: int = 2) -> None:
        log.info("[Monitor] Starting conversation monitor...")
        asyncio.create_task(self.processor.start_workers())
        
        while True:
            try:
                log.info("[Monitor] Checking for unread messages...")
                conversations = await self.get_unread_conversations()
                for conversation in conversations:
                    await self.nc_bot.clear_reactions(conversation=conversation)
                    log.info(f"[Monitor] Unread messages found in {conversation.display_name}. Adding conversation to queue...")
                    await self.processor.add_to_queue(conversation)
                    if conversation.last_message is not None:
                        try:
                            await self.nc_bot.set_reaction(conversation=conversation,message=conversation.last_message,reaction=REACTIONS.get("SEEN"))
                        except Exception as e:
                            log.warning("[Monitor] could not set reaction")
                    else:
                        log.warning(f"[Monitor] Conversation {conversation.conversation_id} has no last_message; skipping reaction.")
            except Exception as e:
                log.error(f"[Monitor] Failed to monitor and reply: {e}")
            
            log.info(f"[Monitor] Sleeping for {check_interval} seconds...")
            await asyncio.sleep(check_interval)
    
    async def get_unread_conversations(self) -> List[Conversation]:
        try:
            conversations : List[Conversation] = await self.nc_bot.get_user_conversations(modified_since=True)
            unanswered_conversations= [conv for conv in conversations if conv.conversation_type.name == "ONE_TO_ONE" and conv.unread_messages_count > 0]
            if unanswered_conversations:
                log.info(f"[Monitor] Found {len(unanswered_conversations)} conversations with unread messages.")
            else:
                log.info("[Monitor] No conversations with unread messages found.")
            return unanswered_conversations
        except Exception as e:
            log.error(f"[Monitor] Failed to retrieve unread conversations: {e}")
            return []
    
    async def get_filtered_messages(self, conversation_id: int) -> List[TalkMessage]:
        try:
            messages = await self.nc_bot.retrieve_conversation_history(conversation_id)
            return [msg for msg in messages if msg.message not in [
                "You deleted a message", "{actor} deleted a message", "Message deleted by author", "Message deleted by you"
            ]]
        except Exception as e:
            log.error(f"[Monitor] Failed to retrieve messages for conversation {conversation_id}: {e}")
            return []
        

if __name__ == "__main__":
    bot = TalkBot()
    asyncio.run(bot.monitor_and_reply(bot.check_interval))
