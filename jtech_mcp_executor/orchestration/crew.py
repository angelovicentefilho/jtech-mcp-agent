import asyncio # Necessário para crew.close()
from typing import Any, List, Optional, Dict

# Importar JtechMCPAgent e JtechMCPWorkflow
from jtech_mcp_executor.agents.mcpagent import JtechMCPAgent
from .workflow import JtechMCPWorkflow # Usar import relativo para workflow
from .memory import AgentMemory # Usar import relativo para AgentMemory

# Adicione um logger
import logging
logger = logging.getLogger(__name__)

class JtechMCPCrew:
    """Gerencia um grupo de agentes JtechMCP que trabalham juntos."""

    def __init__(
        self,
        name: str,
        description: str,
        agents: Optional[List[JtechMCPAgent]] = None,
        verbose: bool = False,
        shared_memory: Optional[AgentMemory] = None
    ) -> None:
        """Inicializa um novo JtechMCPCrew.

        Args:
            name: O nome do crew.
            description: Uma descrição do propósito do crew.
            agents: Uma lista opcional de agentes para adicionar inicialmente ao crew.
            verbose: Se True, habilita logging verboso para as operações do crew.
            shared_memory: Uma instância opcional de AgentMemory para ser usada pelo crew.
        """
        self.name = name
        self.description = description
        self.agents: Dict[str, JtechMCPAgent] = {} # Armazenar agentes por nome/role
        self.verbose = verbose
        
        self.shared_memory = shared_memory if shared_memory is not None else AgentMemory()

        if agents:
            for agent in agents:
                self.add_agent(agent) # Usar o método add_agent para consistência
        
        if self.verbose:
            logger.info(f"Crew '{self.name}' criado. Descrição: {self.description}")

    def add_agent(self, agent: JtechMCPAgent) -> None:
        """Adiciona um novo agente ao crew.

        O agente é armazenado usando seu papel (role) como chave.
        Se o agente não tiver um papel definido, uma exceção é levantada.

        Args:
            agent: A instância de JtechMCPAgent a ser adicionada.
        
        Raises:
            ValueError: Se o agente não tiver um papel definido ou se um agente
                        com o mesmo papel já existir.
        """
        role, _ = agent.get_role()
        if not role:
            raise ValueError("Agente deve ter um papel definido para ser adicionado ao crew.")
            
        if role in self.agents:
            raise ValueError(f"Um agente com o papel '{role}' já existe neste crew.")
            
        self.agents[role] = agent
        if self.verbose:
            logger.info(f"Agente com papel '{role}' adicionado ao crew '{self.name}'.")

    def get_agent(self, agent_name_or_role: str) -> Optional[JtechMCPAgent]:
        """Recupera um agente do crew pelo seu nome ou papel.

        Args:
            agent_name_or_role: O nome ou papel do agente a ser recuperado.

        Returns:
            A instância do agente se encontrada, caso contrário None.
        """
        return self.agents.get(agent_name_or_role)

    async def run(
        self,
        task_description: str, # Descrição geral da tarefa para o crew
        workflow: JtechMCPWorkflow,
        initial_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Executa o workflow com a equipe de agentes.

        Args:
            task_description: A descrição da tarefa principal que o crew deve realizar.
            workflow: A instância de JtechMCPWorkflow que define como os agentes colaboram.
            initial_context: Um dicionário opcional de contexto inicial para o workflow.

        Returns:
            Um dicionário contendo o resultado da execução do workflow.
        """
        if self.verbose:
            logger.info(f"Crew '{self.name}' iniciando a execução do workflow '{workflow.__class__.__name__}' para a tarefa: {task_description}")
        
        current_context = initial_context if initial_context is not None else {}
        
        if 'task_description' not in current_context:
            current_context['task_description'] = task_description

        # A especificação sugere que o workflow pode precisar da shared_memory.
        # Isso pode ser passado diretamente para workflow.execute ou setado no workflow.
        # Por agora, vamos passar como argumento para execute, assumindo que
        # o workflow.execute está preparado para recebê-lo ou ignorá-lo.
        # O workflow.execute também recebe 'crew=self'
        result = await workflow.execute(
            crew=self,
            task_description=task_description,
            context=current_context,
            shared_memory=self.shared_memory # Passando a memória compartilhada
        )
        
        if self.verbose:
            logger.info(f"Crew '{self.name}' concluiu a execução do workflow. Resultado: {result}")
            
        return result
        
    async def close(self) -> None:
        """Fecha todos os agentes e recursos associados ao crew."""
        if self.verbose:
            logger.info(f"Fechando o crew '{self.name}' e seus agentes...")
        
        closing_tasks = []
        for agent in self.agents.values():
            if hasattr(agent, 'close') and asyncio.iscoroutinefunction(agent.close):
                closing_tasks.append(agent.close())
            elif hasattr(agent, 'close'):
                # Se 'close' não for uma corrotina, chamar diretamente (menos comum para I/O)
                # ou logar um aviso. Para este contexto, vamos assumir que é async.
                logger.warning(f"Agente {agent.role or agent.__class__.__name__} possui um método 'close' que não é uma corrotina. Não será aguardado.")

        if closing_tasks:
            await asyncio.gather(*closing_tasks)
        
        if self.verbose:
            logger.info(f"Crew '{self.name}' fechado com sucesso.")
