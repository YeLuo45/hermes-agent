"""
Conversation Service - A complete conversation management service.

Components:
- types: Type definitions and data classes
- intent_parser: Intent detection and entity extraction
- operations: Core conversation CRUD operations
- conversation_manager: High-level orchestration

Usage:
    from conversation import ConversationManager

    # Initialize
    manager = ConversationManager()

    # Start a conversation
    manager.start_conversation(
        session_id="session-123",
        user_id="user-456",
        channel="support",
        platform="web"
    )

    # Process a user message
    result = manager.process_message(
        session_id="session-123",
        content="Hello, I need help with my order"
    )

    # Get intent
    intent = result.data.get("intent")
    print(f"Detected intent: {intent['name']} (confidence: {intent['confidence']})")

    # Get conversation history
    response = manager.get_response(session_id="session-123")
    messages = response.data.get("messages")

    # End conversation
    manager.end_conversation(session_id="session-123")
"""

# Import modules
import types
import intent_parser
import operations
import conversation_manager

# Re-export for convenience
Message = types.Message
MessageRole = types.MessageRole
Intent = types.Intent
IntentConfidence = types.IntentConfidence
ConversationContext = types.ConversationContext
ConversationStatus = types.ConversationStatus
OperationResult = types.OperationResult

IntentParser = intent_parser.IntentParser
ConversationOperations = operations.ConversationOperations
ConversationManager = conversation_manager.ConversationManager


__all__ = [
    # Types
    "Message",
    "MessageRole",
    "Intent",
    "IntentConfidence",
    "ConversationContext",
    "ConversationStatus",
    "OperationResult",
    # Parser
    "IntentParser",
    # Operations
    "ConversationOperations",
    # Manager
    "ConversationManager",
]


__version__ = "1.0.0"
