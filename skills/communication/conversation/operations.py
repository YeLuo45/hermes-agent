"""
Conversation Operations - Core business logic operations for conversations.
"""

import json
import uuid
from datetime import datetime
from typing import Optional

from conversation_types import (
    ConversationContext,
    ConversationStatus,
    Intent,
    Message,
    MessageRole,
    OperationResult,
)


class ConversationOperations:
    """
    Core operations for managing conversations.
    Handles message storage, retrieval, and conversation state management.
    """

    def __init__(self):
        """Initialize conversation operations."""
        self._conversations: dict[str, list[Message]] = {}
        self._contexts: dict[str, ConversationContext] = {}

    def create_conversation(self, session_id: str, user_id: Optional[str] = None) -> OperationResult:
        """
        Create a new conversation.

        Args:
            session_id: Unique session identifier
            user_id: Optional user identifier

        Returns:
            OperationResult indicating success or failure
        """
        try:
            if session_id in self._conversations:
                return OperationResult(
                    success=False,
                    message=f"Conversation {session_id} already exists",
                    error="duplicate_session_id",
                )

            self._conversations[session_id] = []
            self._contexts[session_id] = ConversationContext(
                session_id=session_id,
                user_id=user_id,
                message_count=0,
            )

            return OperationResult(
                success=True,
                message=f"Conversation {session_id} created successfully",
                data={"session_id": session_id},
            )
        except Exception as e:
            return OperationResult(
                success=False,
                message="Failed to create conversation",
                error=str(e),
            )

    def add_message(
        self,
        session_id: str,
        role: MessageRole,
        content: str,
        metadata: Optional[dict] = None,
    ) -> OperationResult:
        """
        Add a message to a conversation.

        Args:
            session_id: Conversation session ID
            role: Message role (user/assistant/system/tool)
            content: Message content
            metadata: Optional metadata dict

        Returns:
            OperationResult with the created message
        """
        try:
            if session_id not in self._conversations:
                return OperationResult(
                    success=False,
                    message=f"Conversation {session_id} not found",
                    error="session_not_found",
                )

            message = Message(
                id=str(uuid.uuid4()),
                role=role,
                content=content,
                timestamp=datetime.now(),
                metadata=metadata or {},
            )

            self._conversations[session_id].append(message)

            # Update context
            if session_id in self._contexts:
                self._contexts[session_id].message_count += 1

            return OperationResult(
                success=True,
                message="Message added successfully",
                data={"message": message.to_dict()},
            )
        except Exception as e:
            return OperationResult(
                success=False,
                message="Failed to add message",
                error=str(e),
            )

    def get_conversation(
        self,
        session_id: str,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> OperationResult:
        """
        Retrieve a conversation's messages.

        Args:
            session_id: Conversation session ID
            limit: Maximum number of messages to return
            offset: Number of messages to skip

        Returns:
            OperationResult with messages list
        """
        try:
            if session_id not in self._conversations:
                return OperationResult(
                    success=False,
                    message=f"Conversation {session_id} not found",
                    error="session_not_found",
                )

            messages = self._conversations[session_id]

            if offset > 0:
                messages = messages[offset:]
            if limit is not None:
                messages = messages[:limit]

            return OperationResult(
                success=True,
                message="Conversation retrieved successfully",
                data={
                    "session_id": session_id,
                    "messages": [m.to_dict() for m in messages],
                    "total": len(self._conversations[session_id]),
                },
            )
        except Exception as e:
            return OperationResult(
                success=False,
                message="Failed to retrieve conversation",
                error=str(e),
            )

    def get_context(self, session_id: str) -> OperationResult:
        """
        Get conversation context.

        Args:
            session_id: Conversation session ID

        Returns:
            OperationResult with context data
        """
        try:
            if session_id not in self._contexts:
                return OperationResult(
                    success=False,
                    message=f"Context for {session_id} not found",
                    error="session_not_found",
                )

            context = self._contexts[session_id]

            return OperationResult(
                success=True,
                message="Context retrieved successfully",
                data={
                    "session_id": context.session_id,
                    "user_id": context.user_id,
                    "channel": context.channel,
                    "platform": context.platform,
                    "metadata": context.metadata,
                    "last_intent": context.last_intent.to_dict() if context.last_intent else None,
                    "message_count": context.message_count,
                },
            )
        except Exception as e:
            return OperationResult(
                success=False,
                message="Failed to get context",
                error=str(e),
            )

    def update_context(
        self,
        session_id: str,
        intent: Optional[Intent] = None,
        metadata: Optional[dict] = None,
        **kwargs,
    ) -> OperationResult:
        """
        Update conversation context.

        Args:
            session_id: Conversation session ID
            intent: Optional new intent to set
            metadata: Optional metadata to merge
            **kwargs: Additional context fields to update

        Returns:
            OperationResult indicating success
        """
        try:
            if session_id not in self._contexts:
                return OperationResult(
                    success=False,
                    message=f"Context for {session_id} not found",
                    error="session_not_found",
                )

            context = self._contexts[session_id]

            if intent is not None:
                context.last_intent = intent

            if metadata is not None:
                context.metadata.update(metadata)

            for key, value in kwargs.items():
                if hasattr(context, key):
                    setattr(context, key, value)

            return OperationResult(
                success=True,
                message="Context updated successfully",
            )
        except Exception as e:
            return OperationResult(
                success=False,
                message="Failed to update context",
                error=str(e),
            )

    def archive_conversation(self, session_id: str) -> OperationResult:
        """
        Archive a conversation.

        Args:
            session_id: Conversation session ID

        Returns:
            OperationResult indicating success
        """
        try:
            if session_id not in self._conversations:
                return OperationResult(
                    success=False,
                    message=f"Conversation {session_id} not found",
                    error="session_not_found",
                )

            # Mark messages as archived (soft delete)
            if session_id in self._contexts:
                self._contexts[session_id].metadata["status"] = ConversationStatus.ARCHIVED.value
                self._contexts[session_id].metadata["archived_at"] = datetime.now().isoformat()

            return OperationResult(
                success=True,
                message="Conversation archived successfully",
            )
        except Exception as e:
            return OperationResult(
                success=False,
                message="Failed to archive conversation",
                error=str(e),
            )

    def delete_conversation(self, session_id: str) -> OperationResult:
        """
        Delete a conversation and its context.

        Args:
            session_id: Conversation session ID

        Returns:
            OperationResult indicating success
        """
        try:
            if session_id not in self._conversations:
                return OperationResult(
                    success=False,
                    message=f"Conversation {session_id} not found",
                    error="session_not_found",
                )

            del self._conversations[session_id]

            if session_id in self._contexts:
                del self._contexts[session_id]

            return OperationResult(
                success=True,
                message="Conversation deleted successfully",
            )
        except Exception as e:
            return OperationResult(
                success=False,
                message="Failed to delete conversation",
                error=str(e),
            )

    def list_conversations(self, limit: int = 50) -> OperationResult:
        """
        List all conversations.

        Args:
            limit: Maximum number of conversations to return

        Returns:
            OperationResult with conversation summaries
        """
        try:
            summaries = []
            for session_id, messages in self._conversations.items():
                context = self._contexts.get(session_id)
                status = ConversationStatus.ACTIVE.value
                if context:
                    status = context.metadata.get("status", ConversationStatus.ACTIVE.value)

                summaries.append({
                    "session_id": session_id,
                    "message_count": len(messages),
                    "status": status,
                    "last_message_at": messages[-1].timestamp.isoformat() if messages else None,
                    "user_id": context.user_id if context else None,
                })

            # Sort by last message time, most recent first
            summaries.sort(
                key=lambda x: x["last_message_at"] or "",
                reverse=True,
            )

            return OperationResult(
                success=True,
                message="Conversations listed successfully",
                data={
                    "conversations": summaries[:limit],
                    "total": len(summaries),
                },
            )
        except Exception as e:
            return OperationResult(
                success=False,
                message="Failed to list conversations",
                error=str(e),
            )

    def export_conversation(self, session_id: str) -> OperationResult:
        """
        Export a conversation to JSON format.

        Args:
            session_id: Conversation session ID

        Returns:
            OperationResult with exported JSON
        """
        try:
            if session_id not in self._conversations:
                return OperationResult(
                    success=False,
                    message=f"Conversation {session_id} not found",
                    error="session_not_found",
                )

            messages = self._conversations[session_id]
            context = self._contexts.get(session_id)

            export_data = {
                "session_id": session_id,
                "messages": [m.to_dict() for m in messages],
                "context": {
                    "session_id": context.session_id,
                    "user_id": context.user_id,
                    "channel": context.channel,
                    "platform": context.platform,
                    "metadata": context.metadata,
                    "message_count": context.message_count,
                } if context else None,
                "exported_at": datetime.now().isoformat(),
            }

            return OperationResult(
                success=True,
                message="Conversation exported successfully",
                data={"export": export_data},
            )
        except Exception as e:
            return OperationResult(
                success=False,
                message="Failed to export conversation",
                error=str(e),
            )
