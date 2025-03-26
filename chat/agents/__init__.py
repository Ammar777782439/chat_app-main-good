"""
حزمة وكلاء الدردشة.

تحتوي هذه الحزمة على وكلاء مختلفين لتطبيق الدردشة، مثل وكيل Kafka.
"""

from .kafka_chat_agent import KafkaChatAgent

__all__ = ['KafkaChatAgent']
