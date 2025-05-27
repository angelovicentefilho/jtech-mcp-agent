# jtech_mcp_executor/orchestration/__init__.py

"""
Módulo de Orquestração para o JTech MCP Executor.

Este pacote fornece ferramentas para coordenar múltiplos agentes JtechMCPAgent
em tarefas complexas usando diferentes tipos de workflows.
"""

from .crew import JtechMCPCrew
from .task import JtechMCPTask
from .workflow import (
    JtechMCPWorkflow,
    SequentialWorkflow,
    ParallelWorkflow,
    HierarchicalWorkflow
)
from .memory import AgentMemory
from .aggregator import ResultAggregator

__all__ = [
    "JtechMCPCrew",
    "JtechMCPTask",
    "JtechMCPWorkflow",
    "SequentialWorkflow",
    "ParallelWorkflow",
    "HierarchicalWorkflow",
    "AgentMemory",
    "ResultAggregator",
]
