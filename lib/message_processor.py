import asyncio

from nc_py_api.talk import TalkMessage, Conversation
from lib.nextcloud_client import NextcloudClient
from lib.ollama_client import OllamaChat,Message
from simple_logger import Logger
from typing import List
from lib.constants import REACTIONS
from lib.utils import Mappers,Filters

log = Logger()

class MessageProcessor:
    def __init__(self, nc_bot: NextcloudClient, ollama: OllamaChat, max_workers: int = 3):
        self.queue : asyncio.Queue = asyncio.Queue()
        self.nc_bot : NextcloudClient = nc_bot
        self.ollama :OllamaChat = ollama
        self.max_workers : int = max_workers
        self.running : bool = False
        self.filters:Filters=Filters()
        self.mappers:Mappers=Mappers()

    async def start_workers(self):
        self.running = True
        workers = [asyncio.create_task(self.worker()) for _ in range(self.max_workers)]
        await asyncio.gather(*workers)

    async def stop_workers(self):
        self.running = False
        for _ in range(self.max_workers):
            await self.queue.put(None)  

    async def worker(self):
        while self.running:
            conversation : Conversation = await self.queue.get()
            if conversation is None:
                break

            try:
                log.info(f"[Worker] Fetching messages for {conversation.display_name}...")
                messages : List[TalkMessage] = await self.nc_bot.retrieve_conversation_history(conversation.conversation_id)

                if messages:
                    log.info(f"[Worker] Processing {len(messages)} messages from {conversation.display_name}...")
                    
                    filtered_messages:List[TalkMessage]=self.filters.filter_useful_messages(messages=messages)
                    ollama_messages: List[Message] = [Message(role="system", content=self.ollama.system_prompt)]
                    ollama_messages.extend(self.mappers.talk_message_to_ollama_message(message,self.ollama.assistant_id) for message in reversed(filtered_messages))
                    
                    last_message : TalkMessage = await self.nc_bot.retrieve_message_by_id(conversation_id=conversation.conversation_id,message_id=conversation.last_message.message_id) # type:ignore

                    await self.nc_bot.set_reaction(conversation=conversation,message=last_message,reaction=REACTIONS.get("ANSWERING")) 
                    log.debug(f"messages:{len(messages)}")
                    log.debug(f"filtered messages:{len(filtered_messages)}")
                    log.debug(f"ollama messages:{len(ollama_messages)}")
                    response = await self.ollama.send_message_chat(ollama_messages) 
                    
                    updated_conv :Conversation = await self.nc_bot.retrieve_conversation_by_id(conversation.conversation_id)
                    new_last_message:TalkMessage=updated_conv.last_message # type:ignore
                    
                    if last_message.message_id == new_last_message.message_id:
                        answered:bool=await self.nc_bot.reply_to_conversation(conversation, response) # type:ignore
                        log.info(f"[Worker] Replied to {conversation.display_name}.")
                        
                        if answered:
                            await self.nc_bot.set_reaction(conversation=conversation,message=last_message,reaction=REACTIONS.get("ANSWERED"))
                    else:
                        log.debug("[Worker] Last message is outdated, discarding answer.")
                        await self.nc_bot.set_reaction(conversation=conversation,message=last_message,reaction=REACTIONS.get("IGNORED"))
                        
                else:
                    log.info(f"[Worker] No new messages found for {conversation.display_name}. Skipping.")

            except Exception as e:
                log.error(f"[Worker] Error processing conversation {conversation.display_name}: {e}")
                await self.nc_bot.set_reaction(conversation=conversation,message=last_message,reaction=REACTIONS.get("FAILED"))
            finally:
                self.queue.task_done()

    async def add_to_queue(self, conversation: Conversation):
        log.info(f"[Worker] Adding messages from {conversation.display_name} to queue...")
        await self.queue.put((conversation))
