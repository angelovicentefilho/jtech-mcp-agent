"""
Copyright (c) 2025 J-Tech Solucoes em Informatica.
All Rights Reserved.

This software is the confidential and proprietary information of J-Tech.
("Confidential Information"). You shall not disclose such Confidential
Information and shall use it only in accordance with the terms of the
license agreement you entered into with J-Tech.
"""

"""
jtech-mcp-executor - An MCP library for LLMs.

This library provides a unified interface for connecting different LLMs
to MCP tools through existing LangChain adapters.
"""

from importlib.metadata import version

from .agents.mcpagent import JtechMCPAgent
from .client import JtechMCPClient
from .config import load_config_file
from .connectors import BaseConnector, HttpConnector, StdioConnector, WebSocketConnector
from .logging import MCP_USE_DEBUG, Logger, logger
from .session import JtechMCPSession

from .orchestration import (
    JtechMCPCrew,
    JtechMCPTask,
    SequentialWorkflow,
    ParallelWorkflow,
    HierarchicalWorkflow,
    AgentMemory,
    ResultAggregator
)

__version__ = version("jtech-mcp-executor")

__all__ = [
    "JtechMCPAgent",
    "JtechMCPClient",
    "JtechMCPSession",
    "BaseConnector",
    "StdioConnector",
    "WebSocketConnector",
    "HttpConnector",
    
    # Novos componentes de orquestração
    "JtechMCPCrew",
    "JtechMCPTask",
    "SequentialWorkflow",
    "ParallelWorkflow",
    "HierarchicalWorkflow",
    "AgentMemory",
    "ResultAggregator",

    # Funções/variáveis existentes (mantendo create_session_from_config conforme instruído)
    "create_session_from_config",
    "load_config_file",
    "logger",
    "MCP_USE_DEBUG",
    "Logger",
    "set_debug",
]


# Helper function to set debug mode
def set_debug(debug=2):
    """Set the debug mode for jtech-mcp-executor.

    Args:
        debug: Whether to enable debug mode (default: True)
    """
    Logger.set_debug(debug)
