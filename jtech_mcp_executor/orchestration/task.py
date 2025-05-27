from typing import Any, Optional

class JtechMCPTask:
    """Representa uma tarefa específica para um agente."""

    def __init__(
        self,
        description: str,
        agent_name: str, # Nome do agente que deve executar a tarefa
        expected_output: Optional[str] = None, # Descrição do que se espera como resultado
        context: Optional[dict[str, Any]] = None, # Dados adicionais para a tarefa
        # Considere adicionar um ID para a tarefa ou um nome opcional para fácil referência
        name: Optional[str] = None,
        task_id: Optional[str] = None,
    ) -> None:
        """
        Inicializa uma nova instância de JtechMCPTask.

        Args:
            description: Descrição da tarefa.
            agent_name: Nome do agente que deve executar a tarefa.
            expected_output: Descrição do que se espera como resultado.
            context: Dados adicionais para a tarefa.
            name: Nome opcional para a tarefa.
            task_id: ID opcional para a tarefa.
        """
        self.description = description
        self.agent_name = agent_name
        self.expected_output = expected_output
        self.context = context if context is not None else {}
        self.name = name
        self.task_id = task_id
        # Adicione quaisquer outros atributos ou inicializações que julgar necessárias
        # com base na especificação.
