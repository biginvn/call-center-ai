from enum import Enum


class ConversationType(str, Enum):
    AGENT_TO_AGENT = "A->A"
    AGENT_TO_AI = "A->AI"
    AGENT_TO_CUSTOMER = "A->C"


class MessageType(str, Enum):
    AGENT = "Agent"
    CUSTOMER = "C"
    AI = "AI"


class ConversationMood(str, Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    UNKNOWN = "unknown"
    

class ConversationStatus(str, Enum):
    START = "start"
    ACCEPT = "accept"
    DECLINE = "decline"
    CLOSED = "closed"
   

