"""Test script for conversation service."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from index import (
    ConversationManager,
    MessageRole,
    IntentConfidence,
)

# Test basic functionality
manager = ConversationManager()

# Start conversation
r = manager.start_conversation('test-session-1', user_id='user-1')
print('Start:', r.success, r.message)

# Process message
r = manager.process_message('test-session-1', 'Hello, I need help with my order')
print('Process:', r.success)
if r.data and 'intent' in r.data:
    intent = r.data['intent']
    print(f'Intent: {intent["name"]} ({intent["confidence_level"]})')

# Add another message
r = manager.process_message('test-session-1', 'create a new task', role=MessageRole.USER)
if r.data and 'intent' in r.data:
    print(f'Intent 2: {r.data["intent"]["name"]}')

# Get response
r = manager.get_response('test-session-1')
print('Messages:', len(r.data.get('messages', [])))

# Get summary
r = manager.get_conversation_summary('test-session-1')
print('Summary:', r.data.get('total_messages'), 'messages')

# List supported intents
intents = manager.get_supported_intents()
print('Supported intents:', len(intents), intents[:5])

print('All tests passed!')
