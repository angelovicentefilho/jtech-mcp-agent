# JTech MCP Executor - Sumário do Projeto

## Visão Geral

JTech MCP Executor é uma biblioteca Python proprietária da J-Tech Soluções em Informática que permite conectar qualquer modelo de linguagem grande (LLM) a servidores MCP (Model Context Protocol), oferecendo uma forma unificada para desenvolvedores da empresa criarem agentes baseados em IA com acesso a diversas ferramentas.

A biblioteca facilita a integração entre LLMs e ferramentas externas como navegação web, operações de arquivo, modelagem 3D e outras capacidades expostas via servidores MCP compatíveis.
Além disso, o projeto agora suporta a orquestração de múltiplos agentes, permitindo a criação de equipes de agentes (crews) que podem colaborar em tarefas complexas através de workflows configuráveis.

## Principais Recursos

- **Flexibilidade de LLM**: Compatível com qualquer LLM suportado pelo LangChain que tenha capacidade de chamada de ferramentas (OpenAI, Anthropic, Groq, LLama, etc.)
- **Suporte a Múltiplas Conexões**: HTTP, WebSocket e stdio para comunicação com servidores MCP
- **Suporte Multi-Servidor**: Capacidade de usar múltiplos servidores MCP simultaneamente
- **Seleção Dinâmica de Servidor**: Gerenciador de servidor para escolher automaticamente o servidor mais adequado para cada tarefa
- **Restrições de Ferramentas**: Controle de acesso para limitar ferramentas potencialmente perigosas
- **API Amigável**: Interface simples para criar agentes em poucas linhas de código
- **Adaptadores para Frameworks**: Suporte a LangChain com possibilidade de expansão para outros frameworks
- **Streaming de Saída**: Suporte para streaming assíncrono de resultados do agente
- **Orquestração de Múltiplos Agentes**:
    - Criação de `Crews` (equipes) de agentes especializados.
    - Definição de `Tasks` (tarefas) específicas para cada agente.
    - Suporte a `Workflows` para coordenar a colaboração entre agentes, incluindo:
        - `SequentialWorkflow`: Execução de tarefas em sequência.
        - `ParallelWorkflow`: Execução de tarefas em paralelo com agregação de resultados.
        - `HierarchicalWorkflow`: Modelo supervisor-trabalhador para delegação e revisão iterativa.
    - `AgentMemory`: Mecanismo para compartilhamento de estado e memória entre agentes em um workflow.

## Arquitetura

A arquitetura do projeto é modular e extensível, consistindo de vários componentes interconectados:

### Componentes Principais

1. **JtechMCPClient**: Gerencia conexões com servidores MCP, mantendo sessões e configurações.
2. **JtechMCPSession**: Representa uma sessão individual com um servidor MCP.
3. **JtechMCPAgent**: Implementa a lógica do agente, orquestrando as interações entre o LLM e as ferramentas.
4. **Conectores**: Implementações específicas para diferentes protocolos (HTTP, WebSocket, stdio).
5. **Adaptadores**: Convertem ferramentas MCP para formatos usados por frameworks como LangChain.
6. **Gerenciadores de Servidor**: Controlam a seleção e o direcionamento entre múltiplos servidores.
7. **Gerenciadores de Tarefas**: Lidam com execução assíncrona e streaming de resultados.

### Componentes de Orquestração

8.  **JtechMCPCrew**: Gerencia uma equipe de `JtechMCPAgent`s, atribuindo-lhes papéis e coordenando sua execução através de workflows.
9.  **JtechMCPTask**: Representa uma unidade de trabalho discreta a ser executada por um agente específico dentro de um crew.
10. **JtechMCPWorkflow**: Classe base para definir fluxos de trabalho. Implementações incluem:
    *   `SequentialWorkflow`: Executa tarefas em uma ordem definida.
    *   `ParallelWorkflow`: Executa tarefas simultaneamente e agrega seus resultados.
    *   `HierarchicalWorkflow`: Implementa um padrão de supervisor que delega e revisa o trabalho de agentes trabalhadores.
11. **AgentMemory**: Permite o compartilhamento de dados e estado entre tarefas e agentes durante a execução de um workflow.
12. **ResultAggregator**: Fornece métodos utilitários para combinar ou processar os resultados de múltiplos agentes.

### Estrutura de Diretórios

```
jtech_mcp_executor/
├── __init__.py             # Exporta APIs públicas
├── client.py               # Implementação do JtechMCPClient
├── config.py               # Carregamento e validação de configurações
├── logging.py              # Configuração de logs
├── session.py              # Implementação do JtechMCPSession
├── adapters/               # Adaptadores para diferentes frameworks
│   ├── base.py             # Classe base abstrata para adaptadores
│   ├── langchain_adapter.py # Adaptador específico para LangChain
├── agents/                 # Implementações de agentes
│   ├── base.py             # Classe base de agente
│   ├── mcpagent.py         # JtechMCPAgent (agente principal)
│   └── prompts/            # Templates de prompts para agentes
├── connectors/             # Conectores para diferentes protocolos
│   ├── base.py             # Classe base abstrata para conectores
│   ├── http.py             # Conector HTTP
│   ├── stdio.py            # Conector stdio
│   └── websocket.py        # Conector WebSocket
├── managers/               # Gerenciadores para funcionalidades específicas
│   ├── server_manager.py   # Gerenciador de multi-servidor
│   └── tools/              # Ferramentas internas do gerenciador
├── orchestration/          # Novo: Componentes para orquestração de agentes
│   ├── __init__.py         # Exporta APIs de orquestração
│   ├── crew.py             # Implementação do JtechMCPCrew
│   ├── task.py             # Implementação do JtechMCPTask
│   ├── workflow.py         # Classes base e implementações de workflows
│   ├── memory.py           # Implementação do AgentMemory
│   └── aggregator.py       # Implementação do ResultAggregator
└── task_managers/          # Gerenciadores de tarefas assíncronas
    ├── base.py             # Classe base para gerenciadores de tarefas
    ├── sse.py              # Gerenciador de eventos do servidor
    ├── stdio.py            # Gerenciador de E/S padrão
    └── websocket.py        # Gerenciador WebSocket
```

## Fluxo de Trabalho Típico

1. **Configuração**: O usuário cria uma configuração com os servidores MCP desejados
2. **Inicialização**: Um `JtechMCPClient` é criado a partir da configuração
3. **Criação do Agente**: Um `JtechMCPAgent` é inicializado com o cliente e um LLM
4. **Execução de Consultas**: O agente processa consultas em linguagem natural
5. **Descoberta de Ferramentas**: O agente conecta aos servidores MCP e descobre ferramentas disponíveis
6. **Execução de Ações**: O LLM decide quais ferramentas usar e o agente executa essas ações
7. **Processamento de Resultados**: Os resultados das ferramentas são processados pelo LLM
8. **Resposta Final**: O LLM gera uma resposta final baseada nas informações coletadas

### Fluxo de Trabalho com Orquestração

1.  **Definição de Agentes**: Crie múltiplas instâncias de `JtechMCPAgent`, cada uma com um LLM e, opcionalmente, configurações de cliente específicas. Atribua papéis a cada agente usando `agent.set_role("meu_papel", "Descrição do papel")`.
2.  **Criação do Crew**: Instancie um `JtechMCPCrew` com a lista de agentes.
3.  **Definição de Tarefas**: Crie uma lista de `JtechMCPTask`, especificando a descrição da tarefa e o `agent_name` (papel do agente) que deve executá-la.
4.  **Escolha do Workflow**: Selecione e instancie um tipo de workflow (ex: `SequentialWorkflow`, `ParallelWorkflow`) com as tarefas definidas.
5.  **Execução do Crew**: Chame `crew.run(task_description="Tarefa geral para o crew", workflow=meu_workflow_configurado)`.
6.  **Processamento do Resultado**: O resultado de `crew.run()` conterá o output final do workflow e, dependendo do workflow, detalhes sobre a execução das tarefas individuais.

## Casos de Uso Comuns

- **Agentes para Navegação Web**: Utilizando o servidor MCP do Playwright para automação de navegadores
- **Busca e Reserva de Acomodações**: Utilizando o servidor MCP do Airbnb
- **Modelagem 3D e Design**: Utilizando o servidor MCP do Blender
- **Automação e Acessibilidade**: Agentes para executar tarefas complexas para usuários
- **Integrações de Sistemas**: Conectando LLMs a sistemas externos através de ferramentas personalizadas
- **Pipelines de Processamento de Informação**: Um agente pesquisador coleta dados, um agente analista os processa, e um agente redator gera um resumo (usando `SequentialWorkflow`).
- **Consultas Paralelas a Múltiplas Fontes**: Vários agentes consultam diferentes fontes de dados simultaneamente, com os resultados sendo agregados para uma resposta consolidada (usando `ParallelWorkflow`).
- **Resolução Iterativa de Problemas**: Um agente supervisor quebra um problema complexo, delega sub-problemas a agentes trabalhadores, revisa os resultados e refina as sub-tarefas até que a solução seja satisfatória (usando `HierarchicalWorkflow`).

## Detalhes Técnicos

### Dependências Principais

- **Python**: Versão 3.8 ou superior
- **LangChain**: Para integração com LLMs
- **AsyncIO**: Para operações assíncronas
- **Pydantic**: Para validação de configuração e esquemas
- **AIOHTTP**: Para conexões HTTP assíncronas
- **Websockets**: Para conexões WebSocket

### Testes

O projeto utiliza pytest para testes unitários, disponíveis na pasta `tests/`. Um script `run_tests.sh` está disponível para facilitar a execução dos testes.

### Como Contribuir (Desenvolvimento Interno)

Para desenvolvedores da J-Tech que desejam contribuir:

1. Clone o repositório do GitLab interno
2. Crie uma branch de desenvolvimento (`git checkout -b dev-nova-funcionalidade`)
3. Implemente suas mudanças seguindo as diretrizes de codificação da empresa
4. Execute os testes usando `make test`
5. Execute o linting usando `make lint` 
6. Envie um Merge Request para a branch `main`

Consulte o arquivo CONTRIBUTING.md para orientações detalhadas sobre o processo de desenvolvimento interno.

## Futuros Desenvolvimentos

- Suporte a mais frameworks de IA além do LangChain
- Implementação de mais conectores para diferentes protocolos
- Ferramentas avançadas de depuração e observabilidade
- Interface de usuário para visualização e controle de agentes
- Expansão da documentação e tutoriais
- Melhorias na capacidade de parsing de output do supervisor em workflows hierárquicos
- Interface para visualização de workflows

## Conclusão

O JTech MCP Executor é uma biblioteca versátil e poderosa desenvolvida internamente pela J-Tech que simplifica significativamente o desenvolvimento de agentes baseados em IA com acesso a ferramentas externas. Seu design modular facilita a interoperabilidade entre diferentes modelos de linguagem e servidores de ferramentas, permitindo que os desenvolvedores da empresa criem aplicações de IA mais capazes e úteis para atender às necessidades dos clientes.