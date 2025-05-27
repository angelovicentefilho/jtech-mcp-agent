# Especificação para Implementação de Orquestração de Múltiplos Agentes

## Visão Geral

Este documento detalha as alterações e adições necessárias ao projeto jtech-mcp-executor para implementar capacidades de orquestração de múltiplos agentes similares às funcionalidades Crew e Flow do CrewAI. A implementação proposta permitirá criar, gerenciar e coordenar múltiplos agentes com diferentes funções, ferramentas e objetivos, trabalhando juntos para resolver tarefas complexas.

## Motivação

Atualmente, o jtech-mcp-executor suporta um único agente (JtechMCPAgent) que pode acessar múltiplos servidores MCP, mas não possui mecanismos para orquestrar múltiplos agentes trabalhando juntos. A adição dessas funcionalidades permitirá:

1. Dividir tarefas complexas entre agentes especializados
2. Criar fluxos de trabalho sequenciais ou paralelos entre agentes
3. Implementar hierarquias de agentes (supervisor/trabalhador)
4. Aumentar a modularidade e reutilização de componentes de agentes
5. Melhorar a resolução de problemas através de especialização e cooperação

## Arquitetura Proposta

### 1. Novos Componentes Principais

#### 1.1 `JtechMCPCrew`

Classe principal responsável por definir e gerenciar um grupo de agentes.

```python
class JtechMCPCrew:
    """Gerencia um grupo de agentes JtechMCP que trabalham juntos."""
    
    def __init__(
        self,
        name: str,
        description: str,
        agents: list[JtechMCPAgent] | None = None,
        verbose: bool = False,
    ) -> None:
        # Inicialização
        
    async def add_agent(self, agent: JtechMCPAgent) -> None:
        # Adicionar um novo agente ao crew
        
    async def run(
        self,
        task: str,
        workflow: JtechMCPWorkflow,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        # Executar o workflow com a equipe de agentes
        
    async def close(self) -> None:
        # Fechar todos os agentes e recursos
```

#### 1.2 `JtechMCPWorkflow`

Define como os agentes devem colaborar para realizar uma tarefa.

```python
class JtechMCPWorkflow(ABC):
    """Classe base abstrata para workflows de execução."""
    
    @abstractmethod
    async def execute(
        self,
        crew: JtechMCPCrew,
        task: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Executa o workflow com o crew especificado."""
        pass
```

#### 1.3 `JtechMCPTask`

Representa uma tarefa específica para um agente.

```python
class JtechMCPTask:
    """Representa uma tarefa específica para um agente."""
    
    def __init__(
        self,
        description: str,
        agent_name: str,
        expected_output: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        # Inicialização
```

### 2. Implementações de Workflows

#### 2.1 `SequentialWorkflow`

Executa agentes em uma sequência definida, onde cada agente recebe o resultado do anterior.

```python
class SequentialWorkflow(JtechMCPWorkflow):
    """Workflow que executa agentes em sequência."""
    
    def __init__(
        self,
        tasks: list[JtechMCPTask] | None = None,
    ) -> None:
        # Inicialização
        
    async def execute(
        self,
        crew: JtechMCPCrew,
        task: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        # Implementação da execução sequencial
```

#### 2.2 `ParallelWorkflow`

Executa múltiplos agentes simultaneamente e depois agrega seus resultados.

```python
class ParallelWorkflow(JtechMCPWorkflow):
    """Workflow que executa agentes em paralelo."""
    
    def __init__(
        self,
        tasks: list[JtechMCPTask] | None = None,
        result_aggregator: Callable | None = None,
    ) -> None:
        # Inicialização
        
    async def execute(
        self,
        crew: JtechMCPCrew,
        task: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        # Implementação da execução paralela
```

#### 2.3 `HierarchicalWorkflow`

Implementa um modelo supervisor/trabalhador, onde um agente supervisiona outros.

```python
class HierarchicalWorkflow(JtechMCPWorkflow):
    """Workflow que implementa uma hierarquia de agentes."""
    
    def __init__(
        self,
        supervisor_name: str,
        workers: list[str],
        max_iterations: int = 5,
    ) -> None:
        # Inicialização
        
    async def execute(
        self,
        crew: JtechMCPCrew,
        task: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        # Implementação da execução hierárquica
```

### 3. Modificações no `JtechMCPAgent`

Adicionar suporte para comunicação entre agentes e contextualização.

```python
class JtechMCPAgent:
    # Adições à classe existente
    
    def set_role(self, role: str, description: str) -> None:
        """Define o papel específico do agente."""
        # Implementação
        
    def get_role(self) -> str:
        """Retorna o papel atual do agente."""
        # Implementação
        
    async def receive_message(
        self,
        message: str,
        from_agent: str,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Recebe mensagem de outro agente."""
        # Implementação
        
    # Método run modificado para incluir contexto
    async def run(
        self,
        query: str,
        max_steps: int | None = None,
        manage_connector: bool = True,
        external_history: list[BaseMessage] | None = None,
        context: dict[str, Any] | None = None,  # Novo parâmetro
    ) -> str:
        # Implementação atualizada
```

### 4. Componentes de Suporte

#### 4.1 `AgentMemory`

Gerencia o histórico e a memória compartilhada entre agentes.

```python
class AgentMemory:
    """Armazena e gerencia a memória compartilhada entre agentes."""
    
    def __init__(self) -> None:
        # Inicialização
        
    def add_memory(self, key: str, value: Any) -> None:
        # Adiciona um item à memória
        
    def get_memory(self, key: str) -> Any:
        # Recupera um item da memória
        
    def get_all_memory(self) -> dict[str, Any]:
        # Recupera toda a memória
```

#### 4.2 `ResultAggregator`

Utilitários para combinar resultados de múltiplos agentes.

```python
class ResultAggregator:
    """Utilitários para agregação de resultados de múltiplos agentes."""
    
    @staticmethod
    def summarize(results: list[str], task: str) -> str:
        # Agrega resultados através de resumo
        
    @staticmethod
    def concatenate(results: list[str]) -> str:
        # Concatena resultados
        
    @staticmethod
    def vote(results: list[str]) -> str:
        # Implementa um sistema de votação para resultados conflitantes
```

## Estrutura de Diretórios Proposta

```
jtech_mcp_executor/
├── ...
├── orchestration/
│   ├── __init__.py
│   ├── crew.py          # Implementação do JtechMCPCrew
│   ├── workflow.py      # Classes base e implementações de workflows
│   ├── task.py          # Implementação de tarefas
│   ├── memory.py        # Gerenciamento de memória compartilhada
│   └── aggregator.py    # Utilitários de agregação de resultados
└── ...
```

## Plano de Implementação

### Fase 1: Estruturas Básicas

1. Criar o pacote `orchestration`
2. Implementar classes base `JtechMCPCrew`, `JtechMCPWorkflow`, e `JtechMCPTask`
3. Modificar `JtechMCPAgent` para suportar roles e contexto
4. Implementar `AgentMemory` para memória compartilhada

### Fase 2: Workflows

1. Implementar `SequentialWorkflow`
2. Implementar `ParallelWorkflow`
3. Implementar `HierarchicalWorkflow`
4. Criar utilitários de agregação de resultados

### Fase 3: Integração e Testes

1. Integrar com os mecanismos existentes do JtechMCPClient e conectores
2. Implementar testes unitários para cada componente
3. Criar exemplos de uso nos vários cenários

## Exemplo de Uso

```python
import asyncio
from langchain_openai import ChatOpenAI
from jtech_mcp_executor import JtechMCPAgent, JtechMCPClient
from jtech_mcp_executor.orchestration import (
    JtechMCPCrew, SequentialWorkflow, JtechMCPTask
)

async def main():
    # Configuração de client
    client = JtechMCPClient.from_config_file("config.json")
    
    # Criar agentes especializados
    pesquisador = JtechMCPAgent(
        llm=ChatOpenAI(model="gpt-4o"),
        client=client,
        system_prompt="Você é um especialista em pesquisa de dados."
    )
    pesquisador.set_role("pesquisador", "Pesquisar e coletar dados")
    
    analista = JtechMCPAgent(
        llm=ChatOpenAI(model="gpt-4o"),
        client=client,
        system_prompt="Você é um analista de dados especializado."
    )
    analista.set_role("analista", "Analisar dados e tirar conclusões")
    
    redator = JtechMCPAgent(
        llm=ChatOpenAI(model="gpt-4o"),
        client=client,
        system_prompt="Você é um redator especializado em relatórios."
    )
    redator.set_role("redator", "Criar relatórios a partir de análises")
    
    # Criar um crew com estes agentes
    crew = JtechMCPCrew(
        name="Equipe de Análise de Dados",
        description="Equipe especializada em pesquisa e análise de dados",
        agents=[pesquisador, analista, redator]
    )
    
    # Definir tarefas para cada agente
    tarefas = [
        JtechMCPTask(
            description="Pesquise dados sobre o mercado imobiliário em São Paulo nos últimos 5 anos",
            agent_name="pesquisador"
        ),
        JtechMCPTask(
            description="Analise as tendências e padrões nos dados coletados",
            agent_name="analista"
        ),
        JtechMCPTask(
            description="Crie um relatório detalhado sobre as descobertas",
            agent_name="redator"
        )
    ]
    
    # Criar um workflow sequencial
    workflow = SequentialWorkflow(tasks=tarefas)
    
    # Executar o workflow
    resultado = await crew.run(
        task="Elabore um estudo completo sobre o mercado imobiliário em São Paulo",
        workflow=workflow
    )
    
    print(resultado)
    
    # Liberar recursos
    await crew.close()

if __name__ == "__main__":
    asyncio.run(main())
```

## Considerações Técnicas

### 1. Compatibilidade Retroativa
Manter compatibilidade com o uso existente de JtechMCPAgent para que códigos anteriores continuem funcionando.

### 2. Gerenciamento de Recursos
Garantir que todos os recursos (conexões, sessões) sejam adequadamente gerenciados, especialmente ao usar múltiplos agentes simultaneamente.

### 3. Tratamento de Erros
Implementar estratégias robustas para lidar com falhas em agentes individuais sem comprometer todo o workflow.

### 4. Observabilidade
Adicionar logs e telemetria para facilitar a depuração de workflows complexos.

### 5. Persistência
Considerar opções para persistir o estado dos workflows para recuperação em caso de falhas.

## Conclusão

A implementação de capacidades de orquestração de múltiplos agentes no jtech-mcp-executor permitirá desenvolver aplicações mais sofisticadas, aproveitando a especialização e colaboração entre agentes. A arquitetura proposta mantém a filosofia modular do projeto enquanto adiciona novas capacidades importantes para solucionar problemas complexos.
