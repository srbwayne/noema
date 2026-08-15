"""Instruction authority classifications."""

from enum import Enum


class InstructionAuthority(Enum):
    """Separate instructional authority from contextual content."""

    SYSTEM_POLICY = "system_policy"
    AGENT_POLICY = "agent_policy"
    USER_EXPLICIT = "user_explicit"
    TASK_CONTROL = "task_control"
    COGNITIVE_CONTROL = "cognitive_control"
    EXTERNAL_DATA = "external_data"
    UNTRUSTED_CONTENT = "untrusted_content"
