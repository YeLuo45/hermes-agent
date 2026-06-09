"""
Conversation Manager - High-level conversation orchestration and state management.
"""

from typing import Optional

import intent_parser as _intent_parser_module
import operations as _operations_module
from intent_parser import IntentParser
from operations import ConversationOperations
from types import (
    ConversationContext,
    Intent,
    Message,
    MessageRole,
    OperationResult,
)


class ConversationManager:
    """
    High-level conversation manager that orchestrates intent parsing
    and conversation operations together.
    """

    def __init__(self):
        """Initialize the conversation manager with all components."""
        self.operations = ConversationOperations()
        self.intent_parser = IntentParser()

    def start_conversation(
        self,
        session_id: str,
        user_id: Optional[str] = None,
        channel: Optional[str] = None,
        platform: Optional[str] = None,
    ) -> OperationResult:
        """
        Start a new conversation.

        Args:
            session_id: Unique session identifier
            user_id: Optional user identifier
            channel: Optional channel name
            platform: Optional platform name

        Returns:
            OperationResult indicating success or failure
        """
        result = self.operations.create_conversation(session_id, user_id)

        if result.success and (channel or platform):
            self.operations.update_context(
                session_id,
                metadata={"channel": channel, "platform": platform},
            )

        return result

    def process_message(
        self,
        session_id: str,
        content: str,
        role: MessageRole = MessageRole.USER,
        metadata: Optional[dict] = None,
    ) -> OperationResult:
        """
        Process a user message: parse intent and store message.

        Args:
            session_id: Conversation session ID
            content: Message content
            role: Message role (default: user)
            metadata: Optional metadata

        Returns:
            OperationResult with message and intent info
        """
        # Ensure conversation exists
        if session_id not in self.operations._conversations:
            self.operations.create_conversation(session_id)

        # Parse intent for user messages
        intent: Optional[Intent] = None
        if role == MessageRole.USER:
            intent = self.intent_parser.parse(content)
            self.operations.update_context(session_id, intent=intent)

        # Add message
        result = self.operations.add_message(session_id, role, content, metadata)

        if result.success and intent:
            result.data["intent"] = intent.to_dict()

        return result

    def get_response(
        self,
        session_id: str,
        limit: Optional[int] = None,
    ) -> OperationResult:
        """
        Get conversation history for generating a response.

        Args:
            session_id: Conversation session ID
            limit: Optional message limit

        Returns:
            OperationResult with messages and context
        """
        messages_result = self.operations.get_conversation(session_id, limit=limit)
        context_result = self.operations.get_context(session_id)

        if not messages_result.success:
            return messages_result

        combined_data = messages_result.data or {}
        if context_result.success:
            combined_data["context"] = context_result.data

        return OperationResult(
            success=True,
            message="Response data retrieved",
            data=combined_data,
        )

    def end_conversation(self, session_id: str) -> OperationResult:
        """
        End a conversation gracefully.

        Args:
            session_id: Conversation session ID

        Returns:
            OperationResult indicating success
        """
        return self.operations.archive_conversation(session_id)

    def get_conversation_summary(
        self,
        session_id: str,
    ) -> OperationResult:
        """
        Get a summary of the conversation.

        Args:
            session_id: Conversation session ID

        Returns:
            OperationResult with conversation summary
        """
        messages_result = self.operations.get_conversation(session_id)
        context_result = self.operations.get_context(session_id)

        if not messages_result.success:
            return messages_result

        messages = messages_result.data.get("messages", [])
        context = context_result.data if context_result.success else {}

        # Build summary
        user_messages = [m for m in messages if m["role"] == MessageRole.USER.value]
        assistant_messages = [m for m in messages if m["role"] == MessageRole.ASSISTANT.value]

        summary = {
            "session_id": session_id,
            "total_messages": len(messages),
            "user_messages": len(user_messages),
            "assistant_messages": len(assistant_messages),
            "last_intent": context.get("last_intent"),
            "message_count": context.get("message_count", 0),
            "first_message": messages[0] if messages else None,
            "last_message": messages[-1] if messages else None,
        }

        return OperationResult(
            success=True,
            message="Summary retrieved",
            data=summary,
        )

    def export_conversation(self, session_id: str) -> OperationResult:
        """
        Export a conversation for backup or transfer.

        Args:
            session_id: Conversation session ID

        Returns:
            OperationResult with exported conversation
        """
        return self.operations.export_conversation(session_id)

    def list_all_conversations(self, limit: int = 50) -> OperationResult:
        """
        List all conversations.

        Args:
            limit: Maximum number to return

        Returns:
            OperationResult with conversation list
        """
        return self.operations.list_conversations(limit=limit)

    def delete_conversation(self, session_id: str) -> OperationResult:
        """
        Delete a conversation permanently.

        Args:
            session_id: Conversation session ID

        Returns:
            OperationResult indicating success
        """
        return self.operations.delete_conversation(session_id)

    def update_user_context(
        self,
        session_id: str,
        user_id: Optional[str] = None,
        channel: Optional[str] = None,
        platform: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> OperationResult:
        """
        Update context fields for a conversation.

        Args:
            session_id: Conversation session ID
            user_id: Optional new user ID
            channel: Optional new channel
            platform: Optional new platform
            metadata: Optional metadata to merge

        Returns:
            OperationResult indicating success
        """
        kwargs = {}
        if user_id is not None:
            kwargs["user_id"] = user_id
        if channel is not None:
            kwargs["channel"] = channel
        if platform is not None:
            kwargs["platform"] = platform

        return self.operations.update_context(session_id, metadata=metadata, **kwargs)

    def get_supported_intents(self) -> list[str]:
        """
        Get list of all supported intents.

        Returns:
            List of intent names
        """
        return self.intent_parser.get_supported_intents()

    def add_custom_intent(self, intent_name: str, patterns: list[str]):
        """
        Add a custom intent with patterns.

        Args:
            intent_name: Name of the new intent
            patterns: List of regex patterns
        """
        self.intent_parser.add_intent_pattern(intent_name, patterns)
