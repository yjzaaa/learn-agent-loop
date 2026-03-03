#!/usr/bin/env python3
"""
core - 面向对象的 Agent 框架

提供可重用的基类和混入类，用于构建各种 Agent。
"""

from .base_agent import BaseAgent
from .mixins import (
    ToolsMixin,
    TodoMixin,
    TaskMixin,
    SkillMixin,
    CompressionMixin,
    BackgroundMixin,
    TeamMixin,
    SubagentMixin,
)
from .client import get_client, get_model

__all__ = [
    "BaseAgent",
    "ToolsMixin",
    "TodoMixin",
    "TaskMixin",
    "SkillMixin",
    "CompressionMixin",
    "BackgroundMixin",
    "TeamMixin",
    "SubagentMixin",
    "get_client",
    "get_model",
]
