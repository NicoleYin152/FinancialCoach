"""In-memory conversation state store. Not persistence."""

from typing import Dict

from agent.schemas.conversation import ConversationState

CONVERSATION_HISTORY: Dict[str, ConversationState] = {}
