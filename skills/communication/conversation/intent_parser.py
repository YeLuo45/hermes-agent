"""
Intent Parser - Parses user messages to extract intents and entities.
"""

import re
from typing import Optional
import conversation_types as _types

Intent = _types.Intent
IntentConfidence = _types.IntentConfidence
Message = _types.Message


class IntentParser:
    """
    Parses user messages to identify intents and extract entities.
    Uses pattern matching and keyword detection for intent classification.
    """

    # Intent patterns - can be extended with more sophisticated NLP
    INTENT_PATTERNS = {
        "greeting": [
            r"\b(hi|hello|hey|good\s*morning|good\s*afternoon|good\s*evening)\b",
            r"^\s*你好|您好|嗨",
        ],
        "farewell": [
            r"\b(bye|goodbye|see\s*you|talk\s*later|good\s*night)\b",
            r"再见|拜拜|下次见",
        ],
        "help_request": [
            r"\b(help|assist|support|guide|how\s*do\s*i|can\s*you|tell\s*me)\b",
            r"帮我|帮帮我|怎么|如何",
        ],
        "question": [
            r"\?\s*$",
            r"\b(what|who|where|when|why|how|which)\b",
            r"什么|谁|哪里|什么时候|为什么|如何",
        ],
        "task_create": [
            r"\b(create|add|new|make|start|begin)\b.*\b(task|todo|item|note)\b",
            r"创建|新建|添加.*任务|添加.*待办",
        ],
        "task_complete": [
            r"\b(complete|finish|done|mark|check|cross\s*off)\b.*\b(task|todo|item)\b",
            r"完成|结束|标记.*完成",
        ],
        "task_list": [
            r"\b(list|show|get|display|view)\b.*\b(tasks|todos|items)\b",
            r"查看|显示|列出.*任务",
        ],
        "search": [
            r"\b(search|find|look\s*up|query)\b",
            r"搜索|查找|找",
        ],
        "code_generate": [
            r"\b(write|create|generate|make|build)\b.*\b(code|function|class|script)\b",
            r"写代码|生成代码|创建函数",
        ],
        "code_debug": [
            r"\b(debug|fix|error|issue|problem|bug)\b.*\b(code)?\b",
            r"调试|修复|错误|问题",
        ],
        "file_operation": [
            r"\b(read|write|edit|modify|delete|create)\b.*\b(file|folder|directory)\b",
            r"读取|写入|编辑|删除.*文件",
        ],
        "git_operation": [
            r"\b(git|commit|push|pull|merge|branch|checkout)\b",
            r"提交|推送|拉取",
        ],
        "system_status": [
            r"\b(status|health|check|monitor|stats)\b",
            r"状态|健康|检查|监控",
        ],
        "configuration": [
            r"\b(config|setting|setup|configure|option|preference)\b",
            r"配置|设置|设定",
        ],
        "affirmation": [
            r"\b(yes|yeah|yep|sure|ok|okay|agree|confirm)\b",
            r"是的|对|好|同意|确认",
        ],
        "negation": [
            r"\b(no|nope|nah|disagree|cancel|stop|quit)\b",
            r"不|不是|否|取消|停止",
        ],
    }

    def __init__(self):
        """Initialize the intent parser with compiled patterns."""
        self._compile_patterns()

    def _compile_patterns(self):
        """Pre-compile regex patterns for performance."""
        self._compiled_patterns: dict[str, list[re.Pattern]] = {}
        for intent, patterns in self.INTENT_PATTERNS.items():
            self._compiled_patterns[intent] = [
                re.compile(p, re.IGNORECASE | re.MULTILINE) for p in patterns
            ]

    def parse(self, message: str | Message) -> Intent:
        """
        Parse a message to extract intent and confidence.

        Args:
            message: The message to parse (string or Message object)

        Returns:
            Intent object with name, confidence, and entities
        """
        if isinstance(message, Message):
            text = message.content
        else:
            text = message

        text = text.strip()
        if not text:
            return Intent(
                name="unknown",
                confidence=0.0,
                confidence_level=IntentConfidence.UNKNOWN,
                raw_text=text,
            )

        intent_scores: dict[str, float] = {}

        # Score each intent based on pattern matches
        for intent, patterns in self._compiled_patterns.items():
            score = 0.0
            match_count = 0
            for pattern in patterns:
                match = pattern.search(text)
                if match:
                    match_count += 1
                    # Longer matches get higher scores
                    score += len(match.group()) / len(text)

            if match_count > 0:
                # Normalize score by number of patterns and matches
                intent_scores[intent] = min(score / len(patterns) * match_count, 1.0)

        # Find best intent
        if not intent_scores:
            return Intent(
                name="unknown",
                confidence=0.0,
                confidence_level=IntentConfidence.UNKNOWN,
                raw_text=text,
            )

        best_intent = max(intent_scores, key=intent_scores.get)
        best_score = intent_scores[best_intent]

        # Get alternatives (top 3 other intents)
        alternatives = [
            {"name": k, "confidence": v}
            for k, v in sorted(intent_scores.items(), key=lambda x: -x[1])[1:4]
        ]

        # Determine confidence level
        if best_score >= 0.8:
            confidence_level = IntentConfidence.HIGH
        elif best_score >= 0.5:
            confidence_level = IntentConfidence.MEDIUM
        elif best_score >= 0.3:
            confidence_level = IntentConfidence.LOW
        else:
            confidence_level = IntentConfidence.UNKNOWN

        # Extract entities based on intent
        entities = self._extract_entities(best_intent, text)

        return Intent(
            name=best_intent,
            confidence=best_score,
            confidence_level=confidence_level,
            entities=entities,
            raw_text=text,
            alternatives=alternatives,
        )

    def _extract_entities(self, intent: str, text: str) -> dict:
        """
        Extract entities from text based on the detected intent.

        Args:
            intent: The detected intent name
            text: The message text

        Returns:
            Dictionary of extracted entities
        """
        entities: dict = {}

        # Extract email addresses
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        if emails:
            entities["email"] = emails

        # Extract URLs
        urls = re.findall(r'https?://[^\s]+', text)
        if urls:
            entities["url"] = urls

        # Extract numbers
        numbers = re.findall(r'\b\d+\.?\d*\b', text)
        if numbers:
            entities["numbers"] = [float(n) for n in numbers]

        # Extract quoted strings
        quoted = re.findall(r'["\']([^"\']+)["\']', text)
        if quoted:
            entities["quoted_strings"] = quoted

        # Extract code snippets
        code_blocks = re.findall(r'```[\s\S]*?```|`([^`]+)`', text)
        if code_blocks:
            entities["code_snippets"] = code_blocks

        # Extract file paths (basic pattern)
        paths = re.findall(r'(?:/[\w.-]+)+|[\w.-]+\.\w+', text)
        if paths:
            entities["paths"] = paths

        return entities

    def add_intent_pattern(self, intent_name: str, patterns: list[str]):
        """
        Add or update intent patterns.

        Args:
            intent_name: Name of the intent
            patterns: List of regex patterns
        """
        compiled = [re.compile(p, re.IGNORECASE | re.MULTILINE) for p in patterns]
        self._compiled_patterns[intent_name] = compiled
        self.INTENT_PATTERNS[intent_name] = patterns

    def get_supported_intents(self) -> list[str]:
        """Return list of all supported intent names."""
        return list(self.INTENT_PATTERNS.keys())
