from lib.constants import USELESS_MESSAGES
from nc_py_api.talk import TalkMessage, MessageReactions
from ollama import AsyncClient, Message, GenerateResponse, ChatResponse
from simple_logger import Logger
from datetime import datetime
from typing import List

log = Logger()


class Filters():

    def is_useless(self, talk_message: TalkMessage) -> bool:
        return talk_message.message not in USELESS_MESSAGES

    def is_empty(self, any) -> bool:
        if isinstance(any, TalkMessage):
            return any.message is None or ""

    def is_structurally_useless(self, message: TalkMessage) -> bool:
        if not message.message:
            return True
        msg = message.message.strip().lower()
        return msg in USELESS_MESSAGES

    def filter_useful_messages(
            self, messages: List[TalkMessage]) -> List[TalkMessage]:
        filtered: List[TalkMessage] = []
        for m in messages:
            if self.is_structurally_useless(m):
                log.debug(f"[Filters] discarded message: {m.message}")
            else:
                filtered.append(m)
        return filtered

    def trim_thought(text: str) -> str:
        import re
        return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


class Mappers():

    def talk_message_to_ollama_message(self, talk_message: TalkMessage,
                                       assistant_id: str) -> Message:
        human_timestamp = datetime.fromtimestamp(talk_message.timestamp)

        context = f"""
        Timestamp: {human_timestamp}
        Id:{talk_message.message_id}
        Replies to:{talk_message.parent}
        Reactions: {talk_message.reactions}      
        """

        content = talk_message.message if talk_message.actor_id == assistant_id else f"Context (ignore for generation): {context} \n Message: {talk_message.message}"

        return Message(role="assistant"
                       if talk_message.actor_id == assistant_id else "user",
                       content=content)
