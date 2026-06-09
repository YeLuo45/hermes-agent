"""
Conversation Service Types - Type definitions for conversation management.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional
from datetime import datetime


class MessageRole(str, Enum):
    """Message sender role."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class ConversationStatus(str, Enum):
    """Conversation lifecycle status."""
    ACTIVE = "active"
    ARCHIVED = "archived"
    ENDED = "ended"


class IntentConfidence(str, Enum):
    """Intent parsing confidence level."""
    HIGH = "high"      # >= 0.8
    MEDIUM = "medium"  # >= 0.5
    LOW = "low"        # >= 0.3
    UNKNOWN = "unknown"  # < 0.3


@dataclass
class Message:
    """A single message in a conversation."""
    id: str
    role: MessageRole
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "role": self.role.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class Intent:
    """Parsed user intent from a message."""
    name: str
    confidence: float
    confidence_level: IntentConfidence
    entities: dict[str, Any] = field(default_factory=dict)
    raw_text: str = ""
    alternatives: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "confidence": self.confidence,
            "confidence_level": self.confidence_level.value,
            "entities": self.entities,
            "raw_text": self.raw_text,
            "alternatives": self.alternatives,
        }


@dataclass
class ConversationContext:
    """Context information for a conversation."""
    session_id: str
    user_id: Optional[str] = None
    channel: Optional[str] = None
    platform: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)
    last_intent: Optional[Intent] = None
    message_count: int = 0


@dataclass
class OperationResult:
    """Result of a conversation operation."""
    success: bool
    message: str
    data: Optional[dict] = None
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "message": self.message,
            "data": self.data,
            "error": self.error,
        }
